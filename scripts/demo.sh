#!/bin/bash

################################################################################
# COMPREHENSIVE DEMO SCRIPT FOR PERSONA-BASED INSURANCE CLAIMS SYSTEM
# Run this script for a complete end-to-end demonstration
################################################################################

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
NAMESPACE="insurance-claims"
MONGODB_NAMESPACE="database"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║  $1"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${CYAN}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

wait_for_user() {
    echo -e "${YELLOW}"
    read -p "Press ENTER to continue..."
    echo -e "${NC}"
}

check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    print_success "AWS CLI installed"

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install it first."
        exit 1
    fi
    print_success "kubectl installed"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install it first."
        exit 1
    fi
    print_success "Docker installed"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install it first."
        exit 1
    fi
    print_success "Python 3 installed"

    # Check kubectl context
    CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
    if [ -z "$CURRENT_CONTEXT" ]; then
        print_error "No kubectl context configured. Please configure your EKS cluster."
        exit 1
    fi
    print_success "kubectl context: $CURRENT_CONTEXT"
}

################################################################################
# Main Demo Functions
################################################################################

demo_phase_1_data_loading() {
    print_header "PHASE 1: Load Synthetic Insurance Data"

    print_step "This will load 500+ realistic insurance policies and generate 100+ claims"
    wait_for_user

    # Check if zip file exists
    ZIP_FILE="newdata/syntheticdatageneral/dist/SyntheticInsuranceData-byPolicy-2022-08-11.zip"
    if [ ! -f "$ZIP_FILE" ]; then
        print_error "Synthetic data file not found: $ZIP_FILE"
        print_warning "Please ensure the synthetic data is available"
        exit 1
    fi

    print_step "Loading synthetic data into MongoDB..."
    python3 -m applications.insurance-claims-processing.src.data_loader "$ZIP_FILE"

    print_success "Data loaded successfully!"
    print_step "Summary:"
    echo "  • 500+ insurance policies loaded"
    echo "  • 100+ claims generated with realistic fraud scores"
    echo "  • MongoDB indexed and optimized"
    echo ""
}

demo_phase_2_build_and_deploy() {
    print_header "PHASE 2: Build & Deploy to AWS EKS"

    print_step "Building Docker images for persona-based system..."
    wait_for_user

    # Build web interface (with new persona-based code)
    print_step "Building web-interface with persona-based portals..."
    ECR_REGISTRY=$ECR_REGISTRY ./scripts/build-docker-images.sh build web-interface
    print_success "Web interface built"

    # Build coordinator
    print_step "Building AI coordinator..."
    ECR_REGISTRY=$ECR_REGISTRY ./scripts/build-docker-images.sh build coordinator
    print_success "Coordinator built"

    # Push to ECR
    print_step "Pushing images to Amazon ECR..."
    ECR_REGISTRY=$ECR_REGISTRY ./scripts/build-docker-images.sh push web-interface
    ECR_REGISTRY=$ECR_REGISTRY ./scripts/build-docker-images.sh push coordinator
    print_success "Images pushed to ECR"

    # Deploy to Kubernetes
    print_step "Deploying to Kubernetes..."
    ECR_REGISTRY=$ECR_REGISTRY ./scripts/deploy-kubernetes.sh deploy

    # Wait for pods to be ready
    print_step "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=web-interface -n $NAMESPACE --timeout=120s

    print_success "Deployment complete!"
    echo ""
}

demo_phase_3_access_system() {
    print_header "PHASE 3: Access the Persona-Based Portals"

    print_step "Setting up access to the system..."

    # Get service information
    print_step "Service information:"
    kubectl get svc -n $NAMESPACE web-interface-service

    # Port forwarding instructions
    echo ""
    print_warning "Starting port forwarding to access the system locally..."
    print_step "Running: kubectl port-forward -n $NAMESPACE svc/web-interface-service 8080:8080"
    echo ""

    # Start port forward in background
    kubectl port-forward -n $NAMESPACE svc/web-interface-service 8080:8080 &
    PF_PID=$!

    # Wait for port forward to be ready
    sleep 3

    print_success "Port forwarding active! System is accessible at:"
    echo ""
    echo -e "${GREEN}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${GREEN}│  🌐 Portal Selector:    ${CYAN}http://localhost:8080/${GREEN}             │${NC}"
    echo -e "${GREEN}│  👤 Claimant Portal:    ${CYAN}http://localhost:8080/claimant${GREEN}    │${NC}"
    echo -e "${GREEN}│  👨‍💼 Adjuster Dashboard: ${CYAN}http://localhost:8080/adjuster${GREEN}    │${NC}"
    echo -e "${GREEN}│  🔍 SIU Portal:         ${CYAN}http://localhost:8080/siu${GREEN}          │${NC}"
    echo -e "${GREEN}│  📊 Supervisor Portal:  ${CYAN}http://localhost:8080/supervisor${GREEN}  │${NC}"
    echo -e "${GREEN}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""

    # Open browser (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_step "Opening portal selector in browser..."
        sleep 1
        open http://localhost:8080/
    fi

    echo ""
    print_warning "Port forwarding is running in the background (PID: $PF_PID)"
    print_warning "To stop it later: kill $PF_PID"
    echo ""

    wait_for_user
}

demo_phase_4_demo_walkthrough() {
    print_header "PHASE 4: Demo Walkthrough"

    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════╗
║                    DEMO WALKTHROUGH GUIDE                         ║
╚═══════════════════════════════════════════════════════════════════╝

🎬 SCENARIO: Auto Collision Claim Processing

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACT 1: CLAIMANT FILES CLAIM

1. Open: http://localhost:8080/claimant

2. Enter any policy number (or skip to see the form)

3. Fill out claim form:
   ┌─────────────────────────────────────────┐
   │ Claim Type:     Collision               │
   │ Incident Date:  Today                   │
   │ Amount:         $15,000                 │
   │ Location:       Los Angeles, CA         │
   │ Description:    "Rear-ended at traffic  │
   │                 light while stopped"    │
   └─────────────────────────────────────────┘

4. Click "Submit Claim"

5. NOTE the Claim ID (e.g., CLM-20250113-A7B2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACT 2: AI PROCESSING (Automatic - Show in Logs)

Watch the coordinator logs for real-time AI processing:

$ kubectl logs -n insurance-claims -l app=coordinator -f

You'll see:
  ⚡ Claim received
  🤖 Fraud Agent analyzing... Score: 0.23 (Low Risk)
  📋 Policy Agent verifying... Coverage valid
  🔍 External data gathering... Weather/location verified
  ✅ Recommendation: Approve with standard review
  👨‍💼 Routed to: Claims Adjuster

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACT 3: ADJUSTER REVIEWS & DECIDES

1. Open: http://localhost:8080/adjuster

2. You'll see the claim in the queue with:
   ┌─────────────────────────────────────────┐
   │ Claim ID:      CLM-20250113-A7B2       │
   │ Fraud Score:   0.23 (🟢 Low Risk)      │
   │ Amount:        $15,000                 │
   │ Priority:      Normal                  │
   │ AI Rec:        Approve                 │
   └─────────────────────────────────────────┘

3. Click "Review" to see detailed analysis

4. Make decision:
   • Decision: Approve
   • Settlement: $14,500
   • Reasoning: "Clear liability, standard rear-end collision"

5. Submit → Claim approved instantly!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACT 4: SUPERVISOR MONITORS

1. Open: http://localhost:8080/supervisor

2. View real-time analytics:
   ┌─────────────────────────────────────────┐
   │ Total Claims:            127           │
   │ Avg Processing Time:     4.2 min       │
   │ Fraud Detection Rate:    12.8%         │
   │ Approval Rate:           78%           │
   │ Total Claim Amount:      $2.4M         │
   └─────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BONUS: FRAUD INVESTIGATION

1. Submit a high-value suspicious claim:
   • Amount: $85,000
   • Unusual details
   • AI assigns high fraud score (0.87)

2. Open: http://localhost:8080/siu

3. See claim in high-risk queue

4. Click "Investigate" to start fraud investigation workflow

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY TALKING POINTS FOR DEMO:

✨ "Notice how each portal is completely tailored to its user"
✨ "AI processes the claim in under 3 seconds"
✨ "Fraud detection happens automatically with every claim"
✨ "The adjuster gets AI recommendations but makes final call"
✨ "All decisions are audited with timestamps and reasoning"
✨ "System scales automatically based on load"
✨ "Running on production-grade AWS EKS infrastructure"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    wait_for_user
}

demo_phase_5_monitoring() {
    print_header "PHASE 5: Monitoring & Logs"

    print_step "Real-time monitoring commands:"
    echo ""
    echo "View all pods:"
    echo "  $ kubectl get pods -n $NAMESPACE"
    echo ""
    echo "Watch coordinator logs (AI processing):"
    echo "  $ kubectl logs -n $NAMESPACE -l app=coordinator -f"
    echo ""
    echo "Watch web interface logs:"
    echo "  $ kubectl logs -n $NAMESPACE -l app=web-interface -f"
    echo ""
    echo "Check MongoDB:"
    echo "  $ kubectl exec -it -n $MONGODB_NAMESPACE mongodb-0 -- mongosh"
    echo ""
    echo "View all claims in database:"
    echo "  $ kubectl exec -it -n $MONGODB_NAMESPACE mongodb-0 -- mongosh claims_db --eval 'db.claims.countDocuments()'"
    echo ""

    wait_for_user
}

demo_phase_6_cleanup() {
    print_header "PHASE 6: Cleanup (Optional)"

    print_warning "Do you want to clean up the demo environment?"
    read -p "Type 'yes' to cleanup, or press ENTER to skip: " CLEANUP

    if [ "$CLEANUP" == "yes" ]; then
        print_step "Stopping port forwarding..."
        if [ ! -z "$PF_PID" ]; then
            kill $PF_PID 2>/dev/null || true
        fi

        print_step "Cleaning up Kubernetes resources..."
        kubectl delete namespace $NAMESPACE --timeout=60s || true

        print_success "Cleanup complete!"
    else
        print_success "Skipping cleanup. Resources remain running."
        print_warning "To cleanup later, run: kubectl delete namespace $NAMESPACE"
    fi

    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    clear

    cat << 'EOF'

   _____ _                              _____                            _
  / ____| |                            |  __ \                          (_)
 | |    | | __ _ _   _ ___  ___       | |__) | __ ___   ___ ___  ___ ___ _ __   __ _
 | |    | |/ _` | | | / __|/ _ \      |  ___/ '__/ _ \ / __/ _ \/ __/ __| '_ \ / _` |
 | |____| | (_| | |_| \__ \  __/      | |   | | | (_) | (_|  __/\__ \__ \ | | | (_| |
  \_____|_|\__,_|\__,_|___/\___|      |_|   |_|  \___/ \___\___||___/___/_| |_|\__, |
                                                                                 __/ |
   AI-Powered Insurance on AWS EKS                                             |___/

EOF

    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}           COMPREHENSIVE DEMO SCRIPT${NC}"
    echo -e "${CYAN}    Production-Grade Persona-Based Claims System${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Check prerequisites
    check_prerequisites
    echo ""

    print_success "All prerequisites met! Ready to start demo."
    echo ""
    print_warning "This demo will:"
    echo "  1. Load 500+ synthetic insurance policies"
    echo "  2. Build and deploy the persona-based system"
    echo "  3. Set up access to all 4 portals"
    echo "  4. Guide you through a complete demo"
    echo ""

    wait_for_user

    # Execute demo phases
    demo_phase_1_data_loading
    demo_phase_2_build_and_deploy
    demo_phase_3_access_system
    demo_phase_4_demo_walkthrough
    demo_phase_5_monitoring
    demo_phase_6_cleanup

    # Final message
    print_header "DEMO COMPLETE!"

    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════╗
║                      🎉 DEMO SUCCESSFUL! 🎉                       ║
╚═══════════════════════════════════════════════════════════════════╝

Your AI-Powered Insurance Claims Processing System is ready!

📱 Access Points:
   • Portal Selector:    http://localhost:8080/
   • Claimant Portal:    http://localhost:8080/claimant
   • Adjuster Dashboard: http://localhost:8080/adjuster
   • SIU Portal:         http://localhost:8080/siu
   • Supervisor Portal:  http://localhost:8080/supervisor

📚 Documentation:
   • README.md                     - Complete guide
   • PERSONA_BASED_DEPLOYMENT.md   - Deployment details
   • REVOLUTIONARY_FEATURES.md     - Feature breakdown

💡 Tips for Your Demo Tomorrow:
   1. Keep this terminal open for logs
   2. Have browser with all portals in tabs ready
   3. Prepare 2-3 claim scenarios
   4. Show logs during AI processing
   5. Highlight fraud detection capabilities

🚀 You're all set to revolutionize insurance claims processing!

EOF

    print_success "Demo script completed successfully!"
    echo ""
}

# Trap to cleanup port forwarding on exit
trap 'kill $PF_PID 2>/dev/null || true' EXIT

# Run main function
main "$@"
