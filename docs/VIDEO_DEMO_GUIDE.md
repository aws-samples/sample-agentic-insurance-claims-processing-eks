# 🎬 Video Demo Guide - AI-Powered Insurance Claims Processing

## Overview

This guide helps you record a professional video demonstration of the **AI-Powered Insurance Claims Processing System** running on Amazon EKS with LangGraph agents and Ollama LLM.

## 🚀 Quick Start

### 1. Setup Video Demo

```bash
# Run the complete demo setup
./scripts/run-video-demo.sh

# If you need to rebuild the simulator
./scripts/run-video-demo.sh build
```

### 2. Access Points

- **Web Interface**: http://claims-processing-alb-1924345881.us-west-2.elb.amazonaws.com/
- **Human Review Dashboard**: http://claims-processing-alb-1924345881.us-west-2.elb.amazonaws.com/human-review
- **Claims List**: http://claims-processing-alb-1924345881.us-west-2.elb.amazonaws.com/claims
- **Simulator API**: `kubectl port-forward -n insurance-claims svc/claims-simulator-service 8091:8091`

## 📊 What's Automated

### Automated Claims Generation

The simulator **automatically generates**:
- **20 claims per minute** (customizable)
- **75% legitimate claims** - Normal insurance claims
- **25% fraudulent claims** - Various fraud patterns
- **Multiple claim types**: Auto, Property, Health, Liability, Workers Comp

### LLM-Powered Processing with Human-in-the-Loop

Each claim goes through:
1. **Coordinator Agent** - Routes the claim to specialized agents
2. **Policy Agent** - Validates against policy rules
3. **Fraud Agent** - Analyzes fraud patterns
4. **Data Enrichment** - Fetches external data (geolocation, weather, vehicle info)
5. **LLM Analysis** - Uses qwen2.5-coder:7b for intelligent analysis
6. **Human Review Queue** - AI recommendations route to human reviewers
7. **Human Decision** - Licensed adjusters make final decisions with audit trail

## 🎥 Recording the Demo

### Option 1: Automated Demo (Recommended for Video)

```bash
# In Terminal 1: Run automated claims generation
./scripts/demo-automated-claims.sh
```

This script:
- ✅ Verifies simulator health
- ✅ Shows real-time statistics
- ✅ Triggers fraud scenarios every 30 seconds
- ✅ Generates diverse claim types automatically
- ✅ Displays colorful progress updates

### Option 2: Watch Live Processing

```bash
# In Terminal 2: Watch real-time logs with color coding
./scripts/watch-demo-live.sh
```

Shows:
- 🟢 **GREEN** - Legitimate claims approved
- 🔴 **RED** - Suspicious claims flagged
- 🟡 **YELLOW** - Claims requiring investigation

### Option 3: Trigger Specific Scenarios

```bash
# Port forward to simulator
kubectl port-forward -n insurance-claims svc/claims-simulator-service 8091:8091

# Trigger staged accident ring
curl -X POST http://localhost:8091/scenario/staged_accident_ring

# Trigger serial fraudster
curl -X POST http://localhost:8091/scenario/serial_fraudster

# Trigger inflated storm claims
curl -X POST http://localhost:8091/scenario/inflated_storm_claims
```

## 🎯 Submitting Claims for Demo

### Option A: Use the Automated Simulator (Recommended)
The simulator automatically generates realistic claims with all required fields. This is the easiest approach for video demos.

### Option B: Submit Claims via Web Interface
Manually submit claims through the browser at `/` for more control over the demo narrative.

### Option C: Programmatic Submission via API
Submit claims via API calls to mimic browser submissions:

```bash
# Example: Submit a claim programmatically
curl -X POST "http://your-alb-url/submit-claim" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "customer_name=John Doe" \
  -d "customer_email=john@example.com" \
  -d "policy_number=POL-12345" \
  -d "claim_type=collision" \
  -d "incident_date=2025-10-01" \
  -d "claim_amount=15000.00" \
  -d "description=Rear-ended at intersection, significant damage to front bumper and hood"

# High-value claim (triggers Senior Adjuster review)
curl -X POST "http://your-alb-url/submit-claim" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "customer_name=Sarah Smith" \
  -d "customer_email=sarah@example.com" \
  -d "policy_number=POL-67890" \
  -d "claim_type=liability" \
  -d "incident_date=2025-10-02" \
  -d "claim_amount=125000.00" \
  -d "description=Multi-vehicle accident with injuries, potential liability issues requiring legal review"
```

**Recommendation for Video Demo**: Stick with the automated simulator as it generates diverse, realistic claims continuously, making the demo more impressive and requiring less manual intervention.

## 🎯 Fraud Detection Scenarios

### 1. Staged Accident Ring
```bash
curl -X POST http://localhost:8091/scenario/staged_accident_ring
```
- Generates 3 coordinated staged accidents in the same location
- High fraud scores (0.7-0.9)
- Shows organized fraud detection

### 2. Serial Fraudster
```bash
curl -X POST http://localhost:8091/scenario/serial_fraudster
```
- Single customer with multiple suspicious claims
- Pattern recognition across claims
- Demonstrates customer history analysis

### 3. Inflated Storm Claims
```bash
curl -X POST http://localhost:8091/scenario/inflated_storm_claims
```
- 4 claims from the same storm event
- Coordinated claim inflation
- Shows event-based fraud detection

## 📹 Suggested Video Flow

### Part 1: Introduction (30 seconds)
- Show the architecture diagram
- Explain: "AI-powered claims processing on EKS with LangGraph agents"

### Part 2: Live Demo (3-5 minutes)

1. **Show Web Interface**
   - Open: http://claims-processing-alb-1924345881.us-west-2.elb.amazonaws.com/
   - Show three main sections: Submit Claim, View Claims, Human Review Queue
   - Explain: "Full human-in-the-loop workflow with AI assistance"

2. **Start Automated Claims**
   ```bash
   ./scripts/demo-automated-claims.sh
   ```
   - Claims automatically appear in the web interface
   - Point out: "Simulator generating 20 claims/minute with diverse types"
   - Note: "Each claim type routes to appropriate human reviewer"

3. **Show AI Analysis & Fraud Detection**
   - Click on a claim to see details
   - Highlight AI recommendations section
   - Show fraud scores and risk indicators (color-coded)
   - Explain: "LLM analyzes patterns and provides recommendations - NOT decisions"

4. **Demonstrate Human Review Queue**
   - Navigate to `/human-review`
   - Select role: Claims Adjuster or SIU Investigator
   - Show pending tasks with AI recommendations
   - Explain: "AI routes high-risk claims to licensed investigators"
   - Point out:
     - Fraud scores clearly visible
     - AI recommendations shown as guidance
     - Risk factors highlighted
     - Regulatory requirements listed

5. **Make a Human Decision**
   - Review a task with high fraud score
   - Show AI recommendation (e.g., "Route to SIU for investigation")
   - Fill in reviewer ID (e.g., "adjuster_sarah_001")
   - Select decision (Approve/Deny/Investigate)
   - Add reasoning: "Based on AI analysis showing fraud score 0.85 and multiple red flags, escalating to fraud investigation team per company policy"
   - Submit decision
   - **Key Point**: "Human makes final decision - AI only provides analysis"

6. **Show Decision Recorded**
   - Navigate back to claim details
   - Show "Human Decision Recorded" section:
     - Decision type
     - Reviewer name
     - Timestamp
     - Full reasoning
   - Show audit trail section
   - Explain: "Industry-compliant audit trail for regulatory requirements"

7. **Trigger Fraud Scenario** (Optional)
   ```bash
   curl -X POST http://localhost:8091/scenario/staged_accident_ring
   ```
   - 3 coordinated suspicious claims appear
   - All automatically route to SIU Investigator queue
   - Show in Human Review Dashboard
   - Explain: "AI detects pattern across claims and routes to fraud specialists"

8. **Show Agent Processing** (Technical Deep Dive)
   - Split screen with logs: `./scripts/watch-demo-live.sh`
   - Show coordinator routing to agents
   - LLM reasoning visible in logs
   - Human workflow manager creating tasks

### Part 3: Technical Highlights (1 minute)
- Show Kubernetes pods: `kubectl get pods -n insurance-claims`
- Show Ollama deployment: `kubectl get pods -n ollama`
- Explain the architecture: LangGraph + Ollama + EKS

## 📊 Monitor During Demo

### Get Real-time Statistics

```bash
# Get simulator stats
curl -s http://localhost:8091/statistics | jq '.'

# Output:
{
  "stream_length": 10380,
  "claims_per_minute": 20,
  "fraud_rate": 0.25,
  "claims_generated": 9324,
  "active_websocket_connections": 0
}
```

### Watch Component Status

```bash
# Check all components
kubectl get pods -n insurance-claims

# Expected output:
coordinator          ✅ Running
policy-agent         ✅ Running
claims-simulator     ✅ Running
claims-web-interface ✅ Running
redis                ✅ Running
mongodb              ✅ Running
```

### Check LLM Processing

```bash
# Watch coordinator logs for LLM decisions
kubectl logs -f -n insurance-claims -l app=coordinator | grep -i "llm\|decision\|fraud"
```

## 🎨 Customization

### Adjust Claim Rate

Edit the simulator deployment:
```bash
kubectl edit deployment claims-simulator -n insurance-claims

# Add environment variable:
- name: CLAIMS_PER_MINUTE
  value: "30"  # Increase for faster demo
```

### Change Fraud Rate

```bash
# Modify in real_time_claims_simulator.py
self.fraud_rate = 0.40  # 40% fraud rate for more suspicious claims
```

### Add Custom Scenarios

Edit `applications/insurance-claims-processing/src/real_time_claims_simulator.py`:

```python
def generate_scenario_claims(self, scenario_type: str):
    if scenario_type == "your_custom_scenario":
        # Your custom logic here
        pass
```

## 🔧 Troubleshooting

### Simulator Not Generating Claims

```bash
# Check simulator logs
kubectl logs -n insurance-claims -l app=claims-simulator

# Restart if needed
kubectl rollout restart deployment/claims-simulator -n insurance-claims
```

### Claims Not Reaching Coordinator

```bash
# Check coordinator service
kubectl get svc -n insurance-claims coordinator-service

# Test connectivity
kubectl run test --rm -it --image=curlimages/curl -- \
  curl -v http://coordinator-service.insurance-claims.svc.cluster.local:8000/health
```

### No LLM Processing

```bash
# Check Ollama is running
kubectl get pods -n ollama

# Check model is loaded
kubectl exec -n ollama -it $(kubectl get pod -n ollama -l app=ollama -o jsonpath='{.items[0].metadata.name}') -- \
  ollama list
```

## 💡 Pro Tips for Video

1. **Split Screen Layout**
   - Left: Web interface showing claims
   - Right: Terminal with colorful logs

2. **Highlight Key Moments**
   - Pause when fraud scenario triggers
   - Zoom on high fraud scores
   - Show LLM reasoning in logs

3. **Performance Metrics**
   - Show claims processed per second
   - Highlight fraud detection accuracy
   - Display agent collaboration

4. **Call Out Features**
   - Real-time processing
   - Multi-agent collaboration
   - LLM-powered decisions
   - Kubernetes scalability

## 📈 Demo Statistics

After running for a while:
- **Total Claims Generated**: 9,324+
- **Fraud Detection Rate**: 25%
- **Average Processing Time**: 2-8 seconds for legitimate, 15-45 seconds for suspicious
- **Claim Types**: Auto (40%), Property (30%), Health (20%), Liability (10%)

## 🚀 Post-Demo

Stop port forwarding:
```bash
pkill -f "port-forward.*8091"
```

Keep simulator running for continuous demo:
```bash
# Simulator runs automatically, no action needed
```

Stop simulator if needed:
```bash
kubectl scale deployment claims-simulator -n insurance-claims --replicas=0
```

## 📝 Video Script Template

```
[INTRO - 30 seconds]
"Welcome to this demo of an AI-powered insurance claims processing system
running on Amazon EKS. This system uses LangGraph agents with Ollama LLM
for intelligent fraud detection with FULL human-in-the-loop oversight,
following industry-standard claims processing requirements."

[SHOW INTERFACE - 15 seconds]
"The web interface has three main sections: Submit Claims, View All Claims,
and the Human Review Dashboard. This demonstrates complete transparency in
how AI assists - but doesn't replace - human decision-making."

[AUTOMATION - 20 seconds]
"Our simulator automatically generates 20 diverse claims per minute, covering
auto, property, health, liability, and workers compensation insurance.
Each claim is analyzed by AI agents and routed to the appropriate human reviewer."

[AI ANALYSIS - 30 seconds]
"Let's look at a claim. The AI coordinator uses the LLM to analyze fraud patterns,
validates policy coverage, and enriches data from external sources. Notice the
fraud score is 0.85 - high risk. But the AI doesn't make the decision..."

[HUMAN REVIEW QUEUE - 45 seconds]
"Instead, it routes to the Human Review Dashboard. I'm logged in as an SIU
Investigator. Here's our pending task - the AI shows its analysis: fraud score,
risk indicators, and regulatory requirements. But watch carefully - the human
makes the FINAL decision."

[HUMAN DECISION - 30 seconds]
"I review the AI's recommendation. The analysis shows multiple red flags. Based
on this AI-assisted analysis and my professional judgment, I'm denying this claim
for suspected fraud. I document my reasoning here - this creates a permanent
audit trail for regulatory compliance."

[DECISION RECORDED - 20 seconds]
"Now when we view the claim details, we see the complete audit trail: who reviewed
it, when, what decision they made, and why. This is industry-standard compliance
- humans accountable for decisions, AI providing intelligent assistance."

[FRAUD SCENARIO - 30 seconds]
"Let's trigger a coordinated fraud ring. Three related claims appear - the AI
detects the pattern and automatically routes all three to fraud investigators.
This shows AI pattern recognition at scale, but still requiring human oversight."

[TECHNICAL VIEW - 20 seconds]
"Under the hood, we have LangGraph agents running on EKS, using Ollama with
qwen2.5-coder:7b - fully open-source, no proprietary LLM APIs. Everything scales
automatically with Kubernetes."

[CONCLUSION - 20 seconds]
"This demonstrates production-ready, human-supervised AI for insurance claims.
AI analyzes and recommends, humans decide and own accountability. Industry
compliance built-in from day one."
```

**Total: ~4 minutes**

## 🎯 Key Talking Points

- ✅ **Human-in-the-Loop** - AI analyzes and recommends, humans make final decisions
- ✅ **Industry Compliant** - Follows insurance industry standards with audit trails
- ✅ **Role-Based Authority** - Claims route to adjusters, investigators, underwriters based on risk/amount
- ✅ **AI-Assisted Analysis** - LangGraph agents with Ollama qwen2.5-coder:7b LLM provide intelligent recommendations
- ✅ **Full Transparency** - Every AI recommendation visible to human reviewers
- ✅ **Audit Trail** - Complete record of who decided what and why
- ✅ **Production-Ready** - Running on EKS with auto-scaling, monitoring, and resilience
- ✅ **Open Source** - No proprietary LLM APIs, fully self-hosted
- ✅ **Multi-Agent** - Coordinator, policy, fraud agents working together
- ✅ **Real-Time** - Live claim processing and fraud detection
- ✅ **Scalable** - Kubernetes-native, handles increasing load automatically
- ✅ **5 Insurance Types** - Auto, Property, Health, Liability, Workers Compensation

---

**Ready to record? Run: `./scripts/run-video-demo.sh`** 🎬
