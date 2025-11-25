# AI Voice Demo Transcripts for Insurance Claims Processing System

This document contains AI voice transcripts for creating a comprehensive demo video of the AI-Powered Insurance Claims Processing system on AWS EKS.

---

## Table of Contents

1. [Introduction Script (30 seconds)](#introduction-script)
2. [System Overview (60 seconds)](#system-overview)
3. [Claimant Portal Demo (90 seconds)](#claimant-portal-demo)
4. [Adjuster Dashboard Demo (90 seconds)](#adjuster-dashboard-demo)
5. [SIU Portal Demo (60 seconds)](#siu-portal-demo)
6. [Supervisor Portal Demo (90 seconds)](#supervisor-portal-demo)
7. [Technical Architecture (60 seconds)](#technical-architecture)
8. [Closing (30 seconds)](#closing)

**Total Duration: ~8 minutes**

---

## Introduction Script

**[Screen: AWS and EKS logos with project title]**

> "Welcome to the AI-Powered Insurance Claims Processing System. This is a production-ready, cloud-native solution built on AWS Elastic Kubernetes Service that demonstrates advanced agentic AI patterns using LangGraph for intelligent, autonomous claims processing.
>
> In this demo, we'll walk through how AI agents collaborate to automate complex insurance workflows while maintaining human oversight through four specialized persona portals."

---

## System Overview

**[Screen: Portal selection page showing 4 persona cards]**

> "Our system provides four distinct portals, each tailored for different stakeholders in the claims lifecycle:
>
> First, the **Claimant Portal**, where policyholders can file new claims and track their status.
>
> Second, the **Adjuster Dashboard**, which provides claims professionals with AI-powered analysis and recommendations for reviewing and approving claims.
>
> Third, the **SIU Portal** - that's Special Investigation Unit - where fraud investigators can review high-risk claims flagged by our AI models.
>
> And finally, the **Supervisor Portal**, offering comprehensive business intelligence with KPIs like loss ratios, fraud detection rates, and processing efficiency.
>
> Let's explore each portal in detail."

---

## Claimant Portal Demo

**[Screen: Claimant portal landing page]**

> "Let's start with the Claimant Portal. This is the entry point for policyholders to interact with the claims system.
>
> **[Action: Enter policy number in login form]**
>
> First, the claimant logs in using their policy number. The system validates the policy and displays their account information.
>
> **[Screen: Claim submission form displayed]**
>
> Now they can file a new claim. Let's walk through this process:
>
> **[Action: Fill out form while narrating]**
>
> They enter their contact information - name, email, and phone number.
>
> Next, they select the claim type - let's choose 'Vehicle Accident' from the dropdown.
>
> They specify the incident details: the date of the accident, the time it occurred, and the location - including the full address, city, state, and zip code.
>
> They enter the estimated claim amount - in this case, twelve thousand five hundred dollars for vehicle repairs.
>
> Finally, they provide a detailed description of the incident: 'Rear-ended at a stoplight on Main Street. Significant damage to rear bumper and trunk. Police report filed. Other driver admitted fault.'
>
> **[Action: Click Submit]**
>
> Once submitted, the claim is instantly saved to our MongoDB database and triggered for AI processing.
>
> **[Screen: Claim confirmation page with claim ID]**
>
> The claimant receives immediate confirmation with a unique claim ID and can track their claim status at any time. The AI coordinator agent has already begun processing this claim in the background."

---

## Adjuster Dashboard Demo

**[Screen: Adjuster dashboard with claims list]**

> "Now let's switch to the Adjuster Dashboard, where claims professionals review and make decisions on submitted claims.
>
> The dashboard displays all pending claims with key metrics at the top: the number of assigned claims, urgent cases, and those pending review.
>
> **[Action: Scroll through claims list]**
>
> Each claim shows essential information: the claim ID, claimant name, claim type, amount, and current status. Let's review one of these claims in detail.
>
> **[Action: Click on a claim]**
>
> **[Screen: Detailed claim review page with AI recommendations]**
>
> Here's where the power of AI comes in. The adjuster sees the complete claim details on the left, but more importantly, they see the AI-generated analysis on the right.
>
> The AI coordinator has analyzed this claim through multiple specialized agents:
>
> The **Policy Agent** verified that the policy is active and valid, with adequate coverage for this claim type.
>
> The **Fraud Agent** ran its machine learning model and assigned a fraud score. In this case, it's 0.23 - quite low, indicating minimal fraud risk. The AI explains its reasoning: the claim aligns with historical patterns, the incident location is valid, and there's no suspicious timing.
>
> The **Risk Agent** calculated an overall risk score of 0.35 and recommends approval with standard processing.
>
> The **External Integration Agent** validated weather conditions for the incident date and confirmed no contradictions.
>
> Based on all this analysis, the AI provides a clear recommendation: **Approve** with a confidence level of 92%.
>
> **[Action: Scroll to decision section]**
>
> The adjuster reviews this AI recommendation but maintains full control. They can approve, deny, or request more information. Let's approve this claim.
>
> **[Action: Enter settlement amount and reasoning]**
>
> The adjuster enters the settlement amount - the full requested twelve thousand five hundred dollars - and adds their reasoning: 'AI analysis confirms low fraud risk. Policy coverage verified. Approving full claim amount based on documented damages and police report.'
>
> **[Action: Click Submit Decision]**
>
> The decision is recorded with full audit trail, and the claim status updates immediately. This demonstrates our human-in-the-loop pattern - AI provides intelligent recommendations, but humans make the final decisions."

---

## SIU Portal Demo

**[Screen: SIU Portal landing page]**

> "Let's now look at the Special Investigation Unit Portal, designed specifically for fraud investigators.
>
> **[Screen: High-risk claims dashboard]**
>
> The SIU dashboard automatically filters and displays only high-risk claims - those with fraud scores above 0.6. This allows investigators to focus their efforts where they're needed most.
>
> We can see the dashboard shows statistical summaries: how many high-risk claims are currently flagged, how many are under active investigation, and how many have been confirmed as fraud.
>
> **[Action: Click on a high-risk claim]**
>
> **[Screen: Investigation detail page]**
>
> Let's investigate this suspicious claim. Notice the prominent fraud alert banner highlighting the high fraud score of 0.87.
>
> The investigator sees all claim details including the unusually high claim amount and can review the AI's detailed fraud analysis. The system flagged this claim for several reasons: the claim was filed very shortly after policy inception, the amount is disproportionately high relative to the premium, and the pattern matches known fraud schemes.
>
> **[Action: Scroll to investigation actions]**
>
> The investigator has several action options: they can open a full investigation, request additional documentation from the claimant, escalate to law enforcement, or clear the claim if they determine it's legitimate.
>
> **[Action: Select action and add notes]**
>
> Let's open a full investigation. The investigator adds detailed notes about what specific aspects they'll investigate - perhaps verifying the incident with the police department and confirming the repair shop estimates.
>
> **[Action: Submit action]**
>
> Once submitted, the claim status updates to 'under investigation', and the action is logged with a full audit trail for compliance purposes."

---

## Supervisor Portal Demo

**[Screen: Supervisor portal with KPI dashboard]**

> "Finally, let's explore the Supervisor Portal, which provides comprehensive business intelligence for management and oversight.
>
> **[Screen: Primary KPIs section]**
>
> The dashboard opens with primary KPIs that matter most to insurance leadership:
>
> We see the total number of claims processed, the total exposure representing all claim amounts, the critical **Loss Ratio** - which is claims paid divided by premiums collected - currently at 64%, safely below the 70% target.
>
> The approval rate shows what percentage of processed claims are being approved, and additional operational metrics include average processing time - currently just 2.3 minutes - and AI model accuracy at an impressive 94.7%.
>
> **[Action: Scroll through sections]**
>
> **[Screen: Claims status distribution]**
>
> The status distribution section shows how claims flow through the system: how many are pending review, how many have been approved, denied, or are under investigation. Visual progress bars make it easy to spot bottlenecks.
>
> **[Screen: Fraud risk analysis section]**
>
> The fraud risk analysis breaks down claims by risk level. We can see the distribution between high-risk, medium-risk, and low-risk claims, with the average fraud score displayed prominently.
>
> **[Screen: Claims by type table]**
>
> This table shows the distribution of claims by type - vehicle accidents, property damage, theft, natural disasters, and so on - helping supervisors identify trends.
>
> **[Screen: Geographic distribution]**
>
> Geographic distribution shows where claims are originating, helping with resource allocation and identifying regional patterns.
>
> **[Screen: Financial performance section]**
>
> And finally, the financial performance section provides the bottom-line metrics: total premiums collected, approved claims payout, net underwriting profit, and the number of active policies.
>
> This comprehensive dashboard gives supervisors everything they need to monitor operations, identify issues, and make data-driven decisions."

---

## Technical Architecture

**[Screen: Architecture diagram]**

> "Now let's briefly discuss the technical architecture that powers this system.
>
> At the infrastructure level, we're running on **AWS Elastic Kubernetes Service** with EKS 1.33, providing enterprise-grade container orchestration.
>
> **Karpenter** handles intelligent node auto-scaling based on workload demands.
>
> All infrastructure is defined as code using **Terraform**, enabling repeatable, version-controlled deployments.
>
> At the application layer, we use **LangGraph** from LangChain for orchestrating our agentic AI workflows. LangGraph provides the state management and coordination between multiple specialized agents.
>
> The coordinator agent manages the workflow, delegating to specialized agents:
> - The Policy Agent for policy validation
> - The Fraud Agent with machine learning models for risk detection
> - The Risk Agent for scoring and recommendations
> - And the External Integration Agent for third-party data sources
>
> For our LLM needs, we're using **Ollama** running the Qwen 2.5 Coder 7B model locally, ensuring data privacy by keeping all claim information within our VPC.
>
> **MongoDB** serves as our primary database for claims and policy documents, while **Redis** provides caching and session management for fast response times.
>
> The web interface is built with **FastAPI**, providing high-performance REST APIs with server-side rendering using Jinja2 templates.
>
> Everything is fronted by an **AWS Application Load Balancer** that routes traffic to our Kubernetes services.
>
> This architecture is production-ready, highly scalable, and fully cloud-native."

---

## Closing

**[Screen: System overview or final dashboard view]**

> "This AI-Powered Insurance Claims Processing System demonstrates how agentic AI patterns can automate complex business processes while keeping humans in control.
>
> The system processes claims in an average of just 2.3 minutes with 94.7% accuracy, dramatically reducing the time from claim submission to resolution.
>
> Yet it maintains crucial human oversight - adjusters make final decisions, investigators handle complex fraud cases, and supervisors monitor business performance.
>
> The entire solution is open-source and available on GitHub. You can deploy it to your own AWS account with a single command, complete with sample data to explore all the features we demonstrated today.
>
> Whether you're an insurance company looking to modernize claims processing, a developer learning about agentic AI systems, or a DevOps engineer exploring Kubernetes on AWS EKS, this project provides a comprehensive, production-ready reference architecture.
>
> Thank you for watching. Visit the GitHub repository for deployment instructions, documentation, and to contribute to the project."

**[Screen: Fade to GitHub repository URL and AWS logo]**

---

## Additional Voice Direction Notes

### Tone and Pace
- **Professional and conversational**: Speak clearly but naturally
- **Medium pace**: Not too fast, allowing viewers to follow along with screen actions
- **Emphasis**: Stress key terms like "AI-powered", "production-ready", "human-in-the-loop"
- **Pauses**: Brief pauses (2-3 seconds) when transitioning between screens

### Technical Pronunciation Guide
- **EKS**: Spell out as "E-K-S" not "eks"
- **Kubernetes**: "koo-ber-NET-eez"
- **LangGraph**: "LANG-graph"
- **MongoDB**: "MON-go-D-B"
- **Redis**: "RED-iss"
- **Karpenter**: "kar-PEN-ter"
- **SIU**: Spell out as "S-I-U"
- **KPI**: Spell out as "K-P-I"

### Recording Tips
1. Record each section separately for easier editing
2. Do a complete run-through without recording first to time each section
3. Record screen captures separately and sync with voice later
4. Keep a glass of water nearby to prevent dry mouth
5. Use a pop filter to eliminate plosives (p, b, t sounds)
6. Record in a quiet environment with minimal echo

---

## Alternative Shorter Version (4-5 Minutes)

If you need a condensed version, use these sections:
1. Introduction Script (30s)
2. System Overview (45s)
3. Combined Demo: Show one claim flowing through Claimant → Adjuster → SIU (150s)
4. Supervisor Portal highlights only (60s)
5. Technical Architecture (condensed to 30s)
6. Closing (20s)

**Total: ~5 minutes**
