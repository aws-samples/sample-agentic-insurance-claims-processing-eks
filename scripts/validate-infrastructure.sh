#!/bin/bash

###############################################################
# Infrastructure Validation Script
# Validates that all infrastructure components are working
###############################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/infrastructure/terraform"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

###############################################################
# Validation Functions
###############################################################

check_aws_connectivity() {
    log_info "Checking AWS connectivity..."

    if aws sts get-caller-identity &> /dev/null; then
        local account=$(aws sts get-caller-identity --query Account --output text)
        local region=$(aws configure get region)
        log_success "Connected to AWS account: ${account} (${region})"
        return 0
    else
        log_error "Cannot connect to AWS"
        return 1
    fi
}

check_terraform_state() {
    log_info "Checking Terraform state..."

    cd "${TERRAFORM_DIR}"

    if [ ! -f "terraform.tfstate" ]; then
        log_error "No terraform.tfstate found. Infrastructure not deployed yet."
        echo "Run: ./scripts/deploy-infrastructure.sh deploy"
        return 1
    fi

    log_success "Terraform state exists"
    return 0
}

check_eks_cluster() {
    log_info "Checking EKS cluster..."

    cd "${TERRAFORM_DIR}"
    local cluster_name=$(terraform output -raw cluster_name 2>/dev/null || echo "")

    if [ -z "$cluster_name" ]; then
        log_error "Cannot get cluster name from Terraform"
        return 1
    fi

    local region=$(terraform output -raw region 2>/dev/null)

    if aws eks describe-cluster --name "$cluster_name" --region "$region" &> /dev/null; then
        local status=$(aws eks describe-cluster --name "$cluster_name" --region "$region" --query 'cluster.status' --output text)
        if [ "$status" = "ACTIVE" ]; then
            log_success "EKS cluster '${cluster_name}' is ACTIVE"
            return 0
        else
            log_warning "EKS cluster status: ${status}"
            return 1
        fi
    else
        log_error "EKS cluster '${cluster_name}' not found"
        return 1
    fi
}

check_kubectl_access() {
    log_info "Checking kubectl access..."

    if kubectl cluster-info &> /dev/null; then
        log_success "kubectl can access cluster"

        local context=$(kubectl config current-context)
        log_info "Current context: ${context}"
        return 0
    else
        log_error "kubectl cannot access cluster"
        echo "Run: aws eks update-kubeconfig --name <cluster-name> --region <region>"
        return 1
    fi
}

check_cluster_nodes() {
    log_info "Checking cluster nodes..."

    local ready_nodes=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready " || echo "0")
    local total_nodes=$(kubectl get nodes --no-headers 2>/dev/null | wc -l || echo "0")

    if [ "$ready_nodes" -gt 0 ]; then
        log_success "Nodes: ${ready_nodes}/${total_nodes} Ready"
        kubectl get nodes
        return 0
    else
        log_error "No ready nodes found"
        return 1
    fi
}

check_core_addons() {
    log_info "Checking core Kubernetes addons..."

    local all_ok=true

    # Check CoreDNS
    if kubectl get deployment coredns -n kube-system &> /dev/null; then
        if kubectl get deployment coredns -n kube-system -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' | grep -q "True"; then
            log_success "CoreDNS is running"
        else
            log_warning "CoreDNS is not ready"
            all_ok=false
        fi
    else
        log_error "CoreDNS not found"
        all_ok=false
    fi

    # Check VPC CNI
    if kubectl get daemonset aws-node -n kube-system &> /dev/null; then
        local desired=$(kubectl get daemonset aws-node -n kube-system -o jsonpath='{.status.desiredNumberScheduled}')
        local ready=$(kubectl get daemonset aws-node -n kube-system -o jsonpath='{.status.numberReady}')
        if [ "$desired" = "$ready" ]; then
            log_success "VPC CNI is running (${ready}/${desired} pods)"
        else
            log_warning "VPC CNI: ${ready}/${desired} pods ready"
            all_ok=false
        fi
    else
        log_error "VPC CNI not found"
        all_ok=false
    fi

    # Check kube-proxy
    if kubectl get daemonset kube-proxy -n kube-system &> /dev/null; then
        local desired=$(kubectl get daemonset kube-proxy -n kube-system -o jsonpath='{.status.desiredNumberScheduled}')
        local ready=$(kubectl get daemonset kube-proxy -n kube-system -o jsonpath='{.status.numberReady}')
        if [ "$desired" = "$ready" ]; then
            log_success "kube-proxy is running (${ready}/${desired} pods)"
        else
            log_warning "kube-proxy: ${ready}/${desired} pods ready"
            all_ok=false
        fi
    else
        log_error "kube-proxy not found"
        all_ok=false
    fi

    [ "$all_ok" = true ] && return 0 || return 1
}

check_alb_controller() {
    log_info "Checking AWS Load Balancer Controller..."

    if kubectl get deployment aws-load-balancer-controller -n kube-system &> /dev/null; then
        if kubectl get deployment aws-load-balancer-controller -n kube-system -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' | grep -q "True"; then
            log_success "AWS Load Balancer Controller is running"

            local replicas=$(kubectl get deployment aws-load-balancer-controller -n kube-system -o jsonpath='{.status.readyReplicas}')
            log_info "Ready replicas: ${replicas}"
            return 0
        else
            log_warning "AWS Load Balancer Controller is not ready"
            kubectl get deployment aws-load-balancer-controller -n kube-system
            return 1
        fi
    else
        log_error "AWS Load Balancer Controller not found"
        echo "This is required for ALB ingress to work!"
        return 1
    fi
}

check_karpenter() {
    log_info "Checking Karpenter..."

    if kubectl get deployment karpenter -n kube-system &> /dev/null; then
        if kubectl get deployment karpenter -n kube-system -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' | grep -q "True"; then
            log_success "Karpenter is running"

            # Check if NodePools exist
            local nodepools=$(kubectl get nodepools --no-headers 2>/dev/null | wc -l || echo "0")
            if [ "$nodepools" -gt 0 ]; then
                log_success "NodePools configured: ${nodepools}"
                kubectl get nodepools
            else
                log_warning "No NodePools found - nodes won't autoscale"
            fi
            return 0
        else
            log_warning "Karpenter is not ready"
            return 1
        fi
    else
        log_error "Karpenter not found"
        return 1
    fi
}

check_ebs_csi_driver() {
    log_info "Checking EBS CSI Driver..."

    if kubectl get deployment ebs-csi-controller -n kube-system &> /dev/null; then
        if kubectl get deployment ebs-csi-controller -n kube-system -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' | grep -q "True"; then
            log_success "EBS CSI Driver is running"
            return 0
        else
            log_warning "EBS CSI Driver is not ready"
            return 1
        fi
    else
        log_warning "EBS CSI Driver not found (optional)"
        return 0
    fi
}

check_vpc_config() {
    log_info "Checking VPC configuration..."

    cd "${TERRAFORM_DIR}"

    local vpc_id=$(terraform output -raw vpc_id 2>/dev/null || echo "")
    if [ -z "$vpc_id" ]; then
        log_error "Cannot get VPC ID"
        return 1
    fi

    local region=$(terraform output -raw region 2>/dev/null)

    # Check VPC exists
    if aws ec2 describe-vpcs --vpc-ids "$vpc_id" --region "$region" &> /dev/null; then
        log_success "VPC exists: ${vpc_id}"

        # Check subnets
        local private_subnets=$(terraform output -json private_subnets 2>/dev/null | jq -r '.[]' | wc -l || echo "0")
        local public_subnets=$(terraform output -json public_subnets 2>/dev/null | jq -r '.[]' | wc -l || echo "0")

        log_success "Private subnets: ${private_subnets}"
        log_success "Public subnets: ${public_subnets}"

        return 0
    else
        log_error "VPC not found: ${vpc_id}"
        return 1
    fi
}

check_s3_bucket() {
    log_info "Checking S3 bucket..."

    cd "${TERRAFORM_DIR}"

    local bucket_name=$(terraform output -raw s3_bucket_name 2>/dev/null || echo "")
    if [ -z "$bucket_name" ]; then
        log_warning "S3 bucket not configured (optional)"
        return 0
    fi

    if aws s3 ls "s3://${bucket_name}" &> /dev/null; then
        log_success "S3 bucket exists: ${bucket_name}"
        return 0
    else
        log_error "S3 bucket not found: ${bucket_name}"
        return 1
    fi
}

###############################################################
# Main Validation
###############################################################

main() {
    echo ""
    echo "=========================================="
    echo "Infrastructure Validation Report"
    echo "=========================================="
    echo ""

    local total_checks=0
    local passed_checks=0
    local failed_checks=0

    run_check() {
        total_checks=$((total_checks + 1))
        if "$@"; then
            passed_checks=$((passed_checks + 1))
        else
            failed_checks=$((failed_checks + 1))
        fi
        echo ""
    }

    # Run all checks
    run_check check_aws_connectivity
    run_check check_terraform_state
    run_check check_eks_cluster
    run_check check_kubectl_access
    run_check check_cluster_nodes
    run_check check_core_addons
    run_check check_alb_controller
    run_check check_karpenter
    run_check check_ebs_csi_driver
    run_check check_vpc_config
    run_check check_s3_bucket

    # Summary
    echo "=========================================="
    echo "Summary"
    echo "=========================================="
    echo "Total checks: ${total_checks}"
    echo -e "${GREEN}Passed: ${passed_checks}${NC}"
    if [ "$failed_checks" -gt 0 ]; then
        echo -e "${RED}Failed: ${failed_checks}${NC}"
    else
        echo -e "${GREEN}Failed: ${failed_checks}${NC}"
    fi
    echo ""

    if [ "$failed_checks" -eq 0 ]; then
        log_success "All infrastructure components are healthy!"
        echo ""
        echo "You can now deploy your application:"
        echo "  ./scripts/build-docker-images.sh build"
        echo "  ./scripts/build-docker-images.sh push"
        echo "  ./scripts/deploy-kubernetes.sh deploy"
        exit 0
    else
        log_error "Some infrastructure components have issues"
        echo ""
        echo "Review the errors above and fix them before deploying applications."
        exit 1
    fi
}

main "$@"
