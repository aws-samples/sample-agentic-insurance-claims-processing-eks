#!/bin/bash
#
# Deploy Loan Underwriting System to EKS
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying Loan Underwriting System${NC}"
echo -e "${GREEN}========================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$(dirname "$SCRIPT_DIR")"
K8S_DIR="${APP_DIR}/infrastructure/kubernetes"

# Auto-detect AWS account and region
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region)
AWS_REGION=${AWS_REGION:-us-west-2}

echo -e "${YELLOW}AWS Account ID:${NC} ${AWS_ACCOUNT_ID}"
echo -e "${YELLOW}AWS Region:${NC} ${AWS_REGION}"
echo ""

# Check if EKS cluster is accessible
echo -e "${YELLOW}Checking EKS cluster access...${NC}"
if ! kubectl get nodes >/dev/null 2>&1; then
    echo -e "${RED}Error: Cannot access EKS cluster${NC}"
    echo -e "${YELLOW}Please ensure kubectl is configured correctly${NC}"
    exit 1
fi
echo -e "${GREEN}✓ EKS cluster accessible${NC}"

# Create namespace if it doesn't exist
echo -e "${YELLOW}Checking namespace...${NC}"
if ! kubectl get namespace insurance-claims >/dev/null 2>&1; then
    echo -e "${YELLOW}Creating namespace: insurance-claims${NC}"
    kubectl create namespace insurance-claims
    echo -e "${GREEN}✓ Namespace created${NC}"
else
    echo -e "${GREEN}✓ Namespace exists${NC}"
fi

# Process and apply Kubernetes manifests
echo -e "${YELLOW}Deploying Kubernetes resources...${NC}"
cat ${K8S_DIR}/deployment.yaml | \
    sed "s/\${AWS_ACCOUNT_ID}/${AWS_ACCOUNT_ID}/g" | \
    sed "s/\${AWS_REGION}/${AWS_REGION}/g" | \
    kubectl apply -f -
echo -e "${GREEN}✓ Deployment applied${NC}"

# Wait for deployment to be ready
echo -e "${YELLOW}Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s \
    deployment/loan-underwriting -n insurance-claims
echo -e "${GREEN}✓ Deployment ready${NC}"

# Get service status
echo ""
echo -e "${YELLOW}Deployment Status:${NC}"
kubectl get deployment loan-underwriting -n insurance-claims
echo ""
echo -e "${YELLOW}Pods:${NC}"
kubectl get pods -n insurance-claims -l app=loan-underwriting
echo ""
echo -e "${YELLOW}Service:${NC}"
kubectl get service loan-underwriting-service -n insurance-claims
echo ""
echo -e "${YELLOW}Ingress:${NC}"
kubectl get ingress loan-underwriting-ingress -n insurance-claims

# Get ALB URL
echo ""
echo -e "${YELLOW}Getting Application Load Balancer URL...${NC}"
sleep 10  # Wait for ALB to be created
ALB_URL=$(kubectl get ingress loan-underwriting-ingress -n insurance-claims \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

if [ -n "$ALB_URL" ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}Application URL:${NC} http://${ALB_URL}/loan"
    echo -e "${YELLOW}Applicant Portal:${NC} http://${ALB_URL}/applicant"
    echo -e "${YELLOW}Loan Officer Portal:${NC} http://${ALB_URL}/officer"
    echo -e "${YELLOW}Risk Manager Portal:${NC} http://${ALB_URL}/risk"
    echo -e "${YELLOW}Executive Portal:${NC} http://${ALB_URL}/executive"
else
    echo -e "${YELLOW}ALB URL not yet available. Run this command to get it:${NC}"
    echo "kubectl get ingress loan-underwriting-ingress -n insurance-claims -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  View logs: kubectl logs -n insurance-claims -l app=loan-underwriting -f"
echo -e "  Check status: kubectl get pods -n insurance-claims -l app=loan-underwriting"
echo -e "  Restart: kubectl rollout restart deployment/loan-underwriting -n insurance-claims"
echo -e "${GREEN}========================================${NC}"
