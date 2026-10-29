"""
Azure Functions v2 Serverless Data Processor for SmartIrrigate Cloud
Trigger: Azure Blob Storage Trigger on 'smartirrigate-raw-data/{name}.csv'
Output: Validated & imputed agricultural dataset written to 'smartirrigate-processed' container
"""

import io
import logging
import os
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import pandas as pd

app = func.FunctionApp()

PROCESSED_CONTAINER = os.environ.get("AZURE_PROCESSED_CONTAINER", "smartirrigate-processed")
STORAGE_CONN_STR = os.environ.get("AzureWebJobsStorage")

REQUIRED_COLUMNS = ["crop_type", "soil_type", "soil_moisture_pct", "temperature_c", "humidity_pct", "rainfall_mm"]


@app.blob_trigger(
    arg_name="myblob",
    path="smartirrigate-raw-data/{name}.csv",
    connection="AzureWebJobsStorage"
)
def process_irrigation_data(myblob: func.InputStream):
    """
    Azure Function Blob Trigger executed when a CSV file is uploaded to the raw container.
    Standardizes schema, imputes missing values, and writes cleaned data to processed container.
    """
    blob_name = myblob.name
    logging.info(f"Processing Azure Blob trigger for: {blob_name}, Size: {myblob.length} bytes")

    try:
        # 1. Read input blob content
        content = myblob.read()
        df = pd.read_csv(io.BytesIO(content))
        initial_rows = len(df)

        if df.empty:
            logging.warning(f"Blob {blob_name} is empty. Skipping.")
            return

        # 2. Schema normalization
        clean_cols = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
        df.rename(columns=clean_cols, inplace=True)

        # 3. Impute missing values
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
            else:
                mode_val = df[col].mode()
                df[col] = df[col].fillna(mode_val[0] if len(mode_val) > 0 else "Unknown")
                df[col] = df[col].astype(str).str.strip().str.title()

        # 4. Serialize cleaned dataframe to CSV
        output_buffer = io.StringIO()
        df.to_csv(output_buffer, index=False)
        csv_bytes = output_buffer.getvalue().encode("utf-8")

        # 5. Upload to Azure Processed Container
        target_blob_name = f"processed_{os.path.basename(blob_name)}"
        if STORAGE_CONN_STR:
            blob_service_client = BlobServiceClient.from_connection_string(STORAGE_CONN_STR)
            container_client = blob_service_client.get_container_client(PROCESSED_CONTAINER)
            if not container_client.exists():
                container_client.create_container()

            dest_blob_client = container_client.get_blob_client(target_blob_name)
            dest_blob_client.upload_blob(
                csv_bytes,
                overwrite=True,
                metadata={
                    "source_blob": blob_name,
                    "initial_rows": str(initial_rows),
                    "cleaned_rows": str(len(df)),
                }
            )
            logging.info(f"Successfully processed {len(df)} rows to container '{PROCESSED_CONTAINER}/{target_blob_name}'")
        else:
            logging.warning("AzureWebJobsStorage connection string not set. Blob processing simulated.")

    except Exception as e:
        logging.error(f"Error processing blob {blob_name}: {e}", exc_info=True)
        raise e
