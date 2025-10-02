#!/bin/bash

# WARNING: Make sure to have the ./keys/OrianeSearchAPIv1_dev.pem file.
# Email alex@oriane.xyz for authorization if missing.

# Make sure the connect script is executable
chmod +x ./connect_to_ec2.sh

# EC2 instance details
EC2_HOST="ec2-3-239-35-32.compute-1.amazonaws.com"
EC2_USER="ubuntu"
KEY_FILE="./keys/OrianeSearchAPIv1_dev.pem"
ECR_REPO="509399609859.dkr.ecr.us-east-1.amazonaws.com/oriane-search-api-v1:latest"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Key file $KEY_FILE not found!"
    echo "Please email alex@oriane.xyz for authorization if missing."
    exit 1
fi

echo "🚀 Oriane Search API Deployment"
echo "==============================="
echo ""
echo "Choose deployment option:"
echo "1. Build and push new image to ECR (using push_api_search.sh), then deploy"
echo "2. Use latest image from ECR and deploy"
echo ""
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "🏗️  Building and pushing new image..."
        echo "======================================"
        
        # Check if push_api_search.sh exists
        if [ ! -f "./push_api_search.sh" ]; then
            echo "Error: push_api_search.sh not found in current directory!"
            echo "Please ensure the script is in the same directory as deploy_to_ec2.sh"
            exit 1
        fi
        
        # Make push script executable and run it
        chmod +x ./push_api_search.sh
        if ! ./push_api_search.sh; then
            echo "❌ Image build and push failed!"
            exit 1
        fi
        
        echo "✅ Image build and push completed successfully!"
        echo ""
        ;;
    2)
        echo ""
        echo "📦 Using latest image from ECR..."
        echo "================================="
        ;;
    *)
        echo "Invalid choice. Please enter 1 or 2."
        exit 1
        ;;
esac

echo "🚀 Connecting to EC2 instance and deploying container..."
echo "======================================================="

# Execute commands on EC2 instance via SSH
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_HOST" << 'EOF'
    # Function to configure AWS credentials
    configure_aws_credentials() {
        echo "Attempting to configure AWS credentials..."
        
        # Check if AWS credentials are available in environment
        if [ ! -z "$AWS_ACCESS_KEY_ID" ] && [ ! -z "$AWS_SECRET_ACCESS_KEY" ]; then
            echo "Using AWS credentials from environment variables"
            return 0
        fi
        
        # Check if credentials file exists
        if [ -f ~/.aws/credentials ]; then
            echo "AWS credentials file found"
            return 0
        fi
        
        # Check if IAM role is attached to EC2 instance
        if curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ >/dev/null 2>&1; then
            echo "IAM role detected on EC2 instance"
            return 0
        fi
        
        # Try to configure AWS CLI interactively
        echo "No AWS credentials found. Please configure them:"
        echo "You can either:"
        echo "1. Set environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        echo "2. Run: aws configure"
        echo "3. Attach an IAM role to the EC2 instance"
        return 1
    }
    
    # Try to configure AWS credentials
    if ! configure_aws_credentials; then
        echo "❌ AWS credentials not configured. Please configure them manually on the EC2 instance."
        echo "You can SSH to the instance and run: aws configure"
        exit 1
    fi
    
    # Check if AWS CLI is configured
    echo "Checking AWS configuration..."
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        echo "Error: AWS CLI not configured or credentials expired!"
        echo "Please configure AWS credentials on the EC2 instance."
        exit 1
    fi
    
    echo "✅ AWS credentials validated successfully"
    
    # Login to ECR
    echo "Logging into ECR..."
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 509399609859.dkr.ecr.us-east-1.amazonaws.com
    
    # Stop and remove existing containers that might conflict
    echo "Cleaning up existing containers..."
    docker stop oriane-search-api oriane-search-api-v1 2>/dev/null || true
    docker rm oriane-search-api oriane-search-api-v1 2>/dev/null || true
    
    # Check if port 8000 is in use and stop any container using it
    PORT_CONTAINER=$(docker ps --format "table {{.Names}}\t{{.Ports}}" | grep ":8000->" | awk '{print $1}')
    if [ ! -z "$PORT_CONTAINER" ]; then
        echo "Stopping container using port 8000: $PORT_CONTAINER"
        docker stop "$PORT_CONTAINER" 2>/dev/null || true
        docker rm "$PORT_CONTAINER" 2>/dev/null || true
    fi
    
    # Pull the latest image from ECR
    echo "Pulling latest image from ECR..."
    docker pull 509399609859.dkr.ecr.us-east-1.amazonaws.com/oriane-search-api-v1:latest
    
    # Run the new container
    echo "Starting new container..."
    docker run -d \
        --name oriane-search-api-v1 \
        -p 8000:8000 \
        --restart unless-stopped \
        509399609859.dkr.ecr.us-east-1.amazonaws.com/oriane-search-api-v1:latest
    
    # Wait a moment for container to start
    sleep 3
    
    # Verify container is running
    echo "Verifying container status..."
    if docker ps | grep -q oriane-search-api-v1; then
        echo "✅ Container successfully deployed and running on port 8000"
        docker ps | grep oriane-search-api-v1
    else
        echo "❌ Container failed to start. Checking logs..."
        docker logs oriane-search-api-v1
        exit 1
    fi
EOF

echo "Deployment completed!"
