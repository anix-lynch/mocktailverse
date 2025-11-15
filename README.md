# 🍹 Mocktailverse: AWS ETL Pipeline

An end-to-end AWS-native ETL/ELT pipeline demonstrating enterprise-grade data engineering practices with serverless technologies.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Amazon S3     │    │   AWS Glue      │    │  DynamoDB       │
│   (Extract)     │───▶│   (Transform)   │───▶│   (Load)        │
│                 │    │   PySpark ETL   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AWS Lambda    │    │ Apache Airflow  │    │     dbt-core    │
│ (Enrichment)    │    │ (Orchestration) │    │   (Modeling)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker (optional, for containerized deployment)
- Python 3.11+

### 1. Clone and Setup
```bash
git clone <repository-url>
cd mocktailverse

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and default region
```

### 3. Deploy Infrastructure
```bash
# Create S3 buckets, DynamoDB tables, and IAM roles
# (Infrastructure as Code deployment scripts would go here)
```

### 4. Run ETL Pipeline
```bash
# Trigger the Airflow DAG
airflow dags trigger mocktailverse_etl_pipeline
```

## 📁 Project Structure

```
mocktailverse/
├── airflow_dag.py              # Apache Airflow ETL orchestration
├── lambda/
│   └── transform.py            # AWS Lambda data enrichment function
├── glue_job.py                 # AWS Glue PySpark ETL job
├── dbt_project/                # dbt data transformation project
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       └── marts/
├── dynamodb_schema.json        # DynamoDB table schema
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-entrypoint.sh        # Docker entrypoint script
└── README.md                   # This file
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Extract** | Amazon S3 | Raw data storage and ingestion |
| **Transform** | AWS Glue + PySpark | Distributed data processing |
| **Transform** | AWS Lambda | Serverless data enrichment |
| **Load** | Amazon DynamoDB | NoSQL data storage |
| **Model** | dbt-core + Athena | Data modeling and analytics |
| **Orchestrate** | Apache Airflow | Pipeline orchestration |

## 🎯 Key Features

### Enterprise ETL Capabilities
- **Serverless Architecture**: No servers to manage, automatic scaling
- **Distributed Processing**: PySpark on AWS Glue for large datasets
- **Data Quality**: Automated validation and monitoring
- **Incremental Processing**: Efficient handling of new data
- **Error Handling**: Robust retry mechanisms and dead letter queues

### AWS Free Tier Compliant
- **Lambda**: 1M requests/month free
- **Glue**: 1 DPU-hour/month free for first 1M objects
- **S3**: 5GB storage + 20K GET requests free
- **DynamoDB**: 25GB storage + 200M requests free
- **Athena**: Pay per query (typically very low cost)

## 📊 Data Flow

1. **Extract**: Cocktail data ingested from APIs → Stored in S3
2. **Transform**: PySpark ETL on Glue → Data cleansing and standardization
3. **Enrich**: Lambda functions → Add metadata and derived fields
4. **Load**: Processed data → DynamoDB for operational queries
5. **Model**: dbt transforms → Analytics-ready tables in Athena

## 🔧 Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Airflow Configuration
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__CORE__LOAD_EXAMPLES=False
```

### AWS Permissions Required
- `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query`
- `lambda:InvokeFunction`
- `glue:StartJobRun`
- `athena:StartQueryExecution`

## 📈 Monitoring & Observability

- **Airflow UI**: Pipeline status and task monitoring
- **CloudWatch**: AWS service metrics and logs
- **Athena Queries**: Data quality and analytics
- **DynamoDB Metrics**: Performance monitoring

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Validate dbt models
cd dbt_project && dbt test

# Run ETL pipeline locally
airflow dags test mocktailverse_etl_pipeline
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker
docker build -t mocktailverse-etl .
docker run -p 8080:8080 mocktailverse-etl airflow webserver
```

### AWS Deployment
- Deploy Lambda functions via AWS SAM/CloudFormation
- Create Glue jobs through AWS Console or CDK
- Set up Airflow on EC2/ECS or MWAA (Managed Workflows)

## 📚 Documentation

- [AWS Glue PySpark ETL](./glue_job.py) - Distributed data processing
- [AWS Lambda Enrichment](./lambda/transform.py) - Serverless transformations
- [Airflow Orchestration](./airflow_dag.py) - Pipeline scheduling
- [dbt Data Modeling](./dbt_project/) - Analytics engineering

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Cost Considerations

This pipeline is designed to operate within AWS Free Tier limits for development and small-scale production. For larger workloads:

- Monitor Glue DPU-hours usage
- Consider DynamoDB on-demand pricing for variable loads
- Use Athena for cost-effective analytics queries
- Implement data lifecycle policies for S3

## 🆘 Support

For issues and questions:
1. Check the troubleshooting guide
2. Review AWS service documentation
3. Open an issue on GitHub

---

**Built with ❤️ for the AWS Data Engineering community**