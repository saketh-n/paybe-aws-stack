echo "Deleting CDK stack..."
cd infra/cdk && cdk destroy --force

echo "Deleting CDKToolkit stack..."
aws cloudformation delete-stack --stack-name CDKToolkit
aws cloudformation wait stack-delete-complete --stack-name CDKToolkit

echo "Finding and deleting CDK S3 buckets..."
BUCKETS=$(aws s3 ls | grep cdk | awk '{print $3}')

if [ -z "$BUCKETS" ]; then
    echo "No CDK buckets found."
else
    for BUCKET in $BUCKETS; do
        echo "Emptying and deleting: $BUCKET"
        # Empty bucket
        aws s3 rm s3://$BUCKET --recursive
        # Delete bucket
        aws s3 rb s3://$BUCKET --force
    done
fi