## PREREQUISITES

```bash
# 1. Install AWS CLI
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 2. Install Node.js (for CDK)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 3. Install Python
sudo apt install python3 python3-venv python3-pip

# 4. Install CDK
npm install -g aws-cdk
```

## Clone & Enter Repo
```bash
git clone https://github.com/saketh-n/paybe-aws-stack.git
cd paybe-aws-stack
```

## Create Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Install Python Dependencies
```bash
pip install -r requirements.txt
```

## Create IAM User + Attach Minimal Policy
### Step A: Create User (AWS Console)
1. Open: https://console.aws.amazon.com/iam/
2. Users → Create user
3. Name: finance-summary-deployer
4. Select AWS access type → Access key - Programmatic access
5. Next -> Create user
6. Download .csv -> Save Access Key ID and Secret Access Key

### Step B: Attach the following policy
[See iam.json]

## Configure AWS Credentials
```bash
aws configure
```
Enter:
* Access Key ID: AKIA...
* Secret Access Key: ...
* Region: us-east-1
* Output: json

Where do I get keys?
→ AWS Console → IAM → Users → Your User → Create access key

## Deploy Infrastructure
```bash
cd infra/cdk
cdk bootstrap
cdk deploy
```

## Load Sample Data to DynamoDB
```bash
cd ../../scripts
python load_data.py
```

## Test API
```bash
curl "https://YOUR_API_URL_HERE/summary?userId=USER%23me"
```

## CLEANUP (When done)
```bash
./cleanup.sh
```

### Note:
In production (no need to use Bedrock or even LLM):
* Use heuristic or small classifier to tag category (as a column in DynamoDB), per tx
* Use DynamoDB queries or Athena for grouping (and total spend per)
