from aws_cdk import (
    Stack, 
    aws_dynamodb as dynamodb, 
    aws_lambda as _lambda, 
    aws_iam,
    aws_apigateway as apigw,
    Duration,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class FinanceSummaryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # === DYNAMODB TABLE ===
        table = dynamodb.Table(
            self, "PersonalShopping",
            table_name="PersonalShopping",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY # For Demo purposes only
        )

        # === LAMBDA FUNCTION ===
        handler = _lambda.Function(
            self, "SummaryHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("../lambda"),
            environment={
                "TABLE_NAME": table.table_name,
                "MODEL_ID": self.node.try_get_context("bedrock_model_id")
            },
            timeout=Duration.seconds(30)
        )

        # Grant permissions
        table.grant_read_data(handler)
        handler.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=["bedrock:InvokeModel"],
                resources=["*"]
            )
        )

        # === API GATEWAY ===
        api = apigw.RestApi(
            self, "FinanceSummaryApi",
            rest_api_name="Finance Summary API"
        )

        summary = api.root.add_resource("summary")
        summary.add_method("GET", apigw.LambdaIntegration(handler))

        # Output API URL
        CfnOutput(self, "ApiUrl", value=f"{api.url}summary")