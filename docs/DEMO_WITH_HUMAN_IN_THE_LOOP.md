# 🎬 Complete Demo Guide - Human-in-the-Loop Insurance Claims Processing

## 🚀 Quick Start

```bash
# Setup and verify demo
./scripts/run-video-demo.sh

# Get your ALB URL
kubectl get ingress claims-processing-ingress -n insurance-claims -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## 📍 Access Points

Your system has **three main interfaces**:

1. **Main Portal** - `http://your-alb-url/`
   - Submit new claims via web form

2. **Claims List** - `http://your-alb-url/claims`
   - View all submitted claims
   - Click any claim to see full details with AI analysis

3. **Human Review Dashboard** - `http://your-alb-url/human-review` ⭐ **NEW!**
   - View pending tasks for different roles
   - See AI recommendations
   - Make human decisions with audit trail

## 🎯 Demo Options

### Option 1: Automated Simulator (Recommended)

**Best for:** Impressive continuous demo, minimal manual work

```bash
# Start automated claims generation
./scripts/demo-automated-claims.sh
```

- Generates 20 claims/minute automatically
- 75% legitimate, 25% fraudulent
- All 5 insurance types covered
- Claims appear in real-time on web interface

### Option 2: Submit Demo Claims via Script

**Best for:** Controlled narrative, specific claim examples

```bash
# Submit 6 pre-defined demo claims
./scripts/submit-demo-claims.sh
```

Submits:
- Low-value auto claim ($5,500) → Claims Adjuster
- Medium property claim ($28,000) → Claims Adjuster
- High-value liability ($125,000) → Senior Adjuster
- Health claim ($15,000) → Claims Adjuster
- Workers comp ($32,000) → Claims Adjuster
- **Suspicious claim ($45,000)** → SIU Investigator

### Option 3: Manual Browser Submission

**Best for:** Live audience interaction, custom scenarios

1. Go to `http://your-alb-url/`
2. Fill out the claim form
3. Submit and watch it process

### Option 4: Programmatic API Calls

**Best for:** Scripted demos, CI/CD testing

```bash
curl -X POST "http://your-alb-url/submit-claim" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "customer_name=Jane Doe" \
  -d "customer_email=jane@example.com" \
  -d "policy_number=POL-99999" \
  -d "claim_type=collision" \
  -d "incident_date=2025-10-03" \
  -d "claim_amount=75000.00" \
  -d "description=Suspicious multi-vehicle collision with conflicting witness statements"
```

## 🎥 Recommended Demo Flow (4-5 minutes)

### Step 1: Introduction (30 seconds)
- Open browser to main portal
- Show three navigation links
- Explain: "Human-in-the-loop AI with full transparency"

### Step 2: Start Claims Processing (15 seconds)
```bash
./scripts/demo-automated-claims.sh
# OR
./scripts/submit-demo-claims.sh
```

### Step 3: Show AI Analysis (45 seconds)
- Navigate to `/claims`
- Click on any claim
- Highlight:
  - **AI Recommendation** section (blue background)
  - Fraud score (color-coded)
  - External data enrichment
  - Risk indicators
- **Key point**: "AI provides analysis, NOT decisions"

### Step 4: Human Review Dashboard (1 minute)
- Navigate to `/human-review`
- Select role: **SIU Investigator** (shows high-risk claims)
- Show task card:
  - Claim details
  - AI analysis with fraud score
  - Risk factors
  - Regulatory requirements
  - **AI recommendation** prominently displayed
- **Key point**: "Human reviewer sees all AI analysis as guidance"

### Step 5: Make Human Decision (1 minute)
- Fill in reviewer ID: `investigator_sarah_001`
- Select decision: **Deny**
- Add reasoning:
  ```
  Based on AI fraud score of 0.87 and multiple red flags including:
  - Policy inception 2 days before claim
  - No police report
  - Abandoned vehicle

  Denying claim per fraud investigation protocols.
  Recommend referral to law enforcement.
  ```
- Click **Submit Decision**
- **Key point**: "Human makes final call with full accountability"

### Step 6: Show Decision Recorded (30 seconds)
- Click "View Claims" to go back to claims list
- Click on the same claim
- Show **Human Decision Recorded** section:
  - Decision: DENY
  - Reviewed by: investigator_sarah_001
  - Timestamp
  - Full reasoning
- Show **Audit Trail** section
- **Key point**: "Complete regulatory compliance with audit trail"

### Step 7: Fraud Scenario (Optional - 1 minute)
```bash
# Port forward to simulator
kubectl port-forward -n insurance-claims svc/claims-simulator-service 8091:8091

# In another terminal
curl -X POST http://localhost:8091/scenario/staged_accident_ring
```

- 3 coordinated fraud claims appear
- Navigate to `/human-review?role=siu_investigator`
- Show all 3 tasks in queue
- **Key point**: "AI detects patterns across claims, routes to specialists"

### Step 8: Technical Deep Dive (Optional - 1 minute)
```bash
# Show Kubernetes components
kubectl get pods -n insurance-claims

# Show coordinator logs
kubectl logs -n insurance-claims -l app=coordinator --tail=50

# Show Ollama model
kubectl exec -n insurance-claims deployment/ollama -- ollama list
```

## 🎯 Key Messages to Emphasize

### Primary Message
**"AI analyzes and recommends, humans decide and are accountable"**

### Supporting Points
1. ✅ **Industry Compliant** - Follows insurance regulatory requirements
2. ✅ **Full Transparency** - Every AI recommendation visible to humans
3. ✅ **Authority Limits** - Claims route based on amount and risk
4. ✅ **Audit Trail** - Complete record for compliance
5. ✅ **Open Source** - Self-hosted LLM, no proprietary APIs
6. ✅ **Production Ready** - Running on EKS with auto-scaling

### What This Demo Shows
- ✅ 5 Insurance Types (Auto, Property, Health, Liability, Workers Comp)
- ✅ Multi-Agent AI Analysis (Coordinator, Policy, Fraud agents)
- ✅ LLM-Powered Recommendations (Ollama qwen2.5-coder:7b)
- ✅ Human Review Workflow (Role-based queues)
- ✅ Decision Authority Validation (Settlement limits per role)
- ✅ Regulatory Compliance (Audit trails, deadlines)
- ✅ Real-Time Processing (20 claims/minute)

### What This Demo Does NOT Show
- ❌ AI making autonomous decisions without human oversight
- ❌ Black-box AI (all analysis is transparent)
- ❌ Humans as passive observers (they're decision-makers)

## 📝 Script Template

```
[HOOK - 10 seconds]
"Can AI replace insurance claims adjusters? No - but it can make them
10x more effective. Let me show you how."

[INTERFACE TOUR - 20 seconds]
"This is a production-ready claims system running on AWS EKS. Three main
sections: submit claims, view all claims, and - critically - the human
review dashboard where final decisions happen."

[AI ANALYSIS - 30 seconds]
"When a claim comes in, our LangGraph agents analyze it using an open-source
LLM. Look at this claim - fraud score 0.87, multiple red flags detected.
The AI has done deep analysis: cross-referenced fraud databases, checked
weather data, validated policy coverage. But notice what it DOESN'T do..."

[HUMAN DECISION - 45 seconds]
"It doesn't decide. Instead, it routes to this human review queue. I'm
logged in as an SIU investigator. Here's the pending task. I can see
everything the AI found - the fraud score, the risk factors, the
recommendations. But I'm making the final call. Based on the AI's analysis
AND my professional judgment, I'm denying this claim for fraud. I document
my reasoning here - this creates a permanent, auditable record."

[AUDIT TRAIL - 20 seconds]
"Now when anyone looks at this claim, they see exactly who decided what
and why. This isn't just good practice - it's required by insurance
regulators. The AI analyzed, I decided, the system recorded everything."

[SCALE DEMO - 30 seconds]
"Let me trigger a fraud ring scenario. Three coordinated claims just
appeared. The AI detected the pattern across all three and automatically
routed them to fraud investigators. This is AI pattern recognition at
scale - but still requiring human oversight."

[CLOSE - 20 seconds]
"This is the future of insurance claims: AI handling the analysis at
machine scale, humans maintaining decision authority and accountability.
Industry compliant, fully transparent, production ready on Kubernetes."
```

**Total: ~3 minutes**

## 🛠️ Troubleshooting

### No claims appearing in web interface
```bash
# Check web interface logs
kubectl logs -n insurance-claims -l app=claims-web-interface --tail=50

# Check coordinator logs
kubectl logs -n insurance-claims -l app=coordinator --tail=50

# Verify services
kubectl get svc -n insurance-claims
```

### Human review dashboard empty
Claims only route to human review if:
1. They have a fraud score > 0.4, OR
2. Claim amount > $10,000, OR
3. Policy issues detected

**Solution**: Submit a high-value or suspicious claim

### Can't access ALB URL
```bash
# Get correct URL
kubectl get ingress claims-processing-ingress -n insurance-claims

# Check ALB is provisioned
kubectl describe ingress claims-processing-ingress -n insurance-claims
```

## 📊 Demo Statistics

After running the simulator for 10 minutes:
- **Claims Processed**: ~200
- **Fraud Detection Rate**: ~25%
- **Claims by Type**:
  - Auto: 40%
  - Property: 30%
  - Health: 20%
  - Liability: 7%
  - Workers Comp: 3%
- **Human Tasks Created**: ~50-60
- **Average Processing Time**: 2-8 seconds per claim

## 🎬 Ready to Record?

```bash
./scripts/run-video-demo.sh
```

Then open: `http://your-alb-url/`

**Key Message**: AI recommends, Humans decide! 🤖🤝👨‍💼
