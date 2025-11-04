#!/bin/bash
###############################################################
# Deployment Validation Script
# Checks if all components are running correctly
###############################################################

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Deployment Validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Check cluster connection
echo -e "${YELLOW}→ Checking cluster connection...${NC}"
if kubectl cluster-info &> /dev/null; then
    echo -e "${GREEN}✓ Connected to cluster${NC}"
else
    echo -e "${RED}✗ Cannot connect to cluster${NC}"
    exit 1
fi
echo ""

# Check External Secrets Operator
echo -e "${YELLOW}→ Checking External Secrets Operator...${NC}"
if kubectl get pods -n external-secrets -l app.kubernetes.io/name=external-secrets &> /dev/null; then
    READY=$(kubectl get pods -n external-secrets -l app.kubernetes.io/name=external-secrets -o json | jq '.items[0].status.conditions[] | select(.type=="Ready") | .status' -r 2>/dev/null || echo "False")
    if [ "$READY" == "True" ]; then
        echo -e "${GREEN}✓ External Secrets Operator running${NC}"
    else
        echo -e "${YELLOW}⚠ External Secrets Operator not ready${NC}"
    fi
else
    echo -e "${RED}✗ External Secrets Operator not found${NC}"
fi
echo ""

# Check secrets are synced
echo -e "${YELLOW}→ Checking secret synchronization...${NC}"
if kubectl get externalsecrets -n insurance-claims &> /dev/null; then
    kubectl get externalsecrets -n insurance-claims
    SYNCED=$(kubectl get externalsecrets mongodb-credentials -n insurance-claims -o json 2>/dev/null | jq -r '.status.conditions[] | select(.type=="Ready") | .status' 2>/dev/null || echo "False")
    if [ "$SYNCED" == "True" ]; then
        echo -e "${GREEN}✓ Secrets synchronized${NC}"
    else
        echo -e "${YELLOW}⚠ Secrets not yet synchronized${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ExternalSecrets not deployed${NC}"
fi
echo ""

# Check pods
echo -e "${YELLOW}→ Checking application pods...${NC}"
kubectl get pods -n insurance-claims

echo ""
TOTAL=$(kubectl get pods -n insurance-claims --no-headers 2>/dev/null | wc -l | tr -d ' ')
RUNNING=$(kubectl get pods -n insurance-claims --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [ "$RUNNING" -eq "$TOTAL" ] && [ "$TOTAL" -gt "0" ]; then
    echo -e "${GREEN}✓ All $TOTAL pods running${NC}"
elif [ "$TOTAL" -gt "0" ]; then
    echo -e "${YELLOW}⚠ $RUNNING/$TOTAL pods running${NC}"
else
    echo -e "${RED}✗ No pods found${NC}"
fi
echo ""

# Check services
echo -e "${YELLOW}→ Checking services...${NC}"
kubectl get svc -n insurance-claims
echo ""

# Check ingress
echo -e "${YELLOW}→ Checking ingress...${NC}"
kubectl get ingress -n insurance-claims

ALB_DNS=$(kubectl get ingress insurance-claims-ingress -n insurance-claims \
    -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

echo ""
if [ -n "$ALB_DNS" ]; then
    echo -e "${GREEN}✓ ALB provisioned${NC}"
    echo -e "${BLUE}  DNS: $ALB_DNS${NC}"
    
    # Test HTTP redirect
    echo -e "${YELLOW}→ Testing HTTP to HTTPS redirect...${NC}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L http://$ALB_DNS 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "301" ]; then
        echo -e "${GREEN}✓ ALB responding (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}⚠ ALB returned HTTP $HTTP_CODE${NC}"
    fi
else
    echo -e "${YELLOW}⚠ ALB not yet provisioned${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Validation Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}To access the application:${NC}"
if [ -n "$ALB_DNS" ]; then
    echo -e "  • http://$ALB_DNS"
    echo -e "  • https://$ALB_DNS"
else
    echo -e "  • Run: kubectl get ingress -n insurance-claims"
fi
echo ""
echo -e "${BLUE}To view logs:${NC}"
echo -e "  • kubectl logs -f deployment/coordinator -n insurance-claims"
echo -e "  • kubectl logs -f deployment/claims-web-interface -n insurance-claims"
echo ""
echo -e "${BLUE}To monitor pods:${NC}"
echo -e "  • kubectl get pods -n insurance-claims -w"
echo ""
