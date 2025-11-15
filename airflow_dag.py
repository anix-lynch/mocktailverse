"""
AWS ETL Pipeline DAG for Mocktailverse
========================================

This DAG orchestrates an end-to-end AWS-native ETL pipeline demonstrating:
- Serverless data extraction (S3)
- Distributed transformation (Glue/Lambda)
- NoSQL data loading (DynamoDB)
- Data modeling (dbt-core)
- Pipeline orchestration (Apache Airflow)

Architecture:
    S3 (Extract) → Glue/Lambda (Transform) → DynamoDB (Load) → dbt-core (Model)

CLI Usage:
    airflow dags trigger mocktailverse_dag

Free Tier Compliant:
- Uses AWS Lambda free tier (1M requests/month)
- Uses AWS Glue free tier (1 DPU/hour for first 1M objects)
- Uses Amazon DynamoDB free tier (25GB storage, 200M requests/month)
- Uses Amazon S3 free tier (5GB storage, 20K GET requests)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.glue import GlueJobOperator
from airflow.providers.amazon.aws.operators.lambda_function import LambdaInvokeFunctionOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.hooks.dynamodb import DynamoDBHook
import boto3
import json
import logging

# Default DAG arguments
default_args = {
    'owner': 'mocktailverse',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'max_active_runs': 1,
}

# DAG definition
dag = DAG(
    'mocktailverse_etl_pipeline',
    default_args=default_args,
    description='AWS ETL Pipeline for Mocktailverse Cocktail Data',
    schedule_interval='@daily',  # Run daily
    catchup=False,
    tags=['aws', 'etl', 'mocktailverse', 'glue', 'lambda', 'dynamodb', 'dbt'],
)

def extract_cocktail_data():
    """
    Extract cocktail recipe data from external APIs and store in S3.
    This simulates extracting data from various cocktail APIs.
    """
    import requests
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook

    logging.info("Starting data extraction from cocktail APIs")

    # Sample cocktail data (in production, this would call real APIs)
    cocktail_data = [
        {
            "id": "margarita_001",
            "name": "Classic Margarita",
            "category": "Cocktail",
            "ingredients": [
                {"name": "Tequila", "amount": "2", "unit": "oz"},
                {"name": "Lime Juice", "amount": "1", "unit": "oz"},
                {"name": "Triple Sec", "amount": "1", "unit": "oz"},
                {"name": "Salt", "amount": "1", "unit": "rim"}
            ],
            "instructions": "Shake all ingredients with ice. Strain into salt-rimmed glass.",
            "glass": "Margarita Glass",
            "extracted_at": datetime.now().isoformat()
        },
        {
            "id": "mojito_002",
            "name": "Mojito",
            "category": "Cocktail",
            "ingredients": [
                {"name": "White Rum", "amount": "2", "unit": "oz"},
                {"name": "Lime Juice", "amount": "1", "unit": "oz"},
                {"name": "Simple Syrup", "amount": "0.5", "unit": "oz"},
                {"name": "Mint Leaves", "amount": "8", "unit": "leaves"},
                {"name": "Club Soda", "amount": "2", "unit": "oz"}
            ],
            "instructions": "Muddle mint leaves with lime juice and syrup. Add rum and ice. Top with soda.",
            "glass": "Highball Glass",
            "extracted_at": datetime.now().isoformat()
        }
    ]

    # Upload to S3
    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = 'mocktailverse-raw-data'
    key = f'extracted/{datetime.now().strftime("%Y/%m/%d")}/cocktail_data.json'

    # Ensure bucket exists (in production, create via CloudFormation/Terraform)
    try:
        s3_hook.create_bucket(bucket_name=bucket_name)
    except Exception as e:
        logging.info(f"Bucket {bucket_name} already exists: {e}")

    # Upload data
    json_data = json.dumps(cocktail_data, indent=2)
    s3_hook.load_string(
        string_data=json_data,
        key=key,
        bucket_name=bucket_name,
        replace=True
    )

    logging.info(f"Extracted {len(cocktail_data)} cocktail recipes to s3://{bucket_name}/{key}")
    return key

def validate_data_quality():
    """
    Validate data quality after extraction.
    """
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook

    s3_hook = S3Hook(aws_conn_id='aws_default')
    bucket_name = 'mocktailverse-raw-data'
    key = f'extracted/{datetime.now().strftime("%Y/%m/%d")}/cocktail_data.json'

    # Read and validate data
    data = s3_hook.read_key(key=key, bucket_name=bucket_name)
    cocktail_data = json.loads(data)

    # Quality checks
    if not cocktail_data:
        raise ValueError("No cocktail data extracted")

    for cocktail in cocktail_data:
        if not all(key in cocktail for key in ['id', 'name', 'ingredients', 'instructions']):
            raise ValueError(f"Missing required fields in cocktail: {cocktail.get('id', 'unknown')}")

    logging.info(f"Data quality validation passed for {len(cocktail_data)} cocktails")
    return True

# Task definitions
extract_task = PythonOperator(
    task_id='extract_cocktail_data',
    python_callable=extract_cocktail_data,
    dag=dag,
)

validate_task = PythonOperator(
    task_id='validate_data_quality',
    python_callable=validate_data_quality,
    dag=dag,
)

# Glue ETL job for data transformation
transform_glue_task = GlueJobOperator(
    task_id='transform_with_glue',
    job_name='mocktailverse-etl-transform',
    script_location='s3://mocktailverse-scripts/glue/transform_cocktail_data.py',
    s3_bucket='mocktailverse-processed-data',
    iam_role_name='GlueServiceRole',
    script_args={
        '--job-bookmark-option': 'job-bookmark-enable',
        '--enable-metrics': '',
        '--input_bucket': 'mocktailverse-raw-data',
        '--output_bucket': 'mocktailverse-processed-data',
        '--date_partition': '{{ ds }}'
    },
    dag=dag,
)

# Lambda function for additional transformations
lambda_transform_task = LambdaInvokeFunctionOperator(
    task_id='lambda_enrichment',
    function_name='mocktailverse-transform-lambda',
    payload=json.dumps({
        'input_bucket': 'mocktailverse-processed-data',
        'output_bucket': 'mocktailverse-processed-data',
        'date_partition': '{{ ds }}'
    }),
    dag=dag,
)

def load_to_dynamodb():
    """
    Load transformed data into DynamoDB.
    """
    from airflow.providers.amazon.aws.hooks.dynamodb import DynamoDBHook
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook

    dynamodb_hook = DynamoDBHook(aws_conn_id='aws_default')
    s3_hook = S3Hook(aws_conn_id='aws_default')

    # Read transformed data from S3
    bucket_name = 'mocktailverse-processed-data'
    key = f'transformed/{datetime.now().strftime("%Y/%m/%d")}/enriched_cocktail_data.json'

    data = s3_hook.read_key(key=key, bucket_name=bucket_name)
    cocktail_data = json.loads(data)

    # Load to DynamoDB
    table_name = 'mocktailverse-cocktails'
    for cocktail in cocktail_data:
        dynamodb_hook.put_item(
            table_name=table_name,
            item=cocktail
        )

    logging.info(f"Loaded {len(cocktail_data)} cocktails to DynamoDB table {table_name}")

load_task = PythonOperator(
    task_id='load_to_dynamodb',
    python_callable=load_to_dynamodb,
    dag=dag,
)

# dbt transformation task
dbt_run_task = BashOperator(
    task_id='dbt_run_models',
    bash_command='cd /opt/airflow/dbt_project && dbt run --profiles-dir .',
    dag=dag,
)

# dbt testing task
dbt_test_task = BashOperator(
    task_id='dbt_test_models',
    bash_command='cd /opt/airflow/dbt_project && dbt test --profiles-dir .',
    dag=dag,
)

# Pipeline orchestration
extract_task >> validate_task >> transform_glue_task >> lambda_transform_task >> load_task >> dbt_run_task >> dbt_test_task
