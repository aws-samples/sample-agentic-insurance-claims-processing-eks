#!/bin/bash
################################################################################
# Sample Data Loader - Insurance Claims Processing System
#
# Generates and loads realistic sample data into MongoDB
#
# Usage:
#   ./scripts/load-data.sh [OPTIONS]
#
# Options:
#   --policies N        Number of policies to generate (default: 500)
#   --claims N          Number of claims to generate (default: 100)
#   --clear             Clear existing data before loading
#   --help              Show this help message
#
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default configuration
NUM_POLICIES=500
NUM_CLAIMS=100
CLEAR_DATA=false
NAMESPACE="insurance-claims"

################################################################################
# Functions
################################################################################

show_help() {
    sed -n '2,/^$/p' "$0" | sed 's/^# //; s/^#//'
    exit 0
}

log_info() {
    echo -e "${BLUE}→ ${NC}$1"
}

log_success() {
    echo -e "${GREEN}✓ ${NC}$1"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${NC}$1"
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --policies)
                NUM_POLICIES="$2"
                shift 2
                ;;
            --claims)
                NUM_CLAIMS="$2"
                shift 2
                ;;
            --clear)
                CLEAR_DATA=true
                shift
                ;;
            --help)
                show_help
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                ;;
        esac
    done

    echo -e "${BLUE}Loading Sample Data into MongoDB${NC}"
    echo ""
    echo "Configuration:"
    echo "  Policies: $NUM_POLICIES"
    echo "  Claims:   $NUM_CLAIMS"
    echo ""

    # Get MongoDB pod name
    log_info "Finding MongoDB pod..."
    MONGO_POD=$(kubectl get pods -n $NAMESPACE -l app=mongodb -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$MONGO_POD" ]; then
        log_warning "Error: MongoDB pod not found"
        exit 1
    fi

    log_success "MongoDB pod: $MONGO_POD"

    # MongoDB credentials (PLACEHOLDER VALUES - replace with actual credentials from secrets management)
    # In production, these should come from Kubernetes Secrets or AWS Secrets Manager
    # See docs/SECRETS_MANAGEMENT.md for secure credential management
    MONGO_USER="<MONGO_USERNAME>"
    MONGO_PASS="<MONGO_PASSWORD>"
    MONGO_DB="claims_db"

    # Generate data using MongoDB JavaScript
    log_info "Generating sample data..."

    kubectl exec -n $NAMESPACE $MONGO_POD -- mongosh \
        --username $MONGO_USER \
        --password $MONGO_PASS \
        --authenticationDatabase admin \
        $MONGO_DB \
        --eval "
// Configuration
const NUM_POLICIES = ${NUM_POLICIES};
const NUM_CLAIMS = ${NUM_CLAIMS};
const CLEAR_DATA = ${CLEAR_DATA};

print('Starting data generation...');

// Clear existing data if requested
if (CLEAR_DATA) {
    print('Clearing existing data...');
    db.policies.deleteMany({});
    db.claims.deleteMany({});
}

// Policy data
const policyTypes = [
    'Personal Auto',
    'Commercial Auto',
    'Homeowners',
    'Renters',
    'Commercial Property',
    'General Liability',
    'Workers Compensation',
    'Professional Liability',
    'Umbrella',
    'Life Insurance'
];

const states = [
    'CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI',
    'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI'
];

const firstNames = [
    'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
    'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa'
];

const lastNames = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris'
];

// Generate policies
print('Generating ' + NUM_POLICIES + ' policies...');
const policies = [];
const batchSize = 1000;

for (let i = 1; i <= NUM_POLICIES; i++) {
    const firstName = firstNames[Math.floor(Math.random() * firstNames.length)];
    const lastName = lastNames[Math.floor(Math.random() * lastNames.length)];
    const state = states[Math.floor(Math.random() * states.length)];
    const policyType = policyTypes[Math.floor(Math.random() * policyTypes.length)];

    const yearOffset = Math.floor(Math.random() * 3); // Policies from last 3 years
    const effectiveDate = new Date(2022 + yearOffset, Math.floor(Math.random() * 12), 1);
    const expirationDate = new Date(effectiveDate.getFullYear() + 1, effectiveDate.getMonth(), effectiveDate.getDate());

    const baseAmount = 50000 + Math.floor(Math.random() * 950000); // 50K to 1M
    const basePremium = Math.floor(baseAmount * 0.02); // ~2% of sum assured

    policies.push({
        policy_number: 'POL-' + (2022 + yearOffset) + '-' + String(i).padStart(6, '0'),
        policy_effective_date: effectiveDate,
        policy_expiration_date: expirationDate,
        line_of_business: policyType,
        policy_status: (Math.random() > 0.05) ? 'Active' : 'Inactive', // 95% active
        sum_assured: baseAmount,
        policy_premium: basePremium,
        customer_no: 'CUST-' + String(i).padStart(6, '0'),
        primary_insured_customer_id: 'CUST-' + String(i).padStart(6, '0'),
        first_name: firstName,
        last_name: lastName,
        email: firstName.toLowerCase() + '.' + lastName.toLowerCase() + '@example.com',
        phone: '+1-' + (200 + Math.floor(Math.random() * 800)) + '-555-' + String(1000 + Math.floor(Math.random() * 9000)),
        issue_state: state,
        resident_state: state,
        generation_date: new Date(),
        last_updated: new Date(),
        policy_in_force: true,
        coverage_details: {
            deductible: [500, 1000, 2500, 5000][Math.floor(Math.random() * 4)],
            coverage_limit: baseAmount,
            collision: Math.random() > 0.3,
            comprehensive: Math.random() > 0.3
        }
    });

    // Insert in batches for better performance
    if (policies.length >= batchSize) {
        db.policies.insertMany(policies);
        print('Inserted ' + policies.length + ' policies (total: ' + i + ')');
        policies.length = 0;
    }
}

// Insert remaining policies
if (policies.length > 0) {
    db.policies.insertMany(policies);
    print('Inserted remaining ' + policies.length + ' policies');
}

print('Total policies inserted: ' + NUM_POLICIES);

// Generate claims
print('Generating ' + NUM_CLAIMS + ' claims...');
const claims = [];
const claimTypes = [
    'Collision',
    'Comprehensive',
    'Theft',
    'Liability',
    'Property Damage',
    'Bodily Injury',
    'Medical Payments',
    'Vandalism',
    'Fire',
    'Water Damage'
];

const claimStatuses = ['submitted', 'pending_review', 'approved', 'denied', 'investigating'];
const priorities = ['low', 'normal', 'high', 'urgent'];

// Get random active policies for claims
const activePolicies = db.policies.find({ policy_status: 'Active' }).limit(NUM_POLICIES).toArray();

if (activePolicies.length === 0) {
    print('Error: No active policies found');
} else {
    for (let i = 1; i <= NUM_CLAIMS; i++) {
        const policy = activePolicies[Math.floor(Math.random() * activePolicies.length)];
        const claimType = claimTypes[Math.floor(Math.random() * claimTypes.length)];

        // Fraud score: 70% low, 20% medium, 10% high
        const rand = Math.random();
        let fraudScore;
        if (rand < 0.70) {
            fraudScore = Math.random() * 0.3; // 0-0.3
        } else if (rand < 0.90) {
            fraudScore = 0.3 + Math.random() * 0.3; // 0.3-0.6
        } else {
            fraudScore = 0.6 + Math.random() * 0.4; // 0.6-1.0
        }

        // Claim amount (higher amounts correlate slightly with fraud)
        const maxAmount = policy.sum_assured * 0.8;
        const claimAmount = Math.random() * maxAmount + (fraudScore * 20000);

        // Priority based on fraud score and amount
        let priority;
        if (fraudScore > 0.7 || claimAmount > 100000) {
            priority = 'urgent';
        } else if (fraudScore > 0.4 || claimAmount > 50000) {
            priority = 'high';
        } else {
            priority = ['normal', 'low'][Math.floor(Math.random() * 2)];
        }

        // Status distribution
        const statusRand = Math.random();
        let status;
        if (statusRand < 0.40) {
            status = 'submitted';
        } else if (statusRand < 0.60) {
            status = 'pending_review';
        } else if (statusRand < 0.80) {
            status = 'approved';
        } else if (statusRand < 0.95) {
            status = 'denied';
        } else {
            status = 'investigating';
        }

        const daysAgo = Math.floor(Math.random() * 90); // Claims from last 90 days
        const incidentDate = new Date();
        incidentDate.setDate(incidentDate.getDate() - daysAgo - 5);

        const createdDate = new Date();
        createdDate.setDate(createdDate.getDate() - daysAgo);

        const today = new Date().toISOString().split('T')[0].replace(/-/g, '');

        claims.push({
            claim_id: 'CLM-' + today + '-' + String(i).padStart(6, '0'),
            policy_number: policy.policy_number,
            customer_name: policy.first_name + ' ' + policy.last_name,
            customer_email: policy.email,
            customer_phone: policy.phone,
            claim_type: claimType,
            claim_amount: Math.round(claimAmount * 100) / 100,
            description: 'Insurance claim for ' + claimType.toLowerCase() + ' - case ' + i,
            incident_date: incidentDate,
            incident_location: policy.issue_state + ', USA',
            status: status,
            priority: priority,
            fraud_score: Math.round(fraudScore * 100) / 100,
            ai_recommendation: {
                fraud_score: Math.round(fraudScore * 100) / 100,
                policy_valid: Math.random() > 0.05, // 95% valid
                recommended_action: fraudScore > 0.6 ? 'investigate' : (fraudScore > 0.3 ? 'review' : 'approve'),
                external_data_summary: 'External verification ' + (Math.random() > 0.2 ? 'completed' : 'pending'),
                confidence_score: Math.round((0.7 + Math.random() * 0.3) * 100) / 100
            },
            created_at: createdDate,
            updated_at: new Date(),
            processing_time_minutes: Math.floor(Math.random() * 120) + 30
        });

        // Insert in batches
        if (claims.length >= batchSize) {
            db.claims.insertMany(claims);
            print('Inserted ' + claims.length + ' claims (total: ' + i + ')');
            claims.length = 0;
        }
    }

    // Insert remaining claims
    if (claims.length > 0) {
        db.claims.insertMany(claims);
        print('Inserted remaining ' + claims.length + ' claims');
    }

    print('Total claims inserted: ' + NUM_CLAIMS);
}

// Create indexes
print('Creating indexes...');
db.policies.createIndex({ policy_number: 1 }, { unique: true, background: true });
db.policies.createIndex({ policy_status: 1 }, { background: true });
db.policies.createIndex({ customer_no: 1 }, { background: true });
db.policies.createIndex({ issue_state: 1 }, { background: true });

db.claims.createIndex({ claim_id: 1 }, { unique: true, background: true });
db.claims.createIndex({ policy_number: 1 }, { background: true });
db.claims.createIndex({ status: 1 }, { background: true });
db.claims.createIndex({ priority: 1 }, { background: true });
db.claims.createIndex({ fraud_score: 1 }, { background: true });
db.claims.createIndex({ created_at: 1 }, { background: true });

print('Indexes created successfully');

// Summary
print('');
print('=== DATA GENERATION COMPLETE ===');
print('Policies: ' + db.policies.countDocuments());
print('Claims: ' + db.claims.countDocuments());
print('Active Policies: ' + db.policies.countDocuments({ policy_status: 'Active' }));
print('High Risk Claims: ' + db.claims.countDocuments({ fraud_score: { \$gte: 0.6 } }));
"

    # Verify data
    log_info "Verifying data..."

    POLICY_COUNT=$(kubectl exec -n $NAMESPACE $MONGO_POD -- mongosh \
        --username $MONGO_USER \
        --password $MONGO_PASS \
        --authenticationDatabase admin \
        --quiet \
        $MONGO_DB \
        --eval 'db.policies.countDocuments()' | tail -1)

    CLAIM_COUNT=$(kubectl exec -n $NAMESPACE $MONGO_POD -- mongosh \
        --username $MONGO_USER \
        --password $MONGO_PASS \
        --authenticationDatabase admin \
        --quiet \
        $MONGO_DB \
        --eval 'db.claims.countDocuments()' | tail -1)

    HIGH_RISK_COUNT=$(kubectl exec -n $NAMESPACE $MONGO_POD -- mongosh \
        --username $MONGO_USER \
        --password $MONGO_PASS \
        --authenticationDatabase admin \
        --quiet \
        $MONGO_DB \
        --eval 'db.claims.countDocuments({ fraud_score: { $gte: 0.6 } })' | tail -1)

    echo ""
    log_success "Data loaded successfully!"
    echo ""
    echo "Summary:"
    echo "  Policies:         $POLICY_COUNT"
    echo "  Claims:           $CLAIM_COUNT"
    echo "  High Risk Claims: $HIGH_RISK_COUNT"
    echo ""

    # Get application URL
    ALB_HOSTNAME=$(kubectl get ingress insurance-claims-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

    if [ -n "$ALB_HOSTNAME" ]; then
        echo "Access the application:"
        echo "  http://$ALB_HOSTNAME"
        echo ""
        echo "Portals:"
        echo "  Claimant:    http://$ALB_HOSTNAME/claimant"
        echo "  Adjuster:    http://$ALB_HOSTNAME/adjuster"
        echo "  SIU:         http://$ALB_HOSTNAME/siu"
        echo "  Supervisor:  http://$ALB_HOSTNAME/supervisor"
    else
        echo "Run this command to get the application URL:"
        echo "  kubectl get ingress insurance-claims-ingress -n insurance-claims"
    fi
    echo ""
}

main "$@"
