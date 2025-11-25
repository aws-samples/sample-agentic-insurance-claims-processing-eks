# Frontend Walkthrough Guide - Persona Portals

This comprehensive guide provides step-by-step instructions for navigating and demonstrating each persona portal in the AI-Powered Insurance Claims Processing System.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Portal Selection Page](#portal-selection-page)
3. [Claimant Portal Walkthrough](#claimant-portal-walkthrough)
4. [Adjuster Dashboard Walkthrough](#adjuster-dashboard-walkthrough)
5. [SIU Portal Walkthrough](#siu-portal-walkthrough)
6. [Supervisor Portal Walkthrough](#supervisor-portal-walkthrough)
7. [Complete Demo Flow](#complete-demo-flow)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before starting the walkthrough, ensure:

1. ✅ The application is deployed and running on AWS EKS
2. ✅ You have the ALB (Application Load Balancer) URL
3. ✅ Sample data has been loaded (policies and claims)
4. ✅ All pods are in Running state

### Finding Your Application URL

```bash
# Get the ALB URL
kubectl get ingress insurance-claims -n default

# Or use this command
echo "Application URL: http://$(kubectl get ingress insurance-claims -n default -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')"
```

### Test Policy Numbers

Use these pre-loaded test policy numbers for demos:

| Policy Number | Customer Name | Line of Business | Status |
|--------------|---------------|------------------|--------|
| POL-001-2024 | John Doe | Personal Auto | Active |
| POL-002-2024 | Jane Smith | Homeowners | Active |
| POL-003-2024 | Mike Johnson | Commercial Auto | Active |

---

## Portal Selection Page

### Navigation

**URL**: `http://<ALB-URL>/`

### What You'll See

A beautifully designed landing page with four portal cards:

1. 👤 **Claimant Portal** - File claims and track status
2. 👨‍💼 **Adjuster Dashboard** - Review and approve claims
3. 🔍 **SIU Portal** - Investigate fraudulent claims
4. 📊 **Supervisor Portal** - Business analytics

### Key Features to Highlight

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Color-Coded Portals**: Each has a distinct visual identity
- **Gradient Background**: Professional purple gradient
- **Hover Effects**: Cards lift on hover for interactive feedback

### Demo Steps

1. **Open the application URL** in a web browser
2. **Point out the four portals**, explaining each role:
   - **Claimant**: Policyholders submit new claims
   - **Adjuster**: Claims professionals review and approve/deny claims
   - **SIU**: Fraud investigators examine high-risk claims
   - **Supervisor**: Management views business analytics and KPIs
3. **Hover over each card** to show the interactive effect
4. **Choose a portal** to begin the specific walkthrough

---

## Claimant Portal Walkthrough

### Step 1: Access Claimant Portal

**URL**: `http://<ALB-URL>/claimant`

**What to do**:
- Click the "Claimant Portal" card from the home page
- OR navigate directly to `/claimant`

**What you'll see**:
- Clean, focused interface with purple gradient
- Simple policy number login form
- Clear purpose: "Submit Your Insurance Claim"

### Step 2: Login with Policy Number

**What to do**:
1. Enter a test policy number: `POL-001-2024`
2. Click "Continue"

**What happens**:
- The system validates the policy in MongoDB
- Policy details are displayed with a verification checkmark
- The claim submission form appears directly below

**Key points to mention**:
> "The system validates your policy in real-time. Once verified, you can immediately submit a claim - no complicated navigation required."

### Step 3: Review Policy Verification

**What you'll see**:
- ✅ Green success banner: "Policy Verified - Your policy is active and eligible for claims"
- **Your Policy Information** section showing:
  - Policy Number
  - Coverage Type (Personal Auto, Homeowners, etc.)
  - Policy Status (✅ Active)
  - Effective Date

**What to highlight**:
> "Notice the clear verification - the system confirms your policy is active before allowing any claim submission. This prevents invalid claims from entering the system."

### Step 4: File a New Claim

#### Fill Out Claimant Information

1. **First Name**: John
2. **Last Name**: Doe
3. **Email**: john.doe@example.com
4. **Phone**: +1-555-0123

**Note**: "These fields may be pre-populated from policy data in production"

#### Select Claim Type

Click the dropdown and select one of:
- Vehicle Accident ⭐ (Recommended for demo)
- Property Damage
- Theft
- Natural Disaster (Flood)
- Natural Disaster (Hurricane)
- Fire Damage
- Vandalism
- Other

**Demo Tip**: Use "Vehicle Accident" as it's most relatable

#### Enter Incident Details

1. **Incident Date**: Select yesterday's date
2. **Incident Time**: 14:30 (2:30 PM)
3. **Loss Location**: `123 Main Street`
4. **City**: `San Francisco`
5. **State**: `CA`
6. **ZIP Code**: `94102`

**What to say**:
> "The system captures complete incident details for accurate processing and fraud detection"

#### Specify Claim Amount

**Amount**: `12500.00`

**What to say**:
> "Enter the estimated damage amount. The AI will verify this against policy coverage limits and historical patterns"

#### Provide Description

**Sample Description**:
```
I was stopped at a red light on Main Street when another vehicle rear-ended
me. The impact caused significant damage to my rear bumper, trunk, and
taillights. The other driver admitted fault at the scene. I filed a police
report (Report #2024-1234) and have photos of the damage. My vehicle is
currently at Joe's Auto Repair for estimate.
```

**Key points**:
- Detailed narrative
- Mentions police report
- References documentation
- Provides repair shop info

### Step 5: Submit the Claim

**What to do**:
1. Review all entered information
2. Click the "Submit Claim" button
3. Wait for processing (1-2 seconds)

**What happens**:
- Claim is saved to MongoDB
- Unique claim ID is generated (format: `CLM-YYYYMMDD-XXXXXXXX`)
- Coordinator agent is triggered for AI processing in the background
- Redirect to confirmation page

### Step 6: View Claim Confirmation

**What you'll see**:
- ✅ Green success banner: "Claim Submitted Successfully!"
- "← Back to Home" link at the top of the card
- Unique claim ID prominently displayed
- Status badge showing "Submitted"
- All claim details in a clean card layout
- Submission timestamp
- Two navigation buttons at the bottom:
  - **← Home** (gray button) - returns to portal selection
  - **File Another Claim** (purple button) - returns to claimant form

**What to emphasize**:
> "The claimant receives immediate confirmation with a claim ID they can use to track progress. Meanwhile, our AI agents are already analyzing this claim in the background. Notice the clear navigation options - they can return to the home page or file another claim directly."

**Screenshot opportunity**: This is a great screen for documentation

### Step 7: Next Steps in the Demo Flow

**What to do**:
- Note the claim ID for reference
- Click "← Home" button or the home link to return to portal selection
- **Transition to Adjuster Dashboard** to show how this claim is processed

**What to say**:
> "The claimant has successfully submitted their claim and received a unique claim ID. In a production system, they would receive email/SMS notifications as the claim progresses. Now let's see how our AI-powered system processes this claim from the adjuster's perspective."

**For demo purposes**:
- The claim is now in the system with status "submitted"
- AI agents are processing it in the background
- The adjuster will see it appear in their queue within seconds

---

## Adjuster Dashboard Walkthrough

### Step 1: Access Adjuster Dashboard

**URL**: `http://<ALB-URL>/adjuster`

**What to do**:
- Click "Adjuster Dashboard" from home page
- OR navigate directly to `/adjuster`

**What you'll see**:
- Professional dashboard with claims list
- Summary statistics at the top
- Table of pending claims

### Step 2: Review Dashboard Statistics

**Statistics shown**:
- **Assigned Claims**: Total claims for this adjuster
- **Urgent Claims**: High-priority cases
- **Pending Review**: Awaiting adjuster decision
- **Completed Today**: Daily productivity metric

**What to say**:
> "Adjusters see their workload at a glance. The dashboard prioritizes their attention on urgent cases requiring immediate review"

### Step 3: Browse Claims List

**What you'll see** in the table:
- Claim ID (clickable)
- Claimant Name
- Claim Type
- Claim Amount
- Status
- Submission Date
- Priority indicators (if any)

**What to do**:
- Scroll through the list
- Point out different claim types and amounts
- Note status indicators

**What to highlight**:
> "All pending claims are displayed in one place. Adjusters can quickly scan and prioritize their review queue"

### Step 4: Select a Claim for Review

**What to do**:
- Click on the claim ID of the claim you just created
- OR select any claim with status "submitted" or "pending_review"

**Transition statement**:
> "Let's review this claim in detail and see what insights our AI agents provide"

### Step 5: Review Claim Details

**What you'll see** (left side of screen):

#### Claim Information
- Claim ID
- Policy Number
- Claimant Name & Contact Info
- Claim Type
- Incident Date
- Location (full address)
- Claim Amount
- Status
- Description (full narrative)

**What to do**:
- Read through the claim details
- Point out key information like amount and description

### Step 6: Analyze AI Recommendations

**What you'll see** (right side or below claim details):

#### AI Analysis Section

1. **Overall Recommendation**
   - Approve / Investigate / Deny
   - Confidence Score (e.g., 92%)
   - Color-coded badge (Green=Approve, Yellow=Investigate, Red=Deny)

2. **Policy Validation** (from Policy Agent)
   - ✅ Policy Status: Active
   - ✅ Coverage Valid: Yes
   - ✅ Coverage Limit: $25,000
   - ✅ Deductible: $500
   - ✅ Claim within policy period

3. **Fraud Analysis** (from Fraud Agent)
   - **Fraud Score**: 0.23 (Low Risk)
   - **Risk Factors**:
     - ✅ Clean claims history
     - ✅ Reasonable amount for claim type
     - ✅ Valid incident location
     - ✅ Appropriate timing (not suspicious)
   - **Explanation**: "This claim exhibits normal patterns consistent with legitimate vehicle accident claims. No red flags detected."

4. **Risk Assessment** (from Risk Agent)
   - **Risk Score**: 0.35 (Low-Medium)
   - **Factors Analyzed**:
     - Claim-to-premium ratio: Normal
     - Geographic risk: Low
     - Historical data: Consistent
   - **Recommendation**: Approve with standard processing

5. **External Verification** (from External Integration Agent)
   - ✅ Weather conditions: Clear (no contradictions)
   - ✅ Location validated: Real address
   - ℹ️ Police report reference noted
   - ✅ No conflicting external data

**What to emphasize**:
> "The AI coordinator has analyzed this claim through four specialized agents, each providing expert analysis:
> - Policy Agent confirms coverage
> - Fraud Agent calculates risk with ML models
> - Risk Agent provides overall scoring
> - External Agent validates against third-party data
>
> All of this analysis happens in about 2-3 minutes, but the adjuster maintains full control of the final decision"

### Step 7: Make Adjuster Decision

#### Scroll to Decision Section

**What you'll see**:
- Radio buttons or dropdown for decision: Approve / Deny / Request More Info
- Settlement Amount field
- Reasoning text area
- Adjuster ID field
- Submit Decision button

#### For Approval Demo

**What to do**:
1. Select **"Approve"**
2. Enter **Settlement Amount**: `12500.00` (or different if negotiated)
3. Enter **Reasoning**:
   ```
   AI analysis confirms low fraud risk (0.23). Policy coverage verified with
   adequate limits. Claim amount reasonable for reported damages. Police
   report referenced. Approving full requested amount.
   ```
4. Enter **Adjuster ID**: `ADJ001` (or your demo ID)
5. Click **"Submit Decision"**

**What happens**:
- Decision is saved to database
- Claim status updates to "approved" (or "denied")
- Settlement amount is recorded
- Full audit trail is created
- Timestamp and adjuster ID logged
- Redirect back to adjuster dashboard

**What to say**:
> "The adjuster has full authority to approve, deny, or modify the settlement amount based on their expertise. The AI provides recommendations, but humans make the final call - this is our human-in-the-loop pattern"

#### For Denial Demo (Alternative)

If you want to demo a denial:
1. Select **"Deny"**
2. Leave Settlement Amount blank
3. Enter **Reasoning**:
   ```
   Policy deductible not met. Damages estimated below $500 deductible threshold.
   Advised claimant to handle repairs directly.
   ```
4. Enter **Adjuster ID**: `ADJ001`
5. Click **"Submit Decision"**

### Step 8: View Updated Dashboard

**What you'll see**:
- Return to adjuster dashboard
- Claim removed from "pending" list (moved to completed)
- Statistics updated
- Success message (optional)

**What to say**:
> "The claim is now processed and removed from the pending queue. The claimant would receive notification of the decision through the system"

---

## SIU Portal Walkthrough

### Step 1: Access SIU Portal

**URL**: `http://<ALB-URL>/siu`

**What to do**:
- Click "SIU Portal" from home page
- OR navigate directly to `/siu`

**What you'll see**:
- Professional dashboard with red/warning color scheme
- 🔍 Special Investigation Unit branding
- High-risk claims statistics
- List of suspicious claims

### Step 2: Review SIU Dashboard Statistics

**Statistics shown**:
- **High Risk Claims**: Count of claims with fraud score > 0.6
- **Under Investigation**: Active investigations
- **Confirmed Fraud**: Cases confirmed as fraudulent

**What to say**:
> "The SIU portal automatically filters for high-risk claims, allowing investigators to focus their expertise where it matters most. Our AI fraud detection model flags suspicious patterns for human review"

### Step 3: Browse High-Risk Claims

**What you'll see**:
Each claim card displays:
- Claim ID
- Claimant Name
- Claim Type & Amount
- **Fraud Score** (prominently displayed in large red text)
- "Investigate" button

**What to do**:
- Scroll through the list
- Point out the fraud scores
- Note the automatic flagging

**What to highlight**:
> "Claims are automatically ranked by fraud risk. Scores above 0.6 are considered high risk and require investigation"

### Step 4: Investigate a High-Risk Claim

**What to do**:
- Click "Investigate" on a claim with high fraud score (e.g., 0.87)

**What you'll see**:

#### Fraud Alert Banner
- ⚠️ High Fraud Risk Detected
- Large fraud score display
- Red/warning styling

#### Claim Details Section
- All standard claim information
- Claimant contact details
- Policy number
- Claim amount (often suspiciously high)
- Description

#### AI Fraud Analysis Section
Detailed breakdown:
- **Fraud Score**: 0.87
- **Risk Factors Identified**:
  - ⚠️ Policy inception date very recent (suspicious timing)
  - ⚠️ Claim amount disproportionate to premium
  - ⚠️ Pattern matches known fraud schemes
  - ⚠️ Unusual claim frequency for policyholder
  - ⚠️ Description contains contradictions

**What to say**:
> "Our machine learning fraud detection model has identified multiple red flags. The AI doesn't make the final call, but it ensures investigators know exactly what to look for"

### Step 5: Take Investigation Action

**What you'll see**:
Investigation actions dropdown with options:
- Open Full Investigation
- Request Additional Documents
- Escalate to Law Enforcement
- Clear - No Fraud Detected

**Investigation Notes** text area for detailed documentation

#### Demo: Open Full Investigation

**What to do**:
1. Select **"Open Full Investigation"**
2. Enter **Investigation Notes**:
   ```
   Opened formal investigation based on high fraud indicators. Actions to take:
   1. Verify incident with local police department (confirm report #)
   2. Contact repair shop to validate estimates
   3. Review claimant's prior claims history across all insurers
   4. Analyze timeline of policy purchase vs. incident
   5. Request original repair invoices and receipts

   Expected investigation time: 7-10 business days
   Lead Investigator: INV-042
   ```
3. Click **"Submit Investigation Action"**

**What happens**:
- Claim status updates to "under_investigation"
- Investigation notes saved with timestamp
- SIU action logged for audit trail
- Alert sent to relevant parties (in production)
- Redirect to SIU dashboard

#### Alternative Demo: Request Documents

**What to do**:
1. Select **"Request Additional Documents"**
2. Enter notes:
   ```
   Requesting the following documents from claimant:
   - Copy of police report
   - Photos of vehicle damage (all angles)
   - Original repair estimates from two shops
   - Proof of vehicle ownership
   Due date: 5 business days
   ```
3. Click **"Submit Investigation Action"**

### Step 6: View Updated SIU Dashboard

**What to say**:
> "The case is now flagged as under investigation. In production, the claimant would be notified of the additional review, and the claim is temporarily held until investigation completes"

---

## Supervisor Portal Walkthrough

### Step 1: Access Supervisor Portal

**URL**: `http://<ALB-URL>/supervisor`

**What to do**:
- Click "Supervisor Portal" from home page
- OR navigate directly to `/supervisor`

**What you'll see**:
- Comprehensive business intelligence dashboard
- Professional blue gradient header
- Multiple sections with KPIs and metrics

### Step 2: Review Primary KPIs

**What you'll see** (top row of cards):

1. **Total Claims**
   - Large number display
   - "Last 30 days" indicator
   - Blue color scheme

2. **Total Exposure**
   - Dollar amount (sum of all claims)
   - Purple color scheme
   - "Claim amounts" label

3. **Loss Ratio** ⭐ Most Important
   - Percentage (e.g., 64.2%)
   - Green if < 70%, Red if > 70%
   - "Below/Above target (70%)" indicator

4. **Approval Rate**
   - Percentage of claims approved
   - "X of Y processed" detail
   - Green color scheme

**What to say**:
> "The supervisor dashboard opens with the metrics that matter most to insurance leadership. The Loss Ratio is particularly critical - it shows claims paid versus premiums collected. Below 70% is healthy; above that indicates the company may be losing money"

**Demo tip**:
- Hover over cards to show interactive effects
- Point out color coding (green = good, red = needs attention)

### Step 3: Review Operational Metrics

**What you'll see** (second row):

1. **Average Processing Time**
   - Time in minutes (e.g., 2.3 min)
   - "↓ 15% from last month" trend indicator
   - Orange/yellow color

2. **AI Accuracy**
   - Percentage (e.g., 94.7%)
   - "Confidence: 85%" detail
   - Cyan/blue color

3. **Fraud Detection Rate**
   - Percentage of claims flagged as high risk
   - Count of high-risk claims
   - Red color scheme

4. **Average Claim Amount**
   - Dollar amount per claim
   - "Per claim average" label
   - Indigo color

**What to emphasize**:
> "These operational metrics show the efficiency and effectiveness of our AI-powered system. Processing time of 2.3 minutes per claim versus days or weeks in traditional systems. AI accuracy at 94.7% demonstrates the reliability of our automated analysis"

### Step 4: Analyze Claims Status Distribution

**What you'll see**:
Section with 4 cards showing:
- **Pending Review**: Count + progress bar (orange)
- **Approved**: Count + progress bar (green)
- **Denied**: Count + progress bar (red)
- **Under Investigation**: Count + progress bar (purple)

Each has a progress bar showing percentage of total

**What to do**:
- Point out the visual progress bars
- Explain the claim lifecycle
- Note any bottlenecks (e.g., too many pending)

**What to say**:
> "This shows where claims are in the workflow. Supervisors can quickly identify bottlenecks - for example, if too many claims are stuck in 'pending review', they might need to allocate more adjuster resources"

### Step 5: Review Fraud Risk Analysis

**What you'll see**:
Section with 4 cards:
- **High Risk (>0.6)**: Count + red progress bar
- **Medium Risk (0.3-0.6)**: Count + orange progress bar
- **Low Risk (<0.3)**: Count + green progress bar
- **Average Fraud Score**: Decimal value + blue progress bar

**What to highlight**:
> "Our fraud detection model segments claims by risk level. This helps SIU investigators prioritize their workload and shows management the overall fraud exposure"

**Demo tip**: Point out if fraud rate is higher than expected (e.g., > 10%)

### Step 6: Explore Claims by Type

**What you'll see**:
Professional data table with columns:
- Claim Type
- Count
- Percentage
- Distribution (visual progress bar)

**Common claim types**:
- Vehicle Accident
- Property Damage
- Theft
- Natural Disaster (Flood)
- Natural Disaster (Hurricane)
- Fire Damage
- Vandalism
- Other

**What to do**:
- Scroll through the table
- Point out the distribution
- Note any anomalies

**What to say**:
> "Understanding claim distribution by type helps with resource planning, risk assessment, and identifying trends. For example, a spike in natural disaster claims might indicate a recent weather event"

### Step 7: Review Geographic Distribution

**What you'll see**:
"Top 5 Claims by Location" section with cards for each location:
- State/Region name
- Count of claims
- Progress bar showing percentage

**What to highlight**:
> "Geographic analysis helps identify regional patterns, allocate claims adjusters by region, and understand exposure by location. This is crucial for risk management and pricing models"

### Step 8: Analyze Financial Performance

**What you'll see**:
Section with 4 key financial metrics:

1. **Total Premiums Collected**
   - Dollar amount
   - Revenue side of the equation

2. **Approved Claims Payout**
   - Dollar amount
   - Expense side

3. **Net Underwriting Profit**
   - Dollar amount (Premiums - Payouts)
   - Green if positive, Red if negative

4. **Active Policies**
   - Count of policies
   - Revenue base

**What to emphasize**:
> "This is the financial health of the insurance operation at a glance. Net underwriting profit shows whether the company is making money on its insurance policies before investment income"

**Demo tip**: Calculate quick ratios:
- "So we collected $X in premiums, paid out $Y in claims, for a net profit of $Z"
- "That's a loss ratio of __%, which is [good/concerning]"

### Step 9: Review System Status

**What you'll see** (bottom section):
- ● Green badge: "AI-Powered Agentic Claims Processing is Operational"
- System metrics:
  - Avg Processing Time: 2.3 min
  - AI Model Accuracy: 94.7%
  - Total Processed: [count]
  - System Uptime: 99.2%

**What to say**:
> "Finally, system health metrics confirm everything is running smoothly. In production, these would update in real-time and trigger alerts if any metrics fall below thresholds"

### Step 10: Review Timestamp

**What you'll see** (very bottom):
- "Last updated: [timestamp]"
- Footer text

**What to say**:
> "The dashboard shows the last update time. In production, this could refresh automatically every few minutes to provide real-time insights"

---

## Complete Demo Flow

### Recommended Full Demo Sequence (20-25 minutes)

Follow this sequence to tell a complete story:

#### Act 1: The Claim (5 minutes)
1. Start at **Portal Selection Page**
2. Access **Claimant Portal**
3. Login with policy number
4. File a complete claim (vehicle accident)
5. Show confirmation page
6. **Key message**: "Easy for policyholders to file claims digitally"

#### Act 2: The Analysis (8 minutes)
7. Return to home, access **Adjuster Dashboard**
8. Locate the newly filed claim
9. Review claim details thoroughly
10. **Deep dive** into AI recommendations:
    - Policy validation
    - Fraud analysis (emphasize ML model)
    - Risk scoring
    - External verification
11. Make approval decision with reasoning
12. **Key message**: "AI provides intelligent recommendations; humans maintain control"

#### Act 3: The Investigation (5 minutes)
13. Return to home, access **SIU Portal**
14. Review high-risk claims dashboard
15. Investigate one suspicious claim
16. Show detailed fraud analysis
17. Open investigation with notes
18. **Key message**: "ML-powered fraud detection protects the company"

#### Act 4: The Business View (7 minutes)
19. Return to home, access **Supervisor Portal**
20. Walk through all KPI sections:
    - Primary KPIs (emphasize loss ratio)
    - Operational metrics (emphasize AI accuracy)
    - Status distribution
    - Fraud analysis
    - Claims by type
    - Geographic distribution
    - Financial performance
21. **Key message**: "Comprehensive BI for data-driven management decisions"

#### Closing (2 minutes)
22. Return to **Portal Selection Page**
23. Summarize the four personas and their roles
24. Highlight key benefits:
    - ⚡ Fast processing (2.3 min vs. days)
    - 🤖 AI-powered with 94.7% accuracy
    - 👥 Human oversight maintained
    - 📊 Complete transparency and analytics
    - 🛡️ Advanced fraud detection
25. Mention the technical stack (EKS, LangGraph, MongoDB, Redis)
26. Invite questions

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Policy not found" error
**Solution**:
- Ensure sample data has been loaded: `./scripts/load-data.sh`
- Use a valid policy number from the database
- Check MongoDB connection: `kubectl logs -n default deployment/web-interface`

#### Issue: Claims list is empty
**Solution**:
- Load sample claims: `./scripts/load-data.sh --claims 100`
- Check MongoDB: `kubectl exec -it deployment/mongodb -n default -- mongosh`
- Verify coordinator service is running: `kubectl get pods -n default`

#### Issue: AI recommendations not showing
**Solution**:
- Check if coordinator processed the claim: `kubectl logs -n default deployment/coordinator-agent`
- Verify Ollama is running: `kubectl get pods -n default | grep ollama`
- Check claim status in database (should be "pending_review" not "submitted")

#### Issue: Fraud scores are all 0 or missing
**Solution**:
- Ensure the fraud detection model is loaded
- Check coordinator logs for errors during fraud analysis
- Verify sample data includes fraud scores

#### Issue: Dashboard metrics show 0
**Solution**:
- Ensure data has been loaded
- Check MongoDB connection from web interface
- Refresh the page (metrics are calculated on page load)

#### Issue: Images/styles not loading
**Solution**:
- Check that static files are mounted correctly
- Verify Ingress is configured properly
- Test direct pod access: `kubectl port-forward deployment/web-interface 8080:8000`

### Testing Checklist

Before a demo, verify:

- [ ] All 4 pods are running (web, coordinator, mongodb, redis)
- [ ] ALB URL is accessible
- [ ] Portal selection page loads
- [ ] At least one test policy exists
- [ ] Can submit a new claim
- [ ] Adjuster dashboard shows claims
- [ ] SIU portal shows high-risk claims (at least 1)
- [ ] Supervisor dashboard shows non-zero metrics
- [ ] Navigation works between all portals

### Emergency Demo Recovery

If something breaks during demo:

1. **Stay calm and acknowledge it**: "In a live system, we occasionally see timing issues. Let me show you [alternative]"

2. **Have screenshots ready**: Keep screenshots of all portals in case live demo fails

3. **Use alternative claims**: If one claim isn't working, use another from the list

4. **Skip to another portal**: The portals are independent; if Claimant fails, jump to Adjuster

5. **Fall back to architecture**: Explain the architecture and design instead of live demo

---

## Additional Resources

### For Presenters

- **Practice run**: Do a complete walkthrough before any demo
- **Timing**: Full demo is 20-25 minutes; budget 30 minutes with questions
- **Audience adaptation**:
  - Technical audience: Deep dive on AI agents, LangGraph, K8s
  - Business audience: Focus on KPIs, ROI, process improvement
  - Executive audience: Show Supervisor portal, highlight loss ratio and efficiency

### For Technical Setup

- **Network access**: Ensure demo machine can access ALB URL
- **Browser**: Use Chrome or Firefox (latest versions)
- **Screen resolution**: 1920x1080 minimum for good visibility
- **Zoom level**: 100% or 110% for presentations
- **Clear cache**: Clear browser cache before critical demos

### Key Talking Points by Audience

**For Insurance Executives**:
- Loss ratio improvement
- Fraud detection ROI
- Processing time reduction
- Cost per claim
- Customer satisfaction (faster turnaround)

**For IT/DevOps Leaders**:
- Cloud-native architecture on AWS EKS
- Container orchestration with Kubernetes
- Infrastructure as Code with Terraform
- Scalability and high availability
- Security best practices

**For Data Scientists/ML Engineers**:
- LangGraph agentic framework
- Multi-agent coordination patterns
- ML fraud detection models
- Local LLM deployment (Ollama)
- Model accuracy and confidence metrics

**For Product Managers**:
- User experience across personas
- Workflow automation
- Human-in-the-loop design
- Business intelligence dashboard
- Integration points

---

## Conclusion

This walkthrough guide provides everything you need to confidently demonstrate the AI-Powered Insurance Claims Processing System. The key is to tell a story:

1. **Claimant** files a claim (ease of use)
2. **Adjuster** reviews with AI help (intelligent automation)
3. **SIU** investigates suspicious claims (fraud protection)
4. **Supervisor** monitors the business (data-driven leadership)

Each persona portal showcases a different aspect of the system, together demonstrating a complete, production-ready solution for modern insurance claims processing.

Happy demoing! 🎉
