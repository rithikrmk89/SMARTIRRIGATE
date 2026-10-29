# AWS Lambda Serverless Data Processor for SmartIrrigate Cloud

## Overview
This serverless function processes agricultural datasets uploaded to an Amazon S3 Raw Bucket. It:
1. Normalizes column names to standard agro-meteorological snake_case.
2. Imputes missing numerical sensor values with column medians.
3. Imputes missing categorical values with modes.
4. Outputs cleaned CSV records directly to the Amazon S3 Processed Bucket.
5. Guards against duplicate events and avoids recursive trigger loops by reading exclusively from the raw bucket and writing exclusively to the processed bucket.

## Packaging and Deployment Instructions

### 1. Create Deployment Package with AWS Lambda Layer (Pandas)
Because `pandas` has C extensions, use the AWS-provided AWS Lambda Layer for Pandas (`AWSSDKPandas-Python311`) or package in a Docker container matching the Lambda runtime:

```bash
# Package function code
zip -r function.zip data_processor.py
```

### 2. Create the Lambda Function via AWS CLI
```bash
aws lambda create-function \
  --function-name SmartIrrigateDataProcessor \
  --runtime python3.11 \
  --role arn:aws:iam::<YOUR_ACCOUNT_ID>:role/SmartIrrigateLambdaRole \
  --handler data_processor.lambda_handler \
  --zip-file fileb://function.zip \
  --environment Variables={PROCESSED_BUCKET=smartirrigate-processed-bucket} \
  --layers arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python311:12
```

### 3. Grant S3 Permission to Invoke Lambda
```bash
aws lambda add-permission \
  --function-name SmartIrrigateDataProcessor \
  --principal s3.amazonaws.com \
  --statement-id s3invoke \
  --action lambda:InvokeFunction \
  --source-arn arn:aws:s3:::smartirrigate-raw-data-bucket
```

### 4. Configure S3 Event Notification
Configure the raw bucket notification to trigger `SmartIrrigateDataProcessor` upon `s3:ObjectCreated:*` with prefix `uploads/` and suffix `.csv`.
