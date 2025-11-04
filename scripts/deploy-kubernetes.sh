#!/bin/bash

# Kubernetes Deployment Script for Insurance Agentic AI Demo
# Deploys all applications and services to EKS cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
ECR_REGISTRY="${ECR_REGISTRY:-123255318457.dkr.ecr.us-west-2.amazonaws.com}"
IMAGE_TAG="${IMAGE_TAG:-v1}"
NAMESPACE="${NAMESPACE:-insurance-claims}"
CLUSTER_NAME="${CLUSTER_NAME:-agentic-eks-cluster}"
AWS_REGION="${AWS_REGION:-us-west-2}"
MANIFESTS_DIR="./infrastructure/kubernetes"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-300}"
DRY_RUN="${DRY_RUN:-false}"

# Deployment order for services (dependencies matter!)
# Storage and foundational services first, then agents, then interfaces
DEPLOYMENT_ORDER=(
    "namespace"
    "mongodb-deployment"
    "redis-deployment"
    "ollama-deployment"
    "shared-memory"
    "coordinator"
    "policy-agent"
    "external-integrations"
    "claims-web-interface"
    "claims-simulator"
    "insurance-claims-ingress"
)

# Optional GPU deployments
GPU_DEPLOYMENTS=(
    "ollama-qwen"
)

# Function to print section headers
print_section() {
    echo ""
    echo -e "${PURPLE}▶ $1${NC}"
    echo "=============================================="
}

# Function to print usage
usage() {
    echo -e "${BLUE}Kubernetes Deployment Script for Insurance Agentic AI Demo${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy       - Deploy all applications"
    echo "  upgrade      - Upgrade existing deployment"
    echo "  rollback     - Rollback to previous version"
    echo "  status       - Check deployment status"
    echo "  logs         - Show application logs"
    echo "  scale        - Scale applications"
    echo "  restart      - Restart deployments"
    echo "  port-forward - Port forward to services"
    echo "  shell        - Get shell access to pod"
    echo ""
    echo "Options:"
    echo "  --dry-run           - Show what would be deployed"
    echo "  --tag=TAG           - Use specific image tag"
    echo "  --namespace=NS      - Deploy to specific namespace"
    echo "  --include-gpu       - Include GPU-enabled deployments"
    echo "  --wait              - Wait for rollout completion"
    echo "  --timeout=SECONDS   - Wait timeout (default: 300)"
    echo ""
    echo "Environment Variables:"
    echo "  ECR_REGISTRY       - ECR registry URL"
    echo "  IMAGE_TAG         - Docker image tag (default: latest)"
    echo "  NAMESPACE         - Kubernetes namespace (default: insurance-claims)"
    echo "  CLUSTER_NAME      - EKS cluster name"
    echo "  AWS_REGION        - AWS region"
    echo ""
    echo "Examples:"
    echo "  $0 deploy                         # Deploy all applications"
    echo "  $0 deploy --include-gpu --wait    # Deploy with GPU and wait"
    echo "  $0 status                         # Check deployment status"
    echo "  $0 logs coordinator               # Show coordinator logs"
    echo "  $0 scale web-interface 3          # Scale web interface to 3 replicas"
}

# Function to check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"

    local errors=0

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl not found${NC}"
        echo "   Install from: https://kubernetes.io/docs/tasks/tools/"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ kubectl found${NC}"
    fi

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}❌ Not connected to Kubernetes cluster${NC}"
        echo "   Run: aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME"
        errors=$((errors + 1))
    else
        local cluster_url=$(kubectl cluster-info | grep "Kubernetes control plane" | awk '{print $NF}')
        echo -e "${GREEN}✅ Connected to cluster: ${cluster_url}${NC}"
    fi

    # Check manifests directory
    if [ ! -d "$MANIFESTS_DIR" ]; then
        echo -e "${RED}❌ Manifests directory not found: $MANIFESTS_DIR${NC}"
        errors=$((errors + 1))
    else
        local manifest_count=$(find "$MANIFESTS_DIR" -name "*.yaml" -o -name "*.yml" | wc -l)
        echo -e "${GREEN}✅ Found ${manifest_count} manifest files${NC}"
    fi

    # Check node availability
    local node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
    if [ "$node_count" -eq 0 ]; then
        echo -e "${RED}❌ No nodes available in cluster${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ ${node_count} nodes available${NC}"
    fi

    if [ $errors -gt 0 ]; then
        echo -e "${RED}❌ Prerequisites check failed. Please fix the issues above.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All prerequisites satisfied${NC}"
}

# Function to substitute environment variables in manifests
substitute_variables() {
    local manifest_file="$1"
    local temp_file=$(mktemp)

    # Substitute variables
    envsubst < "$manifest_file" > "$temp_file"

    # Additional substitutions for our specific variables
    sed -i.bak \
        -e "s|\${ECR_REGISTRY}|${ECR_REGISTRY}|g" \
        -e "s|\${IMAGE_TAG}|${IMAGE_TAG}|g" \
        -e "s|\${NAMESPACE}|${NAMESPACE}|g" \
        "$temp_file"

    echo "$temp_file"
}

# Function to deploy namespace
deploy_namespace() {
    print_section "Creating Namespace"

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${CYAN}DRY RUN: Would create namespace ${NAMESPACE}${NC}"
        return
    fi

    # Create namespace if it doesn't exist
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        kubectl create namespace "$NAMESPACE"
        echo -e "${GREEN}✅ Created namespace: ${NAMESPACE}${NC}"
    else
        echo -e "${YELLOW}⚠️  Namespace ${NAMESPACE} already exists${NC}"
    fi

    # Label namespace for monitoring
    kubectl label namespace "$NAMESPACE" app=insurance-claims --overwrite
    kubectl label namespace "$NAMESPACE" environment=demo --overwrite
}

# Function to deploy a single manifest
deploy_manifest() {
    local manifest_name="$1"
    local manifest_file=""

    # Find the manifest file
    for ext in yaml yml; do
        local potential_file="${MANIFESTS_DIR}/${manifest_name}.${ext}"
        if [ -f "$potential_file" ]; then
            manifest_file="$potential_file"
            break
        fi
    done

    # Try alternative naming patterns
    if [ -z "$manifest_file" ]; then
        for pattern in "${manifest_name}-deployment" "${manifest_name}-service" "claims-${manifest_name}"; do
            for ext in yaml yml; do
                local potential_file="${MANIFESTS_DIR}/${pattern}.${ext}"
                if [ -f "$potential_file" ]; then
                    manifest_file="$potential_file"
                    break 2
                fi
            done
        done
    fi

    if [ -z "$manifest_file" ]; then
        echo -e "${YELLOW}⚠️  Manifest not found for: ${manifest_name}${NC}"
        return
    fi

    echo -e "${CYAN}Deploying ${manifest_name}...${NC}"

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${CYAN}DRY RUN: Would apply ${manifest_file}${NC}"
        local processed_file=$(substitute_variables "$manifest_file")
        kubectl apply --dry-run=client -f "$processed_file" -n "$NAMESPACE"
        rm -f "$processed_file" "${processed_file}.bak"
        return
    fi

    # Process and apply manifest
    local processed_file=$(substitute_variables "$manifest_file")

    kubectl apply -f "$processed_file" -n "$NAMESPACE"

    # Clean up temporary file
    rm -f "$processed_file" "${processed_file}.bak"

    echo -e "${GREEN}✅ Deployed ${manifest_name}${NC}"
}

# Function to wait for deployment rollout
wait_for_rollout() {
    local deployment_name="$1"

    if [ "$WAIT_ROLLOUT" = "true" ]; then
        echo -e "${CYAN}Waiting for ${deployment_name} rollout...${NC}"
        kubectl rollout status deployment/"$deployment_name" -n "$NAMESPACE" --timeout="${WAIT_TIMEOUT}s"
    fi
}

# Function to deploy all applications
deploy_all() {
    print_section "Deploying Insurance Claims Processing System"

    echo -e "${CYAN}Registry: ${ECR_REGISTRY}${NC}"
    echo -e "${CYAN}Image Tag: ${IMAGE_TAG}${NC}"
    echo -e "${CYAN}Namespace: ${NAMESPACE}${NC}"
    echo -e "${CYAN}Dry Run: ${DRY_RUN}${NC}"
    echo ""

    # Deploy in order
    for component in "${DEPLOYMENT_ORDER[@]}"; do
        case "$component" in
            "namespace")
                deploy_namespace
                ;;
            *)
                deploy_manifest "$component"

                # Wait for rollout only for deployments (not services or ingress)
                if [[ "$component" != *"-ingress"* ]]; then
                    wait_for_rollout "$component"
                fi
                ;;
        esac

        # Add delay between deployments for dependencies
        if [[ "$component" =~ mongodb|redis|ollama ]] && [ "$DRY_RUN" != "true" ]; then
            echo -e "${CYAN}Waiting for ${component} to be ready...${NC}"
            sleep 10
        fi
    done

    # Deploy GPU components if requested
    if [ "$INCLUDE_GPU" = "true" ]; then
        print_section "Deploying GPU-Enabled Components"
        for gpu_component in "${GPU_DEPLOYMENTS[@]}"; do
            deploy_manifest "$gpu_component"
            wait_for_rollout "$gpu_component"
        done
    fi

    if [ "$DRY_RUN" != "true" ]; then
        print_section "Deployment Summary"
        kubectl get all -n "$NAMESPACE"
    fi

    echo -e "${GREEN}✅ Deployment completed successfully${NC}"
}

# Function to check deployment status
check_status() {
    print_section "Deployment Status"

    echo -e "${CYAN}Namespace: ${NAMESPACE}${NC}"
    echo ""

    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        echo -e "${RED}❌ Namespace ${NAMESPACE} not found${NC}"
        return 1
    fi

    # Check deployments
    echo -e "${CYAN}Deployments:${NC}"
    kubectl get deployments -n "$NAMESPACE" -o wide

    echo ""
    echo -e "${CYAN}Services:${NC}"
    kubectl get services -n "$NAMESPACE" -o wide

    echo ""
    echo -e "${CYAN}Pods:${NC}"
    kubectl get pods -n "$NAMESPACE" -o wide

    echo ""
    echo -e "${CYAN}Ingress:${NC}"
    kubectl get ingress -n "$NAMESPACE" -o wide || echo "No ingress found"

    # Check for any issues
    echo ""
    echo -e "${CYAN}Pod Issues:${NC}"
    local problem_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    if [ "$problem_pods" -gt 0 ]; then
        echo -e "${RED}❌ ${problem_pods} pods not running${NC}"
        kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running
    else
        echo -e "${GREEN}✅ All pods running${NC}"
    fi

    # Check resource usage
    echo ""
    echo -e "${CYAN}Resource Usage:${NC}"
    kubectl top pods -n "$NAMESPACE" 2>/dev/null || echo "Metrics server not available"
}

# Function to show logs
show_logs() {
    local service_name="$1"
    local follow="${2:-false}"

    if [ -z "$service_name" ]; then
        echo -e "${RED}❌ Service name required${NC}"
        echo "Available services:"
        kubectl get deployments -n "$NAMESPACE" -o name | sed 's/deployment.apps\///'
        return 1
    fi

    print_section "Logs for ${service_name}"

    local follow_flag=""
    if [ "$follow" = "true" ]; then
        follow_flag="-f"
    fi

    # Get pod name
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l app="$service_name" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$pod_name" ]; then
        echo -e "${RED}❌ No pod found for service: ${service_name}${NC}"
        return 1
    fi

    echo -e "${CYAN}Pod: ${pod_name}${NC}"
    kubectl logs $follow_flag "$pod_name" -n "$NAMESPACE"
}

# Function to scale deployment
scale_deployment() {
    local deployment_name="$1"
    local replicas="$2"

    if [ -z "$deployment_name" ] || [ -z "$replicas" ]; then
        echo -e "${RED}❌ Deployment name and replica count required${NC}"
        echo "Usage: $0 scale DEPLOYMENT REPLICAS"
        return 1
    fi

    print_section "Scaling ${deployment_name} to ${replicas} replicas"

    kubectl scale deployment "$deployment_name" --replicas="$replicas" -n "$NAMESPACE"
    kubectl rollout status deployment/"$deployment_name" -n "$NAMESPACE"

    echo -e "${GREEN}✅ Scaled ${deployment_name} to ${replicas} replicas${NC}"
}

# Function to restart deployments
restart_deployments() {
    print_section "Restarting Deployments"

    local deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}')

    for deployment in $deployments; do
        echo -e "${CYAN}Restarting ${deployment}...${NC}"
        kubectl rollout restart deployment/"$deployment" -n "$NAMESPACE"
    done

    echo -e "${GREEN}✅ All deployments restarted${NC}"
}

# Function to port forward services
port_forward() {
    local service_name="$1"
    local local_port="${2:-8080}"

    if [ -z "$service_name" ]; then
        echo -e "${RED}❌ Service name required${NC}"
        echo "Available services:"
        kubectl get services -n "$NAMESPACE" -o name | sed 's/service\///'
        return 1
    fi

    print_section "Port Forwarding ${service_name}"

    # Get service port
    local service_port=$(kubectl get service "$service_name" -n "$NAMESPACE" -o jsonpath='{.spec.ports[0].port}' 2>/dev/null)

    if [ -z "$service_port" ]; then
        echo -e "${RED}❌ Service not found: ${service_name}${NC}"
        return 1
    fi

    echo -e "${CYAN}Forwarding local port ${local_port} to ${service_name}:${service_port}${NC}"
    echo -e "${YELLOW}Access the service at: http://localhost:${local_port}${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"

    kubectl port-forward service/"$service_name" "$local_port":"$service_port" -n "$NAMESPACE"
}

# Function to get shell access
get_shell() {
    local service_name="$1"

    if [ -z "$service_name" ]; then
        echo -e "${RED}❌ Service name required${NC}"
        echo "Available services:"
        kubectl get deployments -n "$NAMESPACE" -o name | sed 's/deployment.apps\///'
        return 1
    fi

    # Get pod name
    local pod_name=$(kubectl get pods -n "$NAMESPACE" -l app="$service_name" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [ -z "$pod_name" ]; then
        echo -e "${RED}❌ No pod found for service: ${service_name}${NC}"
        return 1
    fi

    print_section "Shell Access to ${service_name}"
    echo -e "${CYAN}Pod: ${pod_name}${NC}"

    kubectl exec -it "$pod_name" -n "$NAMESPACE" -- /bin/bash || \
    kubectl exec -it "$pod_name" -n "$NAMESPACE" -- /bin/sh
}

# Function to rollback deployment
rollback_deployment() {
    local deployment_name="$1"

    if [ -z "$deployment_name" ]; then
        echo "Available deployments:"
        kubectl get deployments -n "$NAMESPACE" -o name | sed 's/deployment.apps\///'
        read -p "Enter deployment name: " deployment_name
    fi

    print_section "Rolling Back ${deployment_name}"

    # Show rollout history
    echo -e "${CYAN}Rollout history:${NC}"
    kubectl rollout history deployment/"$deployment_name" -n "$NAMESPACE"

    # Rollback
    kubectl rollout undo deployment/"$deployment_name" -n "$NAMESPACE"
    kubectl rollout status deployment/"$deployment_name" -n "$NAMESPACE"

    echo -e "${GREEN}✅ Rollback completed${NC}"
}

# Main script logic
main() {
    echo -e "${BLUE}☸️  Kubernetes Deployment for Insurance Agentic AI Demo${NC}"
    echo "==========================================================="
    echo -e "${CYAN}Cluster: ${CLUSTER_NAME}${NC}"
    echo -e "${CYAN}Namespace: ${NAMESPACE}${NC}"
    echo -e "${CYAN}Registry: ${ECR_REGISTRY}${NC}"
    echo -e "${CYAN}Tag: ${IMAGE_TAG}${NC}"
    echo ""

    # Parse command line arguments
    INCLUDE_GPU="false"
    WAIT_ROLLOUT="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --include-gpu)
                INCLUDE_GPU="true"
                shift
                ;;
            --wait)
                WAIT_ROLLOUT="true"
                shift
                ;;
            --timeout=*)
                WAIT_TIMEOUT="${1#*=}"
                shift
                ;;
            --tag=*)
                IMAGE_TAG="${1#*=}"
                shift
                ;;
            --namespace=*)
                NAMESPACE="${1#*=}"
                shift
                ;;
            *)
                if [ -z "$COMMAND" ]; then
                    COMMAND="$1"
                else
                    ARGS+=("$1")
                fi
                shift
                ;;
        esac
    done

    # Check prerequisites for deployment commands
    if [[ "$COMMAND" =~ ^(deploy|upgrade|status|logs|scale|restart|port-forward|shell|rollback)$ ]]; then
        check_prerequisites
    fi

    # Execute command
    case "$COMMAND" in
        deploy|upgrade)
            deploy_all
            ;;
        status)
            check_status
            ;;
        logs)
            local follow_logs="false"
            if [ "${ARGS[1]}" = "--follow" ] || [ "${ARGS[1]}" = "-f" ]; then
                follow_logs="true"
            fi
            show_logs "${ARGS[0]}" "$follow_logs"
            ;;
        scale)
            scale_deployment "${ARGS[0]}" "${ARGS[1]}"
            ;;
        restart)
            restart_deployments
            ;;
        port-forward)
            port_forward "${ARGS[0]}" "${ARGS[1]}"
            ;;
        shell)
            get_shell "${ARGS[0]}"
            ;;
        rollback)
            rollback_deployment "${ARGS[0]}"
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    ARGS=()
    main "$@"
fi