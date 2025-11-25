#!/bin/bash
#
# Full Deployment Script for Loan Underwriting System
# Builds Docker image, pushes to ECR, and deploys to EKS
#

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Loan Underwriting System - Full Deployment${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Step 1: Build and push Docker image
echo -e "${GREEN}Step 1: Building and pushing Docker image...${NC}"
bash "${SCRIPT_DIR}/build-and-push.sh"
echo ""

# Step 2: Deploy to Kubernetes
echo -e "${GREEN}Step 2: Deploying to Kubernetes...${NC}"
bash "${SCRIPT_DIR}/deploy.sh"
echo ""

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Full Deployment Complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Access the application via the ALB URL shown above"
echo -e "  2. Generate sample data: python src/data_generator.py --count 50"
echo -e "  3. Monitor logs: kubectl logs -n insurance-claims -l app=loan-underwriting -f"
echo ""
