#!/bin/bash
set -e

# Initialize Airflow database if it doesn't exist
if [ ! -f "${AIRFLOW_HOME}/airflow.db" ]; then
    echo "Initializing Airflow database..."
    airflow db init
fi

# Create admin user if it doesn't exist
if ! airflow users list | grep -q admin; then
    echo "Creating admin user..."
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin
fi

# Set AWS credentials from environment if provided
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Configuring AWS credentials..."
    mkdir -p ~/.aws
    cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

    if [ -n "$AWS_DEFAULT_REGION" ]; then
        cat > ~/.aws/config << EOF
[default]
region = ${AWS_DEFAULT_REGION}
EOF
    fi
fi

# Execute the command passed to the container
exec "$@"
