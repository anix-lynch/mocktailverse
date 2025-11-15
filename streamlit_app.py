"""
Streamlit Dashboard for Mocktailverse ETL Pipeline Monitoring
============================================================

A real-time dashboard to monitor the AWS ETL pipeline performance,
data quality metrics, and business insights from the cocktail dataset.

Features:
- ETL pipeline status monitoring
- Data quality metrics visualization
- Cocktail analytics and insights
- Real-time AWS service metrics
- Cost monitoring and optimization tips

Deploy to Streamlit Cloud for free hosting.
"""

import streamlit as st
import pandas as pd
import boto3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from botocore.exceptions import ClientError
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Mocktailverse ETL Dashboard",
    page_icon="🍹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize AWS clients
@st.cache_resource
def init_aws_clients():
    """Initialize AWS clients with error handling."""
    try:
        # Get credentials from Streamlit secrets or environment
        aws_access_key = st.secrets.get("AWS_ACCESS_KEY_ID", os.environ.get("AWS_ACCESS_KEY_ID"))
        aws_secret_key = st.secrets.get("AWS_SECRET_ACCESS_KEY", os.environ.get("AWS_SECRET_ACCESS_KEY"))
        region = st.secrets.get("AWS_DEFAULT_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-2"))
        
        if not aws_access_key or not aws_secret_key:
            st.error("⚠️ AWS credentials not configured. Add them in Streamlit Cloud Secrets.")
            return None, None, None
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        dynamodb_client = boto3.client(
            'dynamodb',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        athena_client = boto3.client(
            'athena',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        return s3_client, dynamodb_client, athena_client
    except Exception as e:
        st.error(f"Failed to initialize AWS clients: {e}")
        return None, None, None

s3_client, dynamodb_client, athena_client = init_aws_clients()

def load_css():
    """Load custom CSS for better styling."""
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .status-success {
        color: #00c853;
        font-weight: bold;
    }
    .status-error {
        color: #d32f2f;
        font-weight: bold;
    }
    .status-warning {
        color: #ff9800;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

def get_etl_status():
    """Get the current ETL pipeline status."""
    try:
        # Check recent S3 objects for pipeline activity
        buckets_to_check = [
            'mocktailverse-raw-data',
            'mocktailverse-processed-data',
            'mocktailverse-dbt-data'
        ]

        latest_activity = None
        total_objects = 0

        for bucket in buckets_to_check:
            try:
                response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=100)
                if 'Contents' in response:
                    total_objects += len(response['Contents'])
                    for obj in response['Contents']:
                        if latest_activity is None or obj['LastModified'] > latest_activity:
                            latest_activity = obj['LastModified']
            except ClientError:
                continue  # Bucket might not exist yet

        if latest_activity:
            time_diff = datetime.now(latest_activity.tzinfo) - latest_activity
            if time_diff < timedelta(hours=1):
                return "🟢 ACTIVE", f"Last activity: {latest_activity.strftime('%Y-%m-%d %H:%M:%S')}"
            elif time_diff < timedelta(hours=24):
                return "🟡 IDLE", f"Last activity: {latest_activity.strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                return "🔴 INACTIVE", f"Last activity: {latest_activity.strftime('%Y-%m-%d %H:%M:%S')}"

        return "🔵 NOT STARTED", "No pipeline activity detected"

    except Exception as e:
        logger.error(f"Error checking ETL status: {e}")
        return "❌ ERROR", f"Unable to check status: {e}"

def get_cocktail_metrics():
    """Get cocktail dataset metrics from DynamoDB."""
    try:
        # Query DynamoDB for summary statistics
        response = dynamodb_client.scan(
            TableName='mocktailverse-cocktails',
            Select='COUNT'
        )

        total_cocktails = response.get('Count', 0)

        # Get sample data for analysis
        response = dynamodb_client.scan(
            TableName='mocktailverse-cocktails',
            Limit=100
        )

        if 'Items' in response:
            items = response['Items']
            df = pd.DataFrame([{
                'id': item['id']['S'],
                'name': item.get('name', {}).get('S', 'Unknown'),
                'category': item.get('category', {}).get('S', 'Unknown'),
                'spirit_type': item.get('spirit_type', {}).get('S', 'Unknown'),
                'complexity_score': float(item.get('complexity_score', {}).get('N', 0)),
                'estimated_calories': int(item.get('estimated_calories', {}).get('N', 0)),
                'is_alcoholic': item.get('is_alcoholic', {}).get('BOOL', False)
            } for item in items])

            return total_cocktails, df

    except ClientError as e:
        logger.error(f"Error querying DynamoDB: {e}")

    return 0, pd.DataFrame()

def create_metrics_charts(df):
    """Create interactive charts for cocktail metrics."""
    if df.empty:
        return None, None, None

    # Spirit type distribution
    spirit_chart = px.pie(
        df,
        names='spirit_type',
        title='Cocktail Distribution by Spirit Type',
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    # Complexity distribution
    complexity_chart = px.histogram(
        df,
        x='complexity_score',
        nbins=10,
        title='Cocktail Complexity Distribution',
        labels={'complexity_score': 'Complexity Score', 'count': 'Number of Cocktails'}
    )

    # Calories vs Complexity scatter plot
    scatter_chart = px.scatter(
        df,
        x='complexity_score',
        y='estimated_calories',
        color='spirit_type',
        title='Calories vs Complexity by Spirit Type',
        labels={
            'complexity_score': 'Complexity Score',
            'estimated_calories': 'Estimated Calories',
            'spirit_type': 'Spirit Type'
        }
    )

    return spirit_chart, complexity_chart, scatter_chart

def get_cost_estimate():
    """Provide rough cost estimates based on usage."""
    # These are rough estimates - in production you'd use Cost Explorer API
    estimates = {
        'S3 Storage': '$0.05/month (Free tier)',
        'DynamoDB': '$0.10/month (Free tier)',
        'Lambda': '$0.02/month (Free tier)',
        'Glue': '$0.15/month (Free tier)',
        'Athena': '$0.01/month (Pay per query)',
        'Total Estimated': '$0.33/month'
    }
    return estimates

def main():
    """Main dashboard function."""
    load_css()

    # Header
    st.title("🍹 Mocktailverse AWS ETL Pipeline Dashboard")
    st.caption("Real-time monitoring for AWS-native serverless ETL: S3 → Lambda → Glue → DynamoDB | Orchestrated by Airflow + dbt")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("🔧 Controls")

        if st.button("🔄 Refresh Data"):
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Pipeline Status")

        status, details = get_etl_status()
        if "ACTIVE" in status:
            st.markdown(f"<p class='status-success'>{status}</p>", unsafe_allow_html=True)
        elif "IDLE" in status:
            st.markdown(f"<p class='status-warning'>{status}</p>", unsafe_allow_html=True)
        elif "ERROR" in status:
            st.markdown(f"<p class='status-error'>{status}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p>{status}</p>", unsafe_allow_html=True)

        st.caption(details)

        st.markdown("---")
        st.markdown("### 💰 Cost Estimate")
        costs = get_cost_estimate()
        for service, cost in costs.items():
            st.caption(f"{service}: {cost}")

    # Main content
    col1, col2, col3, col4 = st.columns(4)

    # Get metrics
    total_cocktails, df = get_cocktail_metrics()

    with col1:
        st.metric("📊 Total Cocktails", f"{total_cocktails:,}")

    with col2:
        avg_complexity = df['complexity_score'].mean() if not df.empty else 0
        st.metric("🎯 Avg Complexity", f"{avg_complexity:.1f}")

    with col3:
        avg_calories = df['estimated_calories'].mean() if not df.empty else 0
        st.metric("🔥 Avg Calories", f"{avg_calories:.0f}")

    with col4:
        spirit_types = df['spirit_type'].nunique() if not df.empty else 0
        st.metric("🥃 Spirit Types", spirit_types)

    st.markdown("---")

    # Charts section
    if not df.empty:
        st.header("📈 Analytics Dashboard")

        tab1, tab2, tab3 = st.tabs(["Spirit Distribution", "Complexity Analysis", "Calories vs Complexity"])

        spirit_chart, complexity_chart, scatter_chart = create_metrics_charts(df)

        with tab1:
            if spirit_chart:
                st.plotly_chart(spirit_chart, use_container_width=True)

        with tab2:
            if complexity_chart:
                st.plotly_chart(complexity_chart, use_container_width=True)

        with tab3:
            if scatter_chart:
                st.plotly_chart(scatter_chart, use_container_width=True)

        # Data table
        st.markdown("---")
        st.header("📋 Recent Cocktails")
        st.dataframe(
            df[['name', 'spirit_type', 'complexity_score', 'estimated_calories', 'is_alcoholic']]
            .sort_values('complexity_score', ascending=False)
            .head(10),
            use_container_width=True
        )
    else:
        st.info("📝 No cocktail data available yet. Run the ETL pipeline to populate the dashboard.")

    # Pipeline information
    st.markdown("---")
    st.header("🔄 ETL Pipeline Information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📁 Data Sources")
        st.markdown("""
        - **Raw Data**: S3 (`mocktailverse-raw-data`)
        - **Processed Data**: S3 (`mocktailverse-processed-data`)
        - **Analytics**: Athena (`mocktailverse-dbt-data`)
        - **Operational**: DynamoDB (`mocktailverse-cocktails`)
        """)

    with col2:
        st.subheader("⚙️ Pipeline Components")
        st.markdown("""
        - **Extract**: S3 + External APIs
        - **Transform**: Glue (PySpark) + Lambda
        - **Load**: DynamoDB + S3
        - **Model**: dbt-core + Athena
        - **Orchestrate**: Apache Airflow
        """)

    # Footer
    st.markdown("---")
    st.caption("🍹 Mocktailverse ETL Pipeline - Built with AWS, Airflow, dbt, and Streamlit")
    st.caption("Free Tier Compliant • Serverless • Scalable")

if __name__ == "__main__":
    main()
