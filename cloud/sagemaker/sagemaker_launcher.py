"""
SageMaker Launcher Script for SmartIrrigate Cloud
Triggers a managed Scikit-Learn training job on AWS SageMaker using Boto3.
"""

import os
import boto3
import sagemaker
from sagemaker.sklearn.estimator import SKLearn

# Load environment configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
SAGEMAKER_ROLE = os.environ.get("SAGEMAKER_ROLE_ARN")
TRAIN_DATA_S3 = os.environ.get("S3_PROCESSED_URI", "s3://smartirrigate-processed-bucket/processed/")
OUTPUT_MODELS_S3 = os.environ.get("S3_MODELS_URI", "s3://smartirrigate-models-bucket/models/")
INSTANCE_TYPE = os.environ.get("SAGEMAKER_TRAINING_INSTANCE_TYPE", "ml.m5.large")


def launch_training_job():
    if not SAGEMAKER_ROLE:
        print("ERROR: SAGEMAKER_ROLE_ARN environment variable is not defined.")
        print("Please export SAGEMAKER_ROLE_ARN with your IAM role ARN before running.")
        return

    print(f"Connecting to SageMaker session in region {AWS_REGION}...")
    boto_session = boto3.Session(region_name=AWS_REGION)
    sagemaker_session = sagemaker.Session(boto_session=boto_session)

    sklearn_estimator = SKLearn(
        entry_point="train_entrypoint.py",
        source_dir="cloud/sagemaker",
        role=SAGEMAKER_ROLE,
        instance_count=1,
        instance_type=INSTANCE_TYPE,
        framework_version="1.2-1",
        py_version="py3",
        output_path=OUTPUT_MODELS_S3,
        sagemaker_session=sagemaker_session,
        hyperparameters={
            "n-estimators": 100,
            "max-depth": 12,
            "test-split": 0.2,
        },
        tags=[
            {"Key": "Project", "Value": "SmartIrrigateCloud"},
            {"Key": "Environment", "Value": "Production"},
        ],
    )

    print(f"Launching SageMaker training job using data from {TRAIN_DATA_S3}...")
    sklearn_estimator.fit({"train": TRAIN_DATA_S3})
    print(f"Training job completed. Model artefact uploaded to: {sklearn_estimator.model_data}")


if __name__ == "__main__":
    launch_training_job()
