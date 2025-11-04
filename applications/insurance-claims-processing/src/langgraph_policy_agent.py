"""
LangGraph Policy Analysis Agent - Industry Standard Underwriter Integration
AI-assisted policy analysis with mandatory underwriter approval for coverage decisions
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import operator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State definition for policy validation workflow
class PolicyState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    claim_data: Dict[str, Any]
    policy_data: Dict[str, Any]
    validation_results: Dict[str, Any]
    coverage_analysis: Dict[str, Any]
    compliance_check: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    final_recommendation: Optional[Dict[str, Any]]
    reasoning_chain: List[str]
    confidence_score: float

@tool
def validate_policy_existence(policy_number: str, claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if policy exists and is active."""
    # Simulate policy lookup (replace with actual database query)
    policy_exists = len(policy_number) > 5  # Simple simulation
    
    if policy_exists:
        return {
            "policy_exists": True,
            "policy_status": "active",
            "effective_date": "2023-01-01",
            "expiration_date": "2024-12-31",
            "premium_status": "current"
        }
    else:
        return {
            "policy_exists": False,
            "error": "Policy not found in system"
        }

@tool
def check_coverage_limits(claim_amount: float, policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check if claim amount is within policy coverage limits."""
    policy_limit = policy_data.get("coverage_limit", 100000)
    deductible = policy_data.get("deductible", 1000)
    
    covered_amount = min(claim_amount - deductible, policy_limit)
    coverage_percentage = (covered_amount / claim_amount) * 100 if claim_amount > 0 else 0
    
    return {
        "claim_amount": claim_amount,
        "policy_limit": policy_limit,
        "deductible": deductible,
        "covered_amount": max(0, covered_amount),
        "coverage_percentage": coverage_percentage,
        "within_limits": claim_amount <= policy_limit + deductible,
        "excess_amount": max(0, claim_amount - policy_limit - deductible)
    }

@tool
def validate_claim_type_coverage(claim_type: str, policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if claim type is covered under the policy."""
    covered_perils = policy_data.get("covered_perils", [
        "collision", "comprehensive", "liability", "medical", "uninsured_motorist"
    ])
    
    exclusions = policy_data.get("exclusions", ["racing", "commercial_use", "intentional_damage"])
    
    is_covered = claim_type.lower() in [p.lower() for p in covered_perils]
    is_excluded = claim_type.lower() in [e.lower() for e in exclusions]
    
    return {
        "claim_type": claim_type,
        "is_covered": is_covered and not is_excluded,
        "covered_perils": covered_perils,
        "exclusions": exclusions,
        "exclusion_triggered": is_excluded,
        "coverage_reason": "Covered under policy" if is_covered and not is_excluded else "Not covered or excluded"
    }

@tool
def check_policy_compliance(claim_data: Dict[str, Any], policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check compliance with policy terms and conditions."""
    compliance_issues = []
    
    # Check reporting timeframe
    incident_date = claim_data.get("incident_date", "")
    report_date = claim_data.get("report_date", datetime.utcnow().isoformat())
    
    # Simulate date parsing and checking
    reporting_delay = 5  # days (simplified)
    max_reporting_days = policy_data.get("max_reporting_days", 30)
    
    if reporting_delay > max_reporting_days:
        compliance_issues.append("Late reporting - exceeds policy requirements")
    
    # Check required documentation
    required_docs = policy_data.get("required_documents", ["police_report", "photos", "estimate"])
    provided_docs = claim_data.get("documents", [])
    
    missing_docs = [doc for doc in required_docs if doc not in provided_docs]
    if missing_docs:
        compliance_issues.append(f"Missing required documents: {', '.join(missing_docs)}")
    
    return {
        "compliant": len(compliance_issues) == 0,
        "compliance_issues": compliance_issues,
        "reporting_delay_days": reporting_delay,
        "required_documents": required_docs,
        "provided_documents": provided_docs,
        "missing_documents": missing_docs
    }

@tool
def assess_policy_risk(claim_data: Dict[str, Any], policy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess risk factors related to policy and claim."""
    risk_factors = []
    risk_score = 0.0
    
    # Policy age risk
    policy_age_months = policy_data.get("policy_age_months", 12)
    if policy_age_months < 6:
        risk_factors.append("New policy - less than 6 months old")
        risk_score += 0.2
    
    # Claim frequency risk
    previous_claims = policy_data.get("previous_claims_count", 0)
    if previous_claims > 2:
        risk_factors.append("Multiple previous claims")
        risk_score += 0.3
    
    # Premium payment risk
    premium_status = policy_data.get("premium_status", "current")
    if premium_status != "current":
        risk_factors.append("Premium payment issues")
        risk_score += 0.4
    
    # Claim amount risk
    claim_amount = claim_data.get("claim_amount", 0)
    policy_limit = policy_data.get("coverage_limit", 100000)
    
    if claim_amount > policy_limit * 0.8:
        risk_factors.append("High claim amount relative to policy limit")
        risk_score += 0.3
    
    risk_level = "high" if risk_score > 0.6 else "medium" if risk_score > 0.3 else "low"
    
    return {
        "risk_score": min(1.0, risk_score),
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "policy_age_months": policy_age_months,
        "previous_claims": previous_claims,
        "premium_status": premium_status
    }

class LangGraphPolicyAgent:
    """Autonomous policy validation agent using LangGraph workflows"""
    
    def __init__(self, ollama_endpoint: str = "http://ollama-service:11434"):
        self.agent_id = "langgraph_policy_001"
        self.ollama_endpoint = ollama_endpoint
        
        # Initialize LLM
        self.llm = ChatOllama(
            base_url=ollama_endpoint,
            model="qwen2.5-coder:32b",
            temperature=0.3  # Lower temperature for policy validation
        )
        
        # Policy knowledge base (simulate database)
        self.policy_templates = {
            "auto": {
                "covered_perils": ["collision", "comprehensive", "liability"],
                "exclusions": ["racing", "commercial_use"],
                "max_reporting_days": 30,
                "required_documents": ["police_report", "photos"]
            },
            "home": {
                "covered_perils": ["fire", "theft", "storm", "liability"],
                "exclusions": ["flood", "earthquake", "war"],
                "max_reporting_days": 60,
                "required_documents": ["photos", "receipts", "contractor_estimate"]
            }
        }
        
        # Create policy validation workflow
        self.workflow = self._create_policy_workflow()
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        logger.info(f"Initialized LangGraph Policy Agent: {self.agent_id}")

    def _create_policy_workflow(self) -> StateGraph:
        """Create the policy validation workflow"""
        
        workflow = StateGraph(PolicyState)
        
        # Workflow nodes
        workflow.add_node("validate_policy", self._validate_policy_node)
        workflow.add_node("analyze_coverage", self._analyze_coverage_node)
        workflow.add_node("check_compliance", self._check_compliance_node)
        workflow.add_node("assess_risk", self._assess_risk_node)
        workflow.add_node("llm_reasoning", self._llm_reasoning_node)
        workflow.add_node("make_recommendation", self._make_recommendation_node)
        
        # Workflow edges
        workflow.set_entry_point("validate_policy")
        workflow.add_edge("validate_policy", "analyze_coverage")
        workflow.add_edge("analyze_coverage", "check_compliance")
        workflow.add_edge("check_compliance", "assess_risk")
        workflow.add_edge("assess_risk", "llm_reasoning")
        workflow.add_edge("llm_reasoning", "make_recommendation")
        workflow.add_edge("make_recommendation", END)
        
        return workflow

    async def _validate_policy_node(self, state: PolicyState) -> PolicyState:
        """Validate policy existence and status"""
        claim_data = state["claim_data"]
        policy_number = claim_data.get("policy_number", "")
        
        # Validate policy existence
        validation_result = validate_policy_existence.invoke(policy_number, claim_data)
        
        if validation_result["policy_exists"]:
            # Simulate policy data retrieval
            policy_type = claim_data.get("claim_type", "auto")
            state["policy_data"] = {
                **self.policy_templates.get(policy_type, self.policy_templates["auto"]),
                "policy_number": policy_number,
                "coverage_limit": 100000,
                "deductible": 1000,
                "policy_age_months": 18,
                "previous_claims_count": 1,
                "premium_status": "current"
            }
        
        state["validation_results"] = validation_result
        state["reasoning_chain"].append(f"Policy validation: {'Found' if validation_result['policy_exists'] else 'Not found'}")
        
        return state

    async def _analyze_coverage_node(self, state: PolicyState) -> PolicyState:
        """Analyze coverage limits and claim type coverage"""
        claim_data = state["claim_data"]
        policy_data = state["policy_data"]
        
        # Check coverage limits
        coverage_limits = check_coverage_limits.invoke(
            claim_data.get("claim_amount", 0), 
            policy_data
        )
        
        # Check claim type coverage
        claim_type_coverage = validate_claim_type_coverage.invoke(
            claim_data.get("claim_type", "collision"),
            policy_data
        )
        
        state["coverage_analysis"] = {
            "limits": coverage_limits,
            "claim_type": claim_type_coverage
        }
        
        state["reasoning_chain"].append(f"Coverage analysis: {coverage_limits['coverage_percentage']:.1f}% covered")
        
        return state

    async def _check_compliance_node(self, state: PolicyState) -> PolicyState:
        """Check policy compliance and requirements"""
        claim_data = state["claim_data"]
        policy_data = state["policy_data"]
        
        compliance_result = check_policy_compliance.invoke(claim_data, policy_data)
        
        state["compliance_check"] = compliance_result
        state["reasoning_chain"].append(f"Compliance check: {'Compliant' if compliance_result['compliant'] else 'Issues found'}")
        
        return state

    async def _assess_risk_node(self, state: PolicyState) -> PolicyState:
        """Assess policy-related risks"""
        claim_data = state["claim_data"]
        policy_data = state["policy_data"]
        
        risk_assessment = assess_policy_risk.invoke(claim_data, policy_data)
        
        state["risk_assessment"] = risk_assessment
        state["reasoning_chain"].append(f"Risk assessment: {risk_assessment['risk_level']} risk")
        
        return state

    async def _llm_reasoning_node(self, state: PolicyState) -> PolicyState:
        """Advanced LLM reasoning for complex policy decisions"""
        
        # Prepare comprehensive context for LLM
        context = {
            "claim_data": state["claim_data"],
            "policy_validation": state["validation_results"],
            "coverage_analysis": state["coverage_analysis"],
            "compliance_check": state["compliance_check"],
            "risk_assessment": state["risk_assessment"]
        }
        
        reasoning_prompt = f"""
        Analyze this insurance policy validation case and provide expert reasoning:
        
        Context: {json.dumps(context, indent=2)}
        
        Consider:
        1. Policy validity and status
        2. Coverage adequacy and limits
        3. Compliance with policy terms
        4. Risk factors and concerns
        5. Regulatory requirements
        
        Provide detailed reasoning for policy validation decision.
        """
        
        messages = [SystemMessage(content="You are an expert insurance policy analyst with deep knowledge of policy terms, coverage analysis, and regulatory compliance.")]
        messages.append(HumanMessage(content=reasoning_prompt))
        
        try:
            response = await self.llm.ainvoke(messages)
            llm_analysis = {
                "reasoning": response.content,
                "llm_confidence": 0.85,  # Could be extracted from response
                "key_factors": self._extract_key_factors(response.content)
            }
        except Exception as e:
            logger.error(f"LLM reasoning failed: {e}")
            llm_analysis = {
                "reasoning": "LLM analysis unavailable - using rule-based logic",
                "llm_confidence": 0.6,
                "key_factors": ["rule_based_analysis"]
            }
        
        state["coverage_analysis"]["llm_analysis"] = llm_analysis
        state["reasoning_chain"].append("Advanced LLM reasoning completed")
        
        return state

    def _extract_key_factors(self, llm_response: str) -> List[str]:
        """Extract key factors from LLM response"""
        # Simple keyword extraction (enhance with NLP in production)
        factors = []
        keywords = ["coverage", "compliance", "risk", "exclusion", "limit", "deductible"]
        
        for keyword in keywords:
            if keyword in llm_response.lower():
                factors.append(keyword)
        
        return factors

    async def _make_recommendation_node(self, state: PolicyState) -> PolicyState:
        """Create policy analysis for underwriter review"""

        # Aggregate all analysis results
        policy_valid = state["validation_results"]["policy_exists"]
        coverage_adequate = state["coverage_analysis"]["limits"]["within_limits"]
        claim_covered = state["coverage_analysis"]["claim_type"]["is_covered"]
        compliant = state["compliance_check"]["compliant"]
        risk_level = state["risk_assessment"]["risk_level"]

        # Determine underwriter escalation requirements
        underwriter_required = False
        senior_underwriter_required = False
        escalation_reason = []

        if not policy_valid:
            underwriter_required = True
            escalation_reason.append("Policy validation issues")

        if not claim_covered:
            underwriter_required = True
            escalation_reason.append("Coverage interpretation required")

        if not coverage_adequate:
            underwriter_required = True
            escalation_reason.append("Policy limits exceeded")

        if not compliant:
            senior_underwriter_required = True
            escalation_reason.append("Policy compliance violations")

        if risk_level == "high":
            senior_underwriter_required = True
            escalation_reason.append("High-risk policy factors")

        # Determine required underwriter level
        if senior_underwriter_required:
            required_reviewer = "senior_underwriter"
            regulatory_requirement = "Senior underwriter approval required for complex coverage decisions"
        elif underwriter_required:
            required_reviewer = "underwriter"
            regulatory_requirement = "Licensed underwriter must interpret policy coverage"
        else:
            required_reviewer = "underwriter"  # Even simple cases need underwriter review
            regulatory_requirement = "Basic underwriter review required per industry standards"

        # Calculate confidence score
        confidence_factors = [
            0.9 if policy_valid else 0.1,
            0.9 if claim_covered else 0.1,
            0.8 if coverage_adequate else 0.3,
            0.8 if compliant else 0.4,
            0.7 if risk_level == "low" else 0.5 if risk_level == "medium" else 0.3
        ]

        state["confidence_score"] = sum(confidence_factors) / len(confidence_factors)

        state["final_recommendation"] = {
            "ai_analysis_complete": True,
            "underwriter_required": underwriter_required or senior_underwriter_required,
            "required_reviewer": required_reviewer,
            "escalation_reason": escalation_reason,
            "regulatory_requirement": regulatory_requirement,
            "policy_valid": policy_valid,
            "claim_covered": claim_covered,
            "coverage_adequate": coverage_adequate,
            "compliant": compliant,
            "risk_level": risk_level,
            "covered_amount": state["coverage_analysis"]["limits"]["covered_amount"],
            "coverage_percentage": state["coverage_analysis"]["limits"]["coverage_percentage"],
            "human_decision_required": True,
            "ai_decision_prohibited": "Policy coverage decisions require licensed underwriter approval"
        }

        state["reasoning_chain"].append(f"AI analysis complete - {required_reviewer} review required")

        return state

    async def validate_policy_with_langgraph(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate policy using LangGraph workflow"""
        
        # Initialize state
        initial_state = PolicyState(
            messages=[HumanMessage(content=f"Validate policy for claim: {claim_data.get('claim_id')}")],
            claim_data=claim_data,
            policy_data={},
            validation_results={},
            coverage_analysis={},
            compliance_check={},
            risk_assessment={},
            final_recommendation=None,
            reasoning_chain=[],
            confidence_score=0.0
        )
        
        # Execute workflow
        try:
            config = {"configurable": {"thread_id": claim_data.get("claim_id", "default")}}
            final_state = await self.app.ainvoke(initial_state, config=config)
            
            return {
                "agent_id": self.agent_id,
                "claim_id": claim_data.get("claim_id"),
                "workflow_type": "langgraph_policy_validation",
                "policy_validation": final_state["validation_results"],
                "coverage_analysis": final_state["coverage_analysis"],
                "compliance_check": final_state["compliance_check"],
                "risk_assessment": final_state["risk_assessment"],
                "final_recommendation": final_state["final_recommendation"],
                "reasoning_chain": final_state["reasoning_chain"],
                "confidence_score": final_state["confidence_score"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Policy validation workflow error: {str(e)}")
            return {
                "error": f"Policy validation failed: {str(e)}",
                "agent_id": self.agent_id,
                "workflow_type": "langgraph_policy_validation"
            }

# FastAPI Application
app = FastAPI(
    title="LangGraph Policy Validation Agent",
    description="Autonomous policy validation with advanced reasoning",
    version="3.0.0"
)

# Global agent instance
policy_agent: Optional[LangGraphPolicyAgent] = None

@app.on_event("startup")
async def startup_event():
    global policy_agent
    try:
        policy_agent = LangGraphPolicyAgent()
        logger.info("LangGraph Policy Agent started")
    except Exception as e:
        logger.error(f"Failed to start Policy Agent: {e}")
        # Don't fail startup, continue without agent for now
        pass

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "langgraph-policy-agent",
        "framework": "LangGraph + LangChain + Ollama",
        "capabilities": [
            "policy_validation",
            "coverage_analysis",
            "compliance_checking",
            "risk_assessment",
            "llm_reasoning"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/validate")
async def validate_policy(claim_data: Dict[str, Any]):
    """Validate policy using LangGraph workflow"""
    if not policy_agent:
        raise HTTPException(status_code=503, detail="Policy agent not initialized")
    
    result = await policy_agent.validate_policy_with_langgraph(claim_data)
    return result

@app.get("/workflow")
async def get_workflow_info():
    return {
        "workflow_type": "LangGraph Policy Validation",
        "nodes": [
            "validate_policy",
            "analyze_coverage",
            "check_compliance", 
            "assess_risk",
            "llm_reasoning",
            "make_recommendation"
        ],
        "tools": [
            "validate_policy_existence",
            "check_coverage_limits",
            "validate_claim_type_coverage",
            "check_policy_compliance",
            "assess_policy_risk"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
