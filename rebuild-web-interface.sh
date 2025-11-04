#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Rebuilding Web Interface${NC}"
echo ""

# Detect AWS configuration dynamically
echo -e "${BLUE}→ Detecting AWS configuration...${NC}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠ Error: Could not detect AWS account ID${NC}"
    echo "Please ensure AWS CLI is configured with valid credentials"
    exit 1
fi

AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-west-2")
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  AWS Region:  $AWS_REGION"
echo "  ECR Registry: $ECR_REGISTRY"
echo ""

# Configuration
IMAGE_NAME="insurance-claims/web-interface"
TAG="latest"

# Navigate to application directory
cd applications/insurance-claims-processing

# Login to ECR
echo -e "${BLUE}→ Logging in to ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build the Docker image
echo -e "${BLUE}→ Building Docker image...${NC}"
docker build \
    --platform linux/amd64 \
    -f docker/Dockerfile.web-interface \
    -t $ECR_REGISTRY/$IMAGE_NAME:$TAG \
    .

# Push to ECR
echo -e "${BLUE}→ Pushing to ECR...${NC}"
docker push $ECR_REGISTRY/$IMAGE_NAME:$TAG

# Restart the deployment
echo -e "${BLUE}→ Restarting deployment...${NC}"
kubectl rollout restart deployment/claims-web-interface -n insurance-claims

# Wait for rollout
echo -e "${BLUE}→ Waiting for rollout to complete...${NC}"
kubectl rollout status deployment/claims-web-interface -n insurance-claims

echo ""
echo -e "${GREEN}✓ Web interface updated successfully!${NC}"
echo ""

# Get ALB hostname dynamically
ALB_HOSTNAME=$(kubectl get ingress insurance-claims-ingress -n insurance-claims -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

if [ -n "$ALB_HOSTNAME" ]; then
    echo "Access the updated application:"
    echo "  http://$ALB_HOSTNAME"
    echo ""
    echo "Portals:"
    echo "  Claimant:   http://$ALB_HOSTNAME/claimant"
    echo "  Adjuster:   http://$ALB_HOSTNAME/adjuster"
    echo "  SIU:        http://$ALB_HOSTNAME/siu"
    echo "  Supervisor: http://$ALB_HOSTNAME/supervisor"
else
    echo "Get the application URL with:"
    echo "  kubectl get ingress insurance-claims-ingress -n insurance-claims"
fi
echo ""
