import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal 
import re 

# === CORS HELPER ===
def cors_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])
bedrock = boto3.client('bedrock-runtime')
MODEL_ID = os.environ['MODEL_ID']

def lambda_handler(event, context):
    try:
        user_id = event['queryStringParameters']['userId']
    except (KeyError, TypeError):
        return {"statusCode": 400, "body": json.dumps({"error": "userId required"})}

    # Last 30 days
    end = datetime.utcnow()
    start = end - timedelta(days=30)

    response = table.query(
        KeyConditionExpression="userId = :uid AND #ts BETWEEN :start AND :end",
        ExpressionAttributeNames={"#ts": "timestamp"},
        ExpressionAttributeValues={
            ":uid": user_id,
            ":start": start.strftime("%Y-%m-%dT%H:%M:%S"),
            ":end": end.strftime("%Y-%m-%dT%H:%M:%S")
        }
    )

    transactions = response.get('Items', [])

    if not transactions:
        return {"statusCode": 200, "body": json.dumps({"totalSpend": 0, "byCategory": {}, "budgetRecommendation": "No transactions found."})}

    def decimal_to_float(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError
        
    # Build prompt
    prompt = f"""
    You are a personal finance assistant
    Analyze the following transaction data and return only valid JSON:

    {{
        "totalSpend": $XXX.XX,
        "byCategory": {{"Dining": [relevant-purchases], "Groceries": [relevant-purchases], ...}},
        "budget": "{{"Dining": total-spend-in-by-category * 1.25, "Groceries": total-spend-in-by-category * 1.25, ...}}"
    }}

    Return ONLY the JSON. No extra text.
    Transactions:
    {json.dumps(transactions, indent=2, default=decimal_to_float)}
    """

    # Call Bedrock
    try:
        resp = bedrock.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10000,
                "temperature": 0.3
            })
        )
        
        # DEBUG: Log raw body
        raw_body = resp['body'].read()
        print("Raw Bedrock response:", raw_body)  # ← CloudWatch will show this

        if not raw_body:
            return cors_response(500, {"error": "Empty response from Bedrock"})

        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as e:
            return cors_response(500, {"error": f"Invalid JSON from Bedrock: {str(e)}"})

        # SAFE: Extract content
        choices = parsed.get('choices', [])
        if not choices:
            return cors_response(500, {"error": "No choices in Bedrock response"})

        raw = choices[0].get('message', {}).get('content', '')
        if not raw:
            return cors_response(500, {"error": "No content in Bedrock message"})

    except Exception as e:
        return cors_response(500, {"error": f"Bedrock invoke failed: {str(e)}"})

    # Extract JSON
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        return {"statusCode": 500, "body": json.dumps({"error": "No JSON in LLM response"})}

    try:
        result = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"statusCode": 500, "body": json.dumps({"error": "Invalid JSON from LLM"})}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result)
    }