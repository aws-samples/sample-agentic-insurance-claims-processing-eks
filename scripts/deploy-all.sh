#!/bin/bash
###############################################################
# Complete Automated Deployment Script
# Deploys infrastructure, configures Kubernetes, and validates
###############################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform"
K8S_DIR="$PROJECT_ROOT/infrastructure/kubernetes"
OUTPUT_FILE="$PROJECT_ROOT/deployment-outputs.env"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Complete Automated Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}→ Checking prerequisites...${NC}"

    local missing_tools=()
    for tool in terraform aws kubectl jq; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo -e "${RED}✗ Missing tools: ${missing_tools[*]}${NC}"
        exit 1
    fi

    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}✗ AWS credentials not configured${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ All prerequisites met${NC}"
    echo ""
}

# Deploy Terraform infrastructure
deploy_terraform() {
    echo -e "${YELLOW}→ Deploying Terraform infrastructure...${NC}"

    cd "$TERRAFORM_DIR"

    if [ ! -f "terraform.tfvars" ]; then
        echo -e "${YELLOW}⚠ Creating terraform.tfvars template${NC}"
        cat > terraform.tfvars << EOF
region = "us-west-2"
environment = "production"
project_name = "insurance-claims"

create_acm_certificate = false  # Set to true for production with custom domain
domain_name = ""
route53_zone_id = ""

enable_cloudwatch_metrics = true
enable_fluentbit_logging = true
enable_prometheus_grafana = false
enable_nvidia_device_plugin = true
enable_s3_bucket = true
EOF
        echo -e "${YELLOW}  Please edit terraform.tfvars and run again${NC}"
        exit 0
    fi

    terraform init -upgrade
    terraform plan -out=tfplan

    echo ""
    read -p "Proceed with Terraform apply? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 0
    fi

    terraform apply tfplan
    echo -e "${GREEN}✓ Infrastructure deployed${NC}"
    echo ""
}

# Capture outputs
capture_outputs() {
    echo -e "${YELLOW}→ Capturing Terraform outputs...${NC}"

    cd "$TERRAFORM_DIR"

    AWS_REGION=$(terraform output -raw region 2>/dev/null || echo "us-west-2")
    EKS_CLUSTER=$(terraform output -raw cluster_name 2>/dev/null || echo "")
    ACM_CERT=$(terraform output -raw acm_certificate_arn 2>/dev/null || echo "")

    cat > "$OUTPUT_FILE" << EOF
export AWS_REGION='$AWS_REGION'
export EKS_CLUSTER_NAME='$EKS_CLUSTER'
export ACM_CERTIFICATE_ARN='$ACM_CERT'
EOF

    echo -e "${GREEN}✓ Outputs captured${NC}"
    echo "  Cluster: $EKS_CLUSTER"
    echo "  Region: $AWS_REGION"
    echo "  ACM Cert: ${ACM_CERT:-'None'}"
    echo ""
}

# Configure kubectl
configure_kubectl() {
    echo -e "${YELLOW}→ Configuring kubectl...${NC}"

    source "$OUTPUT_FILE"

    aws eks update-kubeconfig --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION"

    # Wait for cluster
    echo -e "${YELLOW}→ Waiting for cluster...${NC}"
    for i in {1..30}; do
        if kubectl get nodes &> /dev/null; then
            echo -e "${GREEN}✓ Cluster ready${NC}"
            break
        fi
        sleep 10
    done

    kubectl get nodes
    echo ""
}

# Update Kubernetes manifests with outputs
update_k8s_manifests() {
    echo -e "${YELLOW}→ Updating Kubernetes manifests...${NC}"

    source "$OUTPUT_FILE"

    # Update ingress with ACM certificate ARN if available
    if [ -n "$ACM_CERTIFICATE_ARN" ] && [ "$ACM_CERTIFICATE_ARN" != "No certificate created - set create_acm_certificate=true" ]; then
        echo -e "${YELLOW}  Injecting ACM certificate ARN into ingress...${NC}"
        sed -i.bak "s|<ACM_CERTIFICATE_ARN>|$ACM_CERTIFICATE_ARN|g" \
            "$K8S_DIR/insurance-claims-ingress.yaml"
        echo -e "${GREEN}✓ Ingress updated with certificate${NC}"
    else
        echo -e "${YELLOW}⚠ No ACM certificate - using ALB default cert${NC}"
        # Remove certificate annotation if no cert
        sed -i.bak '/certificate-arn:/d' \
            "$K8S_DIR/insurance-claims-ingress.yaml"
    fi

    echo ""
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    echo -e "${YELLOW}→ Deploying Kubernetes resources...${NC}"

    # Deploy in order
    kubectl apply -f "$K8S_DIR/external-secrets.yaml"
    sleep 5

    # Wait for External Secrets Operator
    echo -e "${YELLOW}  Waiting for External Secrets...${NC}"
    kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=external-secrets \
        -n external-secrets --timeout=120s || true

    # Deploy secrets
    echo -e "${YELLOW}  Creating ExternalSecrets...${NC}"
    kubectl apply -f "$K8S_DIR/external-secrets.yaml"
    sleep 10

    # Verify secrets synced
    kubectl get externalsecrets -n insurance-claims

    # Deploy applications
    kubectl apply -f "$K8S_DIR/mongodb-deployment.yaml"
    kubectl apply -f "$K8S_DIR/redis-deployment.yaml"
    kubectl apply -f "$K8S_DIR/ollama-deployment.yaml"
    kubectl apply -f "$K8S_DIR/shared-memory.yaml"
    kubectl apply -f "$K8S_DIR/coordinator.yaml"
    kubectl apply -f "$K8S_DIR/policy-agent.yaml"
    kubectl apply -f "$K8S_DIR/external-integrations.yaml"
    kubectl apply -f "$K8S_DIR/claims-web-interface.yaml"
    kubectl apply -f "$K8S_DIR/claims-simulator.yaml"
    kubectl apply -f "$K8S_DIR/insurance-claims-ingress.yaml"

    echo -e "${GREEN}✓ Kubernetes resources deployed${NC}"
    echo ""
}

# Validate deployment
validate_deployment() {
    echo -e "${YELLOW}→ Validating deployment...${NC}"

    # Check pods
    echo -e "${BLUE}Pods status:${NC}"
    kubectl get pods -n insurance-claims

    # Check ingress
    echo ""
    echo -e "${BLUE}Ingress:${NC}"
    kubectl get ingress -n insurance-claims

    # Get ALB DNS
    ALB_DNS=$(kubectl get ingress insurance-claims-ingress -n insurance-claims \
        -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

    echo ""
    if [ -n "$ALB_DNS" ]; then
        echo -e "${GREEN}✓ ALB DNS: $ALB_DNS${NC}"
        echo -e "${BLUE}Access your application at:${NC}"
        echo -e "  http://$ALB_DNS (will redirect to HTTPS)"
        echo -e "  https://$ALB_DNS"
    else
        echo -e "${YELLOW}⚠ ALB not yet ready, check status in a few minutes${NC}"
    fi

    echo ""
}

# Main execution
main() {
    check_prerequisites
    deploy_terraform
    capture_outputs
    configure_kubectl
    update_k8s_manifests
    deploy_kubernetes
    validate_deployment

    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Deployment Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  • Monitor pods: ${YELLOW}kubectl get pods -n insurance-claims -w${NC}"
    echo -e "  • View logs: ${YELLOW}kubectl logs -f <pod-name> -n insurance-claims${NC}"
    echo -e "  • Check ingress: ${YELLOW}kubectl get ingress -n insurance-claims${NC}"
    echo ""
}

main "$@"
