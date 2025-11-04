#!/bin/bash

# Docker Image Build Script for Insurance Agentic AI Demo
# Builds all required Docker images and pushes to ECR

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
AWS_REGION="${AWS_REGION:-us-west-2}"
BUILD_CONTEXT="./applications/insurance-claims-processing"
PUSH_IMAGES="${PUSH_IMAGES:-true}"
PARALLEL_BUILDS="${PARALLEL_BUILDS:-true}"

# Image definitions - ALL microservices (compatible with bash 3.2)
IMAGES=(
    "coordinator:docker/Dockerfile.coordinator"
    "web-interface:docker/Dockerfile.web-interface"
    "shared-memory:docker/Dockerfile.shared-memory"
    "policy-agent:docker/Dockerfile.policy-agent"
    "external-integrations:docker/Dockerfile.external-integrations"
    "claims-simulator:docker/Dockerfile.claims-simulator"
    "fraud-agent:docker/Dockerfile.fraud-agent"
    "investigation-agent:docker/Dockerfile.investigation-agent"
    "human-workflow:docker/Dockerfile.human-workflow"
    "analytics:docker/Dockerfile.analytics"
    "demo-generator:docker/Dockerfile.demo-generator"
    "langgraph:docker/Dockerfile.langgraph"
)

# GPU-enabled images (for Ollama/Qwen)
GPU_IMAGES=(
    "ollama-qwen:docker/Dockerfile.ollama"
)

# Helper functions for array manipulation (bash 3.2 compatible)
get_dockerfile_for_image() {
    local image_name="$1"
    local array_name="$2"

    if [ "$array_name" = "IMAGES" ]; then
        for item in "${IMAGES[@]}"; do
            if [[ "$item" == "$image_name:"* ]]; then
                echo "${item#*:}"
                return 0
            fi
        done
    elif [ "$array_name" = "GPU_IMAGES" ]; then
        for item in "${GPU_IMAGES[@]}"; do
            if [[ "$item" == "$image_name:"* ]]; then
                echo "${item#*:}"
                return 0
            fi
        done
    fi
    return 1
}

get_image_names() {
    local array_name="$1"
    local names=()

    if [ "$array_name" = "IMAGES" ]; then
        for item in "${IMAGES[@]}"; do
            names+=("${item%%:*}")
        done
    elif [ "$array_name" = "GPU_IMAGES" ]; then
        for item in "${GPU_IMAGES[@]}"; do
            names+=("${item%%:*}")
        done
    fi

    echo "${names[@]}"
}

image_exists() {
    local image_name="$1"
    local array_name="$2"

    if [ "$array_name" = "IMAGES" ]; then
        for item in "${IMAGES[@]}"; do
            if [[ "$item" == "$image_name:"* ]]; then
                return 0
            fi
        done
    elif [ "$array_name" = "GPU_IMAGES" ]; then
        for item in "${GPU_IMAGES[@]}"; do
            if [[ "$item" == "$image_name:"* ]]; then
                return 0
            fi
        done
    fi
    return 1
}

# Function to print section headers
print_section() {
    echo ""
    echo -e "${PURPLE}▶ $1${NC}"
    echo "=============================================="
}

# Function to print usage
usage() {
    echo -e "${BLUE}Docker Image Build Script for Insurance Agentic AI Demo${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build        - Build all Docker images"
    echo "  push         - Push all images to ECR"
    echo "  build-push   - Build and push all images"
    echo "  list         - List all buildable images"
    echo "  clean        - Remove local Docker images"
    echo "  login        - Login to ECR"
    echo "  single IMAGE - Build single image"
    echo ""
    echo "Options:"
    echo "  --no-push           - Don't push images after building"
    echo "  --sequential        - Build images sequentially (not parallel)"
    echo "  --no-cache          - Build without Docker cache"
    echo "  --tag=TAG           - Use custom image tag (default: latest)"
    echo "  --registry=REG      - Use custom ECR registry"
    echo "  --include-gpu       - Include GPU-enabled images"
    echo ""
    echo "Environment Variables:"
    echo "  ECR_REGISTRY        - ECR registry URL"
    echo "  IMAGE_TAG          - Docker image tag (default: latest)"
    echo "  AWS_REGION         - AWS region (default: us-west-2)"
    echo "  PUSH_IMAGES        - Whether to push images (default: true)"
    echo "  PARALLEL_BUILDS    - Build images in parallel (default: true)"
    echo ""
    echo "Examples:"
    echo "  $0 build                              # Build all images"
    echo "  $0 build-push --tag=v1.0.0          # Build and push with custom tag"
    echo "  $0 single coordinator                # Build only coordinator image"
    echo "  $0 build --no-push --include-gpu     # Build all including GPU images"
}

# Function to check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"

    local errors=0

    # Check docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ docker not found${NC}"
        echo "   Install from: https://docs.docker.com/get-docker/"
        errors=$((errors + 1))
    else
        if ! docker info &> /dev/null; then
            echo -e "${RED}❌ Docker daemon not running${NC}"
            echo "   Start Docker Desktop or run: sudo systemctl start docker"
            errors=$((errors + 1))
        else
            local docker_version=$(docker version --format '{{.Server.Version}}')
            echo -e "${GREEN}✅ Docker ${docker_version}${NC}"
        fi
    fi

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ aws cli not found${NC}"
        echo "   Install from: https://aws.amazon.com/cli/"
        errors=$((errors + 1))
    else
        local aws_version=$(aws --version | cut -d/ -f2 | cut -d' ' -f1)
        echo -e "${GREEN}✅ aws cli ${aws_version}${NC}"
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        echo "   Run: aws configure"
        errors=$((errors + 1))
    else
        local aws_account=$(aws sts get-caller-identity --query Account --output text)
        echo -e "${GREEN}✅ AWS credentials configured (Account: ${aws_account})${NC}"
    fi

    # Check build context
    if [ ! -d "$BUILD_CONTEXT" ]; then
        echo -e "${RED}❌ Build context not found: $BUILD_CONTEXT${NC}"
        errors=$((errors + 1))
    else
        echo -e "${GREEN}✅ Build context found${NC}"
    fi

    # Check Dockerfiles
    local dockerfile_count=0
    for item in "${IMAGES[@]}"; do
        local dockerfile="${item#*:}"
        if [ -f "$BUILD_CONTEXT/$dockerfile" ]; then
            dockerfile_count=$((dockerfile_count + 1))
        fi
    done
    echo -e "${GREEN}✅ ${dockerfile_count} Dockerfiles found${NC}"

    if [ $errors -gt 0 ]; then
        echo -e "${RED}❌ Prerequisites check failed. Please fix the issues above.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All prerequisites satisfied${NC}"
}

# Function to login to ECR
ecr_login() {
    print_section "Logging into ECR"

    echo -e "${CYAN}Getting ECR login token...${NC}"
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_REGISTRY"

    echo -e "${GREEN}✅ Successfully logged into ECR${NC}"
}

# Function to create ECR repositories if they don't exist
create_ecr_repos() {
    print_section "Ensuring ECR Repositories Exist"

    local all_images=($(get_image_names "IMAGES"))
    if [ "$INCLUDE_GPU" = "true" ]; then
        all_images+=($(get_image_names "GPU_IMAGES"))
    fi

    for image_name in "${all_images[@]}"; do
        local repo_name="insurance-claims/${image_name}"

        if ! aws ecr describe-repositories --repository-names "$repo_name" --region "$AWS_REGION" &> /dev/null; then
            echo -e "${YELLOW}Creating ECR repository: ${repo_name}${NC}"
            aws ecr create-repository \
                --repository-name "$repo_name" \
                --region "$AWS_REGION" \
                --image-scanning-configuration scanOnPush=true \
                --encryption-configuration encryptionType=AES256 > /dev/null
        else
            echo -e "${GREEN}✅ Repository exists: ${repo_name}${NC}"
        fi
    done
}

# Function to build a single image
build_single_image() {
    local image_name="$1"
    local dockerfile="$2"
    local full_image_name="${ECR_REGISTRY}/insurance-claims/${image_name}:${IMAGE_TAG}"

    echo -e "${CYAN}Building ${image_name}...${NC}"

    local cache_option=""
    if [ "$NO_CACHE" = "true" ]; then
        cache_option="--no-cache"
    fi

    # Build image (force amd64 architecture)
    docker build \
        --platform=linux/amd64 \
        $cache_option \
        -t "$full_image_name" \
        -f "$BUILD_CONTEXT/$dockerfile" \
        "$BUILD_CONTEXT"

    # Tag as latest if not already latest
    if [ "$IMAGE_TAG" != "latest" ]; then
        docker tag "$full_image_name" "${ECR_REGISTRY}/insurance-claims/${image_name}:latest"
    fi

    echo -e "${GREEN}✅ Built ${image_name}${NC}"
}

# Function to push a single image
push_single_image() {
    local image_name="$1"
    local full_image_name="${ECR_REGISTRY}/insurance-claims/${image_name}:${IMAGE_TAG}"

    echo -e "${CYAN}Pushing ${image_name}...${NC}"
    docker push "$full_image_name"

    # Also push latest tag if not already latest
    if [ "$IMAGE_TAG" != "latest" ]; then
        docker push "${ECR_REGISTRY}/insurance-claims/${image_name}:latest"
    fi

    echo -e "${GREEN}✅ Pushed ${image_name}${NC}"
}

# Function to build all images
build_all_images() {
    print_section "Building Docker Images"

    local images_to_build=($(get_image_names "IMAGES"))
    if [ "$INCLUDE_GPU" = "true" ]; then
        images_to_build+=($(get_image_names "GPU_IMAGES"))
        echo -e "${YELLOW}Including GPU-enabled images${NC}"
    fi

    echo -e "${CYAN}Building ${#images_to_build[@]} images with tag: ${IMAGE_TAG}${NC}"
    echo -e "${CYAN}Registry: ${ECR_REGISTRY}${NC}"
    echo ""

    if [ "$PARALLEL_BUILDS" = "true" ]; then
        echo -e "${CYAN}Building images in parallel...${NC}"

        # Start builds in background
        local pids=()
        for image_name in "${images_to_build[@]}"; do
            local dockerfile=""
            if image_exists "$image_name" "IMAGES"; then
                dockerfile=$(get_dockerfile_for_image "$image_name" "IMAGES")
            else
                dockerfile=$(get_dockerfile_for_image "$image_name" "GPU_IMAGES")
            fi

            build_single_image "$image_name" "$dockerfile" &
            pids+=($!)
        done

        # Wait for all builds to complete
        local failed=0
        for pid in "${pids[@]}"; do
            if ! wait "$pid"; then
                failed=$((failed + 1))
            fi
        done

        if [ $failed -gt 0 ]; then
            echo -e "${RED}❌ ${failed} builds failed${NC}"
            exit 1
        fi
    else
        echo -e "${CYAN}Building images sequentially...${NC}"

        for image_name in "${images_to_build[@]}"; do
            local dockerfile=""
            if image_exists "$image_name" "IMAGES"; then
                dockerfile=$(get_dockerfile_for_image "$image_name" "IMAGES")
            else
                dockerfile=$(get_dockerfile_for_image "$image_name" "GPU_IMAGES")
            fi

            build_single_image "$image_name" "$dockerfile"
        done
    fi

    echo -e "${GREEN}✅ All images built successfully${NC}"
}

# Function to push all images
push_all_images() {
    print_section "Pushing Images to ECR"

    local images_to_push=($(get_image_names "IMAGES"))
    if [ "$INCLUDE_GPU" = "true" ]; then
        images_to_push+=($(get_image_names "GPU_IMAGES"))
    fi

    # Ensure we're logged in
    ecr_login

    # Create repositories
    create_ecr_repos

    echo -e "${CYAN}Pushing ${#images_to_push[@]} images...${NC}"

    if [ "$PARALLEL_BUILDS" = "true" ]; then
        # Push in parallel
        local pids=()
        for image_name in "${images_to_push[@]}"; do
            push_single_image "$image_name" &
            pids+=($!)
        done

        # Wait for all pushes to complete
        local failed=0
        for pid in "${pids[@]}"; do
            if ! wait "$pid"; then
                failed=$((failed + 1))
            fi
        done

        if [ $failed -gt 0 ]; then
            echo -e "${RED}❌ ${failed} pushes failed${NC}"
            exit 1
        fi
    else
        # Push sequentially
        for image_name in "${images_to_push[@]}"; do
            push_single_image "$image_name"
        done
    fi

    echo -e "${GREEN}✅ All images pushed successfully${NC}"
}

# Function to list images
list_images() {
    print_section "Available Images"

    echo -e "${CYAN}Standard Images:${NC}"
    for item in "${IMAGES[@]}"; do
        local image_name="${item%%:*}"
        local dockerfile="${item#*:}"
        echo "  📦 ${image_name} (${dockerfile})"
    done

    echo ""
    echo -e "${CYAN}GPU-Enabled Images:${NC}"
    for item in "${GPU_IMAGES[@]}"; do
        local image_name="${item%%:*}"
        local dockerfile="${item#*:}"
        echo "  🚀 ${image_name} (${dockerfile})"
    done

    echo ""
    echo -e "${CYAN}Local Images:${NC}"
    docker images "${ECR_REGISTRY}/insurance-claims/*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" || true
}

# Function to clean local images
clean_images() {
    print_section "Cleaning Local Images"

    echo -e "${YELLOW}⚠️  This will remove all local insurance-claims images${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi

    echo -e "${CYAN}Removing local images...${NC}"

    # Remove images
    local removed=0
    for image in $(docker images "${ECR_REGISTRY}/insurance-claims/*" -q); do
        docker rmi "$image" && removed=$((removed + 1))
    done

    echo -e "${GREEN}✅ Removed ${removed} images${NC}"

    # Clean up dangling images
    echo -e "${CYAN}Cleaning dangling images...${NC}"
    docker image prune -f

    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Function to build a single specific image
build_single() {
    local image_name="$1"

    print_section "Building Single Image: ${image_name}"

    # Check if image exists in our definitions
    local dockerfile=""
    if image_exists "$image_name" "IMAGES"; then
        dockerfile=$(get_dockerfile_for_image "$image_name" "IMAGES")
    elif image_exists "$image_name" "GPU_IMAGES"; then
        dockerfile=$(get_dockerfile_for_image "$image_name" "GPU_IMAGES")
    else
        echo -e "${RED}❌ Unknown image: ${image_name}${NC}"
        echo "Available images:"
        list_images
        exit 1
    fi

    build_single_image "$image_name" "$dockerfile"

    if [ "$PUSH_IMAGES" = "true" ]; then
        ecr_login
        create_ecr_repos
        push_single_image "$image_name"
    fi

    echo -e "${GREEN}✅ Completed building ${image_name}${NC}"
}

# Main script logic
main() {
    echo -e "${BLUE}🐳 Docker Image Builder for Insurance Agentic AI Demo${NC}"
    echo "============================================================"
    echo -e "${CYAN}Registry: ${ECR_REGISTRY}${NC}"
    echo -e "${CYAN}Tag: ${IMAGE_TAG}${NC}"
    echo -e "${CYAN}Region: ${AWS_REGION}${NC}"
    echo ""

    # Parse command line arguments
    NO_CACHE="false"
    INCLUDE_GPU="false"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-push)
                PUSH_IMAGES="false"
                shift
                ;;
            --sequential)
                PARALLEL_BUILDS="false"
                shift
                ;;
            --no-cache)
                NO_CACHE="true"
                shift
                ;;
            --include-gpu)
                INCLUDE_GPU="true"
                shift
                ;;
            --tag=*)
                IMAGE_TAG="${1#*=}"
                shift
                ;;
            --registry=*)
                ECR_REGISTRY="${1#*=}"
                shift
                ;;
            *)
                if [ -z "$COMMAND" ]; then
                    COMMAND="$1"
                else
                    IMAGE_NAME="$1"
                fi
                shift
                ;;
        esac
    done

    # Check prerequisites for build commands
    if [[ "$COMMAND" =~ ^(build|push|build-push|single|clean)$ ]]; then
        check_prerequisites
    fi

    # Execute command
    case "$COMMAND" in
        build)
            build_all_images
            ;;
        push)
            push_all_images
            ;;
        build-push)
            build_all_images
            if [ "$PUSH_IMAGES" = "true" ]; then
                push_all_images
            fi
            ;;
        single)
            if [ -z "$IMAGE_NAME" ]; then
                echo -e "${RED}❌ Image name required for single build${NC}"
                echo "Usage: $0 single IMAGE_NAME"
                exit 1
            fi
            build_single "$IMAGE_NAME"
            ;;
        list)
            list_images
            ;;
        clean)
            clean_images
            ;;
        login)
            ecr_login
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
    main "$@"
fi