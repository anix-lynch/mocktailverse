#!/usr/bin/env python3
"""
Test script for Mocktailverse ETL Pipeline
==========================================

This script validates that all components of the AWS ETL pipeline
are correctly configured and can run locally for development/testing.

Usage:
    python test_pipeline.py

Tests:
- AWS credentials validation
- S3 bucket access
- DynamoDB table schema validation
- Lambda function syntax check
- Glue job syntax validation
- dbt project configuration
- Docker build validation
"""

import boto3
import json
import sys
import os
from pathlib import Path
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PipelineTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.project_root = Path(__file__).parent

    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """Log the result of a test."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if message:
            logger.info(f"   {message}")

        if success:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def test_aws_credentials(self):
        """Test AWS credentials configuration."""
        try:
            # Try to create a client to validate credentials
            sts_client = boto3.client('sts')
            identity = sts_client.get_caller_identity()
            account_id = identity['Account']
            self.log_test_result("AWS Credentials", True, f"Authenticated as account: {account_id}")
            return True
        except Exception as e:
            self.log_test_result("AWS Credentials", False, f"Failed to authenticate: {e}")
            return False

    def test_s3_access(self):
        """Test S3 bucket access."""
        try:
            s3_client = boto3.client('s3')

            # Test buckets that should exist
            test_buckets = [
                'mocktailverse-raw-data',
                'mocktailverse-processed-data'
            ]

            for bucket in test_buckets:
                try:
                    s3_client.head_bucket(Bucket=bucket)
                    self.log_test_result(f"S3 Bucket {bucket}", True, "Bucket exists and accessible")
                except s3_client.exceptions.NoSuchBucket:
                    self.log_test_result(f"S3 Bucket {bucket}", False, "Bucket does not exist")
                    return False
                except Exception as e:
                    self.log_test_result(f"S3 Bucket {bucket}", False, f"Access error: {e}")
                    return False

            return True
        except Exception as e:
            self.log_test_result("S3 Access", False, f"Failed to test S3: {e}")
            return False

    def test_dynamodb_schema(self):
        """Test DynamoDB table schema."""
        try:
            with open(self.project_root / 'dynamodb_schema.json', 'r') as f:
                schema = json.load(f)

            # Validate required fields
            required_fields = ['TableName', 'KeySchema', 'AttributeDefinitions']
            for field in required_fields:
                if field not in schema:
                    self.log_test_result("DynamoDB Schema", False, f"Missing required field: {field}")
                    return False

            # Check table name
            if schema['TableName'] != 'mocktailverse-cocktails':
                self.log_test_result("DynamoDB Schema", False, "Incorrect table name")
                return False

            self.log_test_result("DynamoDB Schema", True, "Schema is valid")
            return True
        except Exception as e:
            self.log_test_result("DynamoDB Schema", False, f"Schema validation failed: {e}")
            return False

    def test_lambda_syntax(self):
        """Test Lambda function syntax."""
        lambda_file = self.project_root / 'lambda' / 'transform.py'
        return self._test_python_syntax(lambda_file, "Lambda Function")

    def test_glue_syntax(self):
        """Test Glue job syntax."""
        glue_file = self.project_root / 'glue_job.py'
        return self._test_python_syntax(glue_file, "Glue Job")

    def test_airflow_syntax(self):
        """Test Airflow DAG syntax."""
        airflow_file = self.project_root / 'airflow_dag.py'
        return self._test_python_syntax(airflow_file, "Airflow DAG")

    def test_streamlit_syntax(self):
        """Test Streamlit app syntax."""
        streamlit_file = self.project_root / 'streamlit_app.py'
        return self._test_python_syntax(streamlit_file, "Streamlit App")

    def _test_python_syntax(self, file_path: Path, component_name: str):
        """Test Python file syntax."""
        try:
            with open(file_path, 'r') as f:
                code = f.read()

            # Try to compile the code
            compile(code, str(file_path), 'exec')
            self.log_test_result(f"{component_name} Syntax", True, f"{file_path.name} compiles successfully")
            return True
        except SyntaxError as e:
            self.log_test_result(f"{component_name} Syntax", False, f"Syntax error in {file_path.name}: {e}")
            return False
        except Exception as e:
            self.log_test_result(f"{component_name} Syntax", False, f"Error reading {file_path.name}: {e}")
            return False

    def test_dbt_project(self):
        """Test dbt project configuration."""
        try:
            dbt_project_file = self.project_root / 'dbt_project' / 'dbt_project.yml'
            profiles_file = self.project_root / 'dbt_project' / 'profiles.yml'

            if not dbt_project_file.exists():
                self.log_test_result("dbt Project", False, "dbt_project.yml not found")
                return False

            if not profiles_file.exists():
                self.log_test_result("dbt Project", False, "profiles.yml not found")
                return False

            # Check if dbt is installed
            try:
                result = subprocess.run(['dbt', '--version'], capture_output=True, text=True, cwd=self.project_root / 'dbt_project')
                if result.returncode == 0:
                    self.log_test_result("dbt Installation", True, "dbt is installed and accessible")
                else:
                    self.log_test_result("dbt Installation", False, "dbt command failed")
                    return False
            except FileNotFoundError:
                self.log_test_result("dbt Installation", False, "dbt is not installed")
                return False

            self.log_test_result("dbt Project", True, "Project structure is valid")
            return True
        except Exception as e:
            self.log_test_result("dbt Project", False, f"dbt validation failed: {e}")
            return False

    def test_docker_build(self):
        """Test Docker build (optional)."""
        try:
            # Check if Docker is available
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                self.log_test_result("Docker Build", False, "Docker is not installed")
                return False

            # Test Dockerfile syntax
            dockerfile = self.project_root / 'Dockerfile'
            if not dockerfile.exists():
                self.log_test_result("Docker Build", False, "Dockerfile not found")
                return False

            # Try to build (this might take time, so we'll just check syntax)
            result = subprocess.run(['docker', 'build', '--dry-run', '-t', 'mocktailverse-test', '.'], cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                self.log_test_result("Docker Build", True, "Dockerfile syntax is valid")
                return True
            else:
                self.log_test_result("Docker Build", False, f"Dockerfile error: {result.stderr}")
                return False
        except Exception as e:
            self.log_test_result("Docker Build", False, f"Docker test failed: {e}")
            return False

    def run_all_tests(self):
        """Run all pipeline tests."""
        logger.info("🧪 Starting Mocktailverse ETL Pipeline Tests")
        logger.info("=" * 60)

        # Core AWS tests
        self.test_aws_credentials()
        self.test_s3_access()
        self.test_dynamodb_schema()

        # Code quality tests
        self.test_lambda_syntax()
        self.test_glue_syntax()
        self.test_airflow_syntax()
        self.test_streamlit_syntax()

        # Infrastructure tests
        self.test_dbt_project()
        self.test_docker_build()

        # Summary
        logger.info("=" * 60)
        logger.info(f"📊 Test Results: {self.tests_passed} passed, {self.tests_failed} failed")

        if self.tests_failed == 0:
            logger.info("🎉 All tests passed! Pipeline is ready for deployment.")
            return True
        else:
            logger.error("❌ Some tests failed. Please fix the issues before deploying.")
            return False

def main():
    """Main test function."""
    tester = PipelineTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
