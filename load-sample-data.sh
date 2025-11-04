#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Loading Sample Data into MongoDB${NC}"
echo ""

# Get MongoDB pod name
MONGO_POD=$(kubectl get pods -n insurance-claims -l app=mongodb -o jsonpath='{.items[0].metadata.name}')

if [ -z "$MONGO_POD" ]; then
    echo -e "${YELLOW}Error: MongoDB pod not found${NC}"
    exit 1
fi

echo -e "${BLUE}→ MongoDB pod: $MONGO_POD${NC}"

# MongoDB credentials
MONGO_USER="admin"
MONGO_PASS="insurance_db_password123"
MONGO_DB="claims_db"

# Generate sample policies directly
echo -e "${BLUE}→ Generating sample policies...${NC}"

kubectl exec -n insurance-claims $MONGO_POD -- mongosh \
    --username $MONGO_USER \
    --password $MONGO_PASS \
    --authenticationDatabase admin \
    $MONGO_DB \
    --eval '
// Clear existing data
db.policies.deleteMany({});
db.claims.deleteMany({});

// Generate 50 sample policies
const policies = [];
const policyTypes = ["Personal Auto", "Commercial Auto", "Property", "Liability"];
const states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH"];

for (let i = 1; i <= 50; i++) {
    policies.push({
        policy_number: "POL-2024-" + String(i).padStart(4, "0"),
        policy_effective_date: new Date("2024-01-01"),
        policy_expiration_date: new Date("2025-01-01"),
        line_of_business: policyTypes[i % policyTypes.length],
        policy_status: "Active",
        sum_assured: 100000 + (i * 10000),
        policy_premium: 1200 + (i * 50),
        customer_no: "CUST-" + String(i).padStart(4, "0"),
        primary_insured_customer_id: "CUST-" + String(i).padStart(4, "0"),
        issue_state: states[i % states.length],
        resident_state: states[i % states.length],
        generation_date: new Date(),
        last_updated: new Date(),
        policy_in_force: true
    });
}

db.policies.insertMany(policies);
print("Inserted " + policies.length + " policies");

// Generate 25 sample claims
const claims = [];
const claimTypes = ["Collision", "Comprehensive", "Theft", "Liability", "Property Damage"];

for (let i = 1; i <= 25; i++) {
    const policyNum = "POL-2024-" + String((i % 50) + 1).padStart(4, "0");
    const claimAmount = 5000 + (Math.random() * 50000);
    const fraudScore = Math.random();

    claims.push({
        claim_id: "CLM-" + new Date().toISOString().split("T")[0].replace(/-/g, "") + "-" + String(i).padStart(4, "0"),
        policy_number: policyNum,
        customer_name: "Customer " + String((i % 50) + 1),
        customer_email: "customer" + ((i % 50) + 1) + "@example.com",
        customer_phone: "+1-555-" + String(1000 + i).slice(-4),
        claim_type: claimTypes[i % claimTypes.length],
        claim_amount: Math.round(claimAmount * 100) / 100,
        description: "Sample claim " + i + " - testing insurance processing system",
        incident_date: new Date(Date.now() - (Math.random() * 30 * 24 * 60 * 60 * 1000)),
        status: (i % 3 === 0) ? "approved" : "submitted",
        priority: fraudScore > 0.7 ? "urgent" : fraudScore > 0.4 ? "high" : "normal",
        fraud_score: Math.round(fraudScore * 100) / 100,
        ai_recommendation: {
            fraud_score: Math.round(fraudScore * 100) / 100,
            policy_valid: true,
            recommended_action: fraudScore > 0.6 ? "investigate" : "approve",
            external_data_summary: "External data verified"
        },
        created_at: new Date(),
        updated_at: new Date()
    });
}

db.claims.insertMany(claims);
print("Inserted " + claims.length + " claims");

// Create indexes
db.policies.createIndex({ policy_number: 1 }, { unique: true });
db.claims.createIndex({ claim_id: 1 }, { unique: true });
db.claims.createIndex({ policy_number: 1 });
db.claims.createIndex({ status: 1 });
print("Indexes created");
'

# Verify data
echo ""
echo -e "${BLUE}→ Verifying data...${NC}"

POLICY_COUNT=$(kubectl exec -n insurance-claims $MONGO_POD -- mongosh \
    --username $MONGO_USER \
    --password $MONGO_PASS \
    --authenticationDatabase admin \
    --quiet \
    $MONGO_DB \
    --eval 'db.policies.countDocuments()' | tail -1)

CLAIM_COUNT=$(kubectl exec -n insurance-claims $MONGO_POD -- mongosh \
    --username $MONGO_USER \
    --password $MONGO_PASS \
    --authenticationDatabase admin \
    --quiet \
    $MONGO_DB \
    --eval 'db.claims.countDocuments()' | tail -1)

echo ""
echo -e "${GREEN}✓ Data loaded successfully!${NC}"
echo ""
echo "Summary:"
echo "  - Policies: $POLICY_COUNT"
echo "  - Claims: $CLAIM_COUNT"
echo ""
echo "Access the application:"
echo "  http://insurance-claims-alb-1846452428.us-west-2.elb.amazonaws.com"
echo ""
echo "Test scenarios:"
echo "  1. Claimant Portal: Submit new claim with policy POL-2024-0001"
echo "  2. Adjuster Dashboard: Review submitted claims"
echo "  3. Click 'Review' button to see detailed claim view"
echo ""
