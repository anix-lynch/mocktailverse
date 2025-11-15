# Multi-stage Docker build for AWS ETL Pipeline
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AIRFLOW_HOME=/opt/airflow \
    AIRFLOW__CORE__LOAD_EXAMPLES=False

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create airflow user
RUN useradd -ms /bin/bash -d ${AIRFLOW_HOME} airflow

# Stage 1: Builder stage for dependencies
FROM base as builder

WORKDIR /build

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime stage
FROM base

# Copy installed packages from builder
COPY --from=builder /root/.local /home/airflow/.local

# Set PATH to include user-installed packages
ENV PATH=/home/airflow/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p ${AIRFLOW_HOME}/dags ${AIRFLOW_HOME}/logs ${AIRFLOW_HOME}/plugins

# Copy application code
COPY airflow_dag.py ${AIRFLOW_HOME}/dags/
COPY dbt_project/ ${AIRFLOW_HOME}/dbt_project/
COPY lambda/ /opt/lambda/

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Change ownership to airflow user
RUN chown -R airflow:airflow ${AIRFLOW_HOME}

# Switch to airflow user
USER airflow

# Set working directory
WORKDIR ${AIRFLOW_HOME}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port for Airflow webserver
EXPOSE 8080

# Default entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
