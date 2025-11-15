"""
AWS Glue ETL Job for Mocktailverse Data Transformation
=======================================================

This PySpark job performs distributed data transformation on AWS Glue.
It processes raw cocktail data from S3, applies transformations, and writes
the results back to S3 for further processing.

Features:
- Distributed processing with Apache Spark
- Serverless ETL (AWS Glue free tier: 1 DPU/hour for first 1M objects)
- Automatic scaling based on data volume
- Integration with S3 and DynamoDB

Input: Raw cocktail JSON data from S3
Output: Transformed Parquet data in S3

Free Tier Compliant: Uses Glue's generous free tier for small datasets.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql.functions import *
from pyspark.sql.types import *
from awsglue.context import GlueContext
from awsglue.job import Job
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def define_cocktail_schema():
    """
    Define the schema for cocktail data.
    """
    return StructType([
        StructField("id", StringType(), True),
        StructField("name", StringType(), True),
        StructField("category", StringType(), True),
        StructField("ingredients", ArrayType(
            StructType([
                StructField("name", StringType(), True),
                StructField("amount", StringType(), True),
                StructField("unit", StringType(), True)
            ])
        ), True),
        StructField("instructions", StringType(), True),
        StructField("glass", StringType(), True),
        StructField("extracted_at", StringType(), True)
    ])

def main():
    """
    Main ETL function for processing cocktail data.
    """
    # Get job parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'input_bucket',
        'output_bucket',
        'date_partition'
    ])

    logger.info("Starting Glue ETL job for Mocktailverse")
    logger.info(f"Input bucket: {args['input_bucket']}")
    logger.info(f"Output bucket: {args['output_bucket']}")
    logger.info(f"Date partition: {args['date_partition']}")

    # Initialize Glue context
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)

    try:
        # Read raw cocktail data from S3
        input_path = f"s3://{args['input_bucket']}/extracted/{args['date_partition']}/cocktail_data.json"

        logger.info(f"Reading data from: {input_path}")

        # Define schema for JSON data
        schema = define_cocktail_schema()

        # Read JSON data
        raw_df = spark.read.schema(schema).json(input_path)

        logger.info(f"Read {raw_df.count()} raw cocktail records")

        # Apply transformations
        transformed_df = transform_cocktail_data(raw_df, args['date_partition'])

        # Write transformed data to S3
        output_path = f"s3://{args['output_bucket']}/transformed/{args['date_partition']}/transformed_cocktail_data"

        logger.info(f"Writing transformed data to: {output_path}")

        # Write as Parquet for efficiency
        transformed_df.write \
            .mode("overwrite") \
            .parquet(output_path)

        # Also write as JSON for Lambda processing
        json_output_path = f"s3://{args['output_bucket']}/transformed/{args['date_partition']}/transformed_cocktail_data.json"

        transformed_df.write \
            .mode("overwrite") \
            .json(json_output_path)

        logger.info("Glue ETL job completed successfully")

        # Log success metrics
        final_count = transformed_df.count()
        logger.info(f"Processed {final_count} cocktail records")

        job.commit()

    except Exception as e:
        logger.error(f"Glue ETL job failed: {str(e)}")
        raise

def transform_cocktail_data(df, date_partition):
    """
    Apply data transformations to cocktail DataFrame.

    Args:
        df: Raw cocktail DataFrame
        date_partition: Date partition string

    Returns:
        Transformed DataFrame
    """
    # Add processing metadata
    df = df.withColumn("processed_at", current_timestamp())
    df = df.withColumn("data_quality_score", lit(1.0))  # Placeholder for quality scoring
    df = df.withColumn("partition_date", lit(date_partition))

    # Clean and standardize data
    df = df.withColumn("name", trim(col("name")))
    df = df.withColumn("category", trim(lower(col("category"))))
    df = df.withColumn("glass", trim(col("glass")))

    # Validate required fields
    df = df.filter(
        (col("id").isNotNull()) &
        (col("name").isNotNull()) &
        (col("ingredients").isNotNull()) &
        (length(col("name")) > 0)
    )

    # Add data quality checks
    df = df.withColumn(
        "has_valid_ingredients",
        when(size(col("ingredients")) > 0, True).otherwise(False)
    )

    df = df.withColumn(
        "has_instructions",
        when((col("instructions").isNotNull()) & (length(col("instructions")) > 0), True).otherwise(False)
    )

    # Calculate ingredient statistics
    df = df.withColumn("ingredient_count", size(col("ingredients")))

    # Extract spirit information
    df = df.withColumn(
        "primary_spirit",
        when(
            exists_in_array(col("ingredients"), lambda x: lower(x.getField("name")).contains("rum")), "rum"
        ).when(
            exists_in_array(col("ingredients"), lambda x: lower(x.getField("name")).contains("vodka")), "vodka"
        ).when(
            exists_in_array(col("ingredients"), lambda x: lower(x.getField("name")).contains("gin")), "gin"
        ).when(
            exists_in_array(col("ingredients"), lambda x: lower(x.getField("name")).contains("tequila")), "tequila"
        ).when(
            exists_in_array(col("ingredients"), lambda x: lower(x.getField("name")).contains("whiskey")), "whiskey"
        ).otherwise("other")
    )

    # Add transformation flags
    df = df.withColumn("transformed_by_glue", lit(True))
    df = df.withColumn("glue_job_version", lit("1.0.0"))

    return df

def exists_in_array(array_col, condition):
    """
    Check if any element in an array matches a condition.

    Args:
        array_col: Array column to check
        condition: Lambda function for condition

    Returns:
        Boolean indicating if condition is met
    """
    return size(filter(array_col, condition)) > 0

if __name__ == "__main__":
    main()
