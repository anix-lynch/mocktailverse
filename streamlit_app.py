import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import boto3
from decimal import Decimal
import json

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="🍹 Mocktailverse | AWS ETL Pipeline",
    page_icon="🍹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hero Section
st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 0;'>🍹 Mocktailverse</h1>
        <p style='font-size: 1.5rem; color: #666; margin-top: 0.5rem;'>
            AWS Serverless ETL Pipeline Dashboard
        </p>
        <p style='font-size: 1.1rem; color: #888;'>
            S3 → Lambda → Glue → DynamoDB | Orchestrated by Airflow + dbt
        </p>
    </div>
""", unsafe_allow_html=True)

# Rest of your existing code continues here...
# (I'll preserve all the existing functionality)

# AWS Configuration
try:
    # Initialize DynamoDB client
    dynamodb = boto3.resource('dynamodb',
        region_name='us-east-1',
        aws_access_key_id=st.secrets.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=st.secrets.get("AWS_SECRET_ACCESS_KEY")
    )
    table = dynamodb.Table('mocktailverse-drinks')
    
    # Fetch data
    response = table.scan()
    items = response['Items']
    
    # Convert Decimal to float for Streamlit
    def decimal_to_float(obj):
        if isinstance(obj, list):
            return [decimal_to_float(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    items = decimal_to_float(items)
    df = pd.DataFrame(items)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Drinks", len(df))
    with col2:
        st.metric("Categories", df['category'].nunique() if 'category' in df.columns else 0)
    with col3:
        st.metric("Alcoholic Types", df['alcoholic'].nunique() if 'alcoholic' in df.columns else 0)
    with col4:
        st.metric("Glasses", df['glass'].nunique() if 'glass' in df.columns else 0)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Analytics", "🔍 Explore Data", "ℹ️ About Pipeline"])
    
    with tab1:
        st.subheader("Drink Distribution by Category")
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            fig = px.bar(x=category_counts.index, y=category_counts.values,
                        labels={'x': 'Category', 'y': 'Count'},
                        title="Drinks by Category")
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if 'alcoholic' in df.columns:
                st.subheader("Alcoholic vs Non-Alcoholic")
                alc_counts = df['alcoholic'].value_counts()
                fig = px.pie(values=alc_counts.values, names=alc_counts.index,
                           title="Alcoholic Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'glass' in df.columns:
                st.subheader("Top 10 Glass Types")
                glass_counts = df['glass'].value_counts().head(10)
                fig = px.bar(x=glass_counts.values, y=glass_counts.index,
                           orientation='h',
                           labels={'x': 'Count', 'y': 'Glass Type'},
                           title="Most Common Glasses")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Explore Mocktail Data")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            if 'category' in df.columns:
                categories = ['All'] + sorted(df['category'].unique().tolist())
                selected_category = st.selectbox("Filter by Category", categories)
        with col2:
            if 'alcoholic' in df.columns:
                alc_types = ['All'] + sorted(df['alcoholic'].unique().tolist())
                selected_alc = st.selectbox("Filter by Type", alc_types)
        
        # Apply filters
        filtered_df = df.copy()
        if selected_category != 'All' and 'category' in df.columns:
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        if selected_alc != 'All' and 'alcoholic' in df.columns:
            filtered_df = filtered_df[filtered_df['alcoholic'] == selected_alc]
        
        # Display data
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name="mocktailverse_data.csv",
            mime="text/csv"
        )
    
    with tab3:
        st.subheader("About This Pipeline")
        st.markdown("""
        ### 🏗️ Architecture
        This dashboard showcases a production-ready AWS serverless ETL pipeline:
        
        **Data Flow:**
        1. **Ingestion**: Raw data stored in S3
        2. **Processing**: AWS Lambda functions transform data
        3. **Cataloging**: AWS Glue maintains data catalog
        4. **Storage**: DynamoDB for fast NoSQL queries
        5. **Orchestration**: Apache Airflow + dbt for workflow management
        6. **Visualization**: This Streamlit dashboard
        
        ### 🛠️ Tech Stack
        - **Storage**: AWS S3
        - **Compute**: AWS Lambda
        - **Database**: DynamoDB
        - **Orchestration**: Airflow + dbt
        - **Infrastructure**: CloudFormation
        - **Deployment**: Docker
        
        ### 📊 Features
        - Serverless architecture
        - Real-time data processing
        - Scalable infrastructure
        - $0/month on AWS Free Tier
        
        ### 👨‍💻 Author
        **Anix Lynch** - Data Scientist & ML Engineer
        - 🌐 [Portfolio](https://gozeroshot.dev)
        - 💼 [LinkedIn](https://linkedin.com/in/anixlynch)
        - 🐙 [GitHub](https://github.com/anix-lynch)
        """)

except Exception as e:
    st.error(f"Error connecting to DynamoDB: {str(e)}")
    st.info("This dashboard requires AWS credentials to display live data.")
    
    # Show demo data
    st.subheader("Demo Mode")
    st.markdown("""
    This is a demo view. The full dashboard connects to:
    - AWS DynamoDB for real-time data
    - S3 for data storage
    - Lambda for processing
    - Airflow for orchestration
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>Built with ❤️ using AWS, Streamlit, and Python</p>
    <p>⭐ <a href='https://github.com/anix-lynch/mocktailverse' target='_blank'>Star on GitHub</a></p>
</div>
""", unsafe_allow_html=True)