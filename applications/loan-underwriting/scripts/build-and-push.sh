#!/bin/bash
#
# Build and Push Loan Underwriting Docker Image to ECR
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Loan Underwriting System${NC}"
echo -e "${GREEN}========================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$(dirname "$SCRIPT_DIR")"

# Auto-detect AWS account and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
AWS_REGION=${AWS_REGION:-us-west-2}

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_NAME="loan-underwriting"
IMAGE_TAG="${1:-latest}"

echo -e "${YELLOW}AWS Account ID:${NC} ${AWS_ACCOUNT_ID}"
echo -e "${YELLOW}AWS Region:${NC} ${AWS_REGION}"
echo -e "${YELLOW}ECR Registry:${NC} ${ECR_REGISTRY}"
echo -e "${YELLOW}Image:${NC} ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""

# Create ECR repository if it doesn't exist
echo -e "${YELLOW}Checking ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region ${AWS_REGION} >/dev/null 2>&1; then
    echo -e "${YELLOW}Creating ECR repository: ${IMAGE_NAME}${NC}"
    aws ecr create-repository \
        --repository-name ${IMAGE_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true
    echo -e "${GREEN}✓ Repository created${NC}"
else
    echo -e "${GREEN}✓ Repository exists${NC}"
fi

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${ECR_REGISTRY}
echo -e "${GREEN}✓ Logged in to ECR${NC}"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
cd "${APP_DIR}"
docker build \
    -f docker/Dockerfile \
    -t ${IMAGE_NAME}:${IMAGE_TAG} \
    -t ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
    .
echo -e "${GREEN}✓ Docker image built${NC}"

# Push to ECR
echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
echo -e "${GREEN}✓ Image pushed to ECR${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Image:${NC} ${ECR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
