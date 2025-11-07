import boto3
import csv
import json
from decimal import Decimal 
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'PersonalShopping'
CSV_PATH = '../data/transactions.csv'

def table_exists():
    client = boto3.client('dynamodb')
    try:
        client.describe_table(TableName=TABLE_NAME)
        return True
    except client.exceptions.ResourceNotFoundException:
        return False

def data_already_loaded():
    table = dynamodb.Table(TABLE_NAME)
    # Tailored to this specific data only, since its demo
    response = table.scan(
        Limit=1,
        FilterExpression="#itm = :val",  # ← Escape "item"
        ExpressionAttributeNames={"#itm": "item"},  # ← Map #itm → item
        ExpressionAttributeValues={":val": "Almond Milk"}
    )
    return response['Count'] > 0

def main():
    if not table_exists():
        print(f"Table {TABLE_NAME} does not exist. Run `cdk deploy` first.")
        return

    if data_already_loaded():
        print("Data already loaded. Skipping.")
        return
    
    table = dynamodb.Table(TABLE_NAME)
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        with table.batch_writer() as batch:
            for row in reader:
                item = {
                    'userId': 'USER#me',
                    'timestamp': row['Timestamp'],
                    'item': row['Item Purchased'],
                    'price': Decimal(row['Price']),
                    'store': row['Store Name'],
                    'location': row['Location']
                }
                batch.put_item(Item=item)

if __name__ == "__main__":
    main()