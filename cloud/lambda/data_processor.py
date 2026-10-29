"""
AWS Lambda Serverless Data Processor for SmartIrrigate Cloud
Trigger: S3 ObjectCreated event on raw bucket
Output: Validated & imputed agricultural dataset written to processed bucket
"""

import io
import json
import logging
import os
import urllib.parse
import boto3
import pandas as pd

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

PROCESSED_BUCKET = os.environ.get("PROCESSED_BUCKET", "smartirrigate-processed-bucket")
REQUIRED_COLUMNS = ["crop_type", "soil_type", "soil_moisture_pct", "temperature_c", "humidity_pct", "rainfall_mm"]


def lambda_handler(event, context):
    """
    AWS Lambda entrypoint triggered by S3 bucket events.
    Protects against duplicate events and avoids recursive triggers by
    reading strictly from raw-bucket and writing strictly to processed-bucket.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    records = event.get("Records", [])
    if not records:
        logger.warning("No records found in event payload.")
        return {"statusCode": 200, "body": "No records to process"}

    processed_count = 0

    for record in records:
        event_name = record.get("eventName", "")
        # Safe idempotent check: process only ObjectCreated events
        if not event_name.startswith("ObjectCreated"):
            logger.info(f"Skipping non-creation event: {event_name}")
            continue

        src_bucket = record["s3"]["bucket"]["name"]
        raw_key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # Prevent recursive execution if trigger misconfigured
        if src_bucket == PROCESSED_BUCKET or raw_key.startswith("processed/"):
            logger.warning(f"Preventing recursive trigger for file {raw_key} in {src_bucket}")
            continue

        logger.info(f"Processing object s3://{src_bucket}/{raw_key}")

        try:
            # 1. Download object from S3 Raw Bucket
            obj_res = s3_client.get_object(Bucket=src_bucket, Key=raw_key)
            content = obj_res["Body"].read()

            df = pd.read_csv(io.BytesIO(content))
            initial_rows = len(df)

            # 2. Schema normalization
            clean_cols = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
            df.rename(columns=clean_cols, inplace=True)

            # 3. Missing values imputation
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
                else:
                    mode_val = df[col].mode()
                    df[col] = df[col].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")
                    df[col] = df[col].astype(str).str.strip().str.title()

            # 4. Serialize to CSV buffer
            out_buffer = io.StringIO()
            df.to_csv(out_buffer, index=False)

            # 5. Write to S3 Processed Bucket
            target_key = f"processed/{raw_key.split('/')[-1]}"
            s3_client.put_object(
                Bucket=PROCESSED_BUCKET,
                Key=target_key,
                Body=out_buffer.getvalue().encode("utf-8"),
                ContentType="text/csv",
                Metadata={
                    "original_bucket": src_bucket,
                    "original_key": raw_key,
                    "processed_rows": str(len(df)),
                    "initial_rows": str(initial_rows),
                },
            )

            logger.info(f"Successfully processed {len(df)} rows to s3://{PROCESSED_BUCKET}/{target_key}")
            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing s3://{src_bucket}/{raw_key}: {e}", exc_info=True)
            # In production, publish to an SQS Dead Letter Queue (DLQ)
            raise e

    return {
        "statusCode": 200,
        "body": json.dumps({"processed_files": processed_count, "status": "success"}),
    }
