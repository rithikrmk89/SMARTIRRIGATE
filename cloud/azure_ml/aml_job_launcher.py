"""
Azure ML Job Launcher for SmartIrrigate Cloud
Uses Azure AI ML SDK (v2) to submit a managed training job to an Azure ML compute cluster.
"""

import os
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient, command, Input
from azure.ai.ml.constants import AssetTypes

SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID")
RESOURCE_GROUP = os.environ.get("AZURE_RESOURCE_GROUP", "smartirrigate-rg")
WORKSPACE_NAME = os.environ.get("AZURE_ML_WORKSPACE_NAME", "smartirrigate-aml")
COMPUTE_CLUSTER = os.environ.get("AZURE_ML_COMPUTE_NAME", "cpu-cluster")
TRAIN_DATA_URL = os.environ.get(
    "AZURE_TRAIN_DATA_URL",
    "azureml://datastores/workspaceblobstore/paths/smartirrigate-processed/"
)


def launch_azure_ml_training():
    if not SUBSCRIPTION_ID:
        print("ERROR: AZURE_SUBSCRIPTION_ID environment variable is required to submit Azure ML jobs.")
        print("Set AZURE_SUBSCRIPTION_ID and ensure 'az login' has been executed.")
        return

    print(f"Authenticating with Azure and connecting to workspace '{WORKSPACE_NAME}' in RG '{RESOURCE_GROUP}'...")
    credential = DefaultAzureCredential()
    ml_client = MLClient(credential, SUBSCRIPTION_ID, RESOURCE_GROUP, WORKSPACE_NAME)

    job = command(
        code="./cloud/azure_ml",
        command="python train_aml.py --data-path ${{inputs.training_data}} --n-estimators ${{inputs.n_estimators}} --max-depth ${{inputs.max_depth}}",
        inputs={
            "training_data": Input(type=AssetTypes.URI_FOLDER, path=TRAIN_DATA_URL),
            "n_estimators": 100,
            "max_depth": 12,
        },
        environment="AzureML-sklearn-1.2-ubuntu20.04-py38-cpu:1",
        compute=COMPUTE_CLUSTER,
        display_name="smartirrigate-rf-training",
        experiment_name="smartirrigate-water-demand",
        tags={"Project": "SmartIrrigateCloud", "Cloud": "MicrosoftAzure"},
    )

    print("Submitting training job to Azure Machine Learning...")
    returned_job = ml_client.jobs.create_or_update(job)
    print(f"Azure ML Job submitted successfully! Studio URL: {returned_job.services['Studio'].endpoint}")


if __name__ == "__main__":
    launch_azure_ml_training()
