"""
LangGraph Investigation Agent - Autonomous Deep Investigation
Advanced investigation with multi-step reasoning and evidence collection
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

# State definition for investigation workflow
class InvestigationState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    claim_data: Dict[str, Any]
    investigation_plan: Dict[str, Any]
    evidence_collected: List[Dict[str, Any]]
    analysis_results: Dict[str, Any]
    cross_references: Dict[str, Any]
    investigation_depth: int
    findings: List[Dict[str, Any]]
    final_report: Optional[Dict[str, Any]]
    reasoning_chain: List[str]
    confidence_score: float

@tool
def create_investigation_plan(claim_data: Dict[str, Any], fraud_indicators: List[str]) -> Dict[str, Any]:
    """Create comprehensive investigation plan based on claim data and fraud indicators."""
    
    investigation_areas = []
    priority_levels = {}
    
    # Determine investigation areas based on fraud indicators
    if "high_amount" in fraud_indicators:
        investigation_areas.extend(["financial_verification", "damage_assessment"])
        priority_levels["financial_verification"] = "high"
    
    if "pattern_match" in fraud_indicators:
        investigation_areas.extend(["historical_analysis", "network_analysis"])
        priority_levels["historical_analysis"] = "high"
    
    if "documentation_issues" in fraud_indicators:
        investigation_areas.extend(["document_verification", "witness_interviews"])
        priority_levels["document_verification"] = "high"
    
    # Default investigation areas
    if not investigation_areas:
        investigation_areas = ["basic_verification", "damage_assessment"]
        priority_levels["basic_verification"] = "medium"
    
    return {
        "investigation_id": f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "investigation_areas": investigation_areas,
        "priority_levels": priority_levels,
        "estimated_duration": len(investigation_areas) * 2,  # days
        "resources_required": ["investigator", "analyst"] if len(investigation_areas) > 2 else ["investigator"],
        "investigation_type": "comprehensive" if len(investigation_areas) > 3 else "standard"
    }

@tool
def collect_evidence(investigation_area: str, claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Collect evidence for specific investigation area."""
    
    evidence = {
        "area": investigation_area,
        "collection_date": datetime.utcnow().isoformat(),
        "evidence_items": [],
        "reliability_score": 0.0,
        "completeness": 0.0
    }
    
    if investigation_area == "financial_verification":
        evidence["evidence_items"] = [
            {"type": "bank_records", "status": "requested", "reliability": 0.9},
            {"type": "income_verification", "status": "pending", "reliability": 0.8},
            {"type": "expense_analysis", "status": "completed", "reliability": 0.7}
        ]
        evidence["reliability_score"] = 0.8
        evidence["completeness"] = 0.7
    
    elif investigation_area == "damage_assessment":
        evidence["evidence_items"] = [
            {"type": "photos", "status": "collected", "reliability": 0.9},
            {"type": "repair_estimates", "status": "collected", "reliability": 0.8},
            {"type": "expert_assessment", "status": "scheduled", "reliability": 0.95}
        ]
        evidence["reliability_score"] = 0.85
        evidence["completeness"] = 0.8
    
    elif investigation_area == "historical_analysis":
        evidence["evidence_items"] = [
            {"type": "claim_history", "status": "analyzed", "reliability": 0.95},
            {"type": "pattern_analysis", "status": "completed", "reliability": 0.8},
            {"type": "behavioral_profile", "status": "in_progress", "reliability": 0.7}
        ]
        evidence["reliability_score"] = 0.82
        evidence["completeness"] = 0.75
    
    elif investigation_area == "document_verification":
        evidence["evidence_items"] = [
            {"type": "police_report", "status": "verified", "reliability": 0.95},
            {"type": "medical_records", "status": "pending", "reliability": 0.9},
            {"type": "witness_statements", "status": "collected", "reliability": 0.7}
        ]
        evidence["reliability_score"] = 0.85
        evidence["completeness"] = 0.8
    
    else:  # basic_verification
        evidence["evidence_items"] = [
            {"type": "identity_check", "status": "completed", "reliability": 0.95},
            {"type": "contact_verification", "status": "completed", "reliability": 0.9},
            {"type": "basic_documentation", "status": "reviewed", "reliability": 0.8}
        ]
        evidence["reliability_score"] = 0.88
        evidence["completeness"] = 0.9
    
    return evidence

@tool
def analyze_evidence_patterns(evidence_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze collected evidence for patterns and inconsistencies."""
    
    total_evidence_items = sum(len(e["evidence_items"]) for e in evidence_list)
    avg_reliability = sum(e["reliability_score"] for e in evidence_list) / len(evidence_list) if evidence_list else 0
    avg_completeness = sum(e["completeness"] for e in evidence_list) / len(evidence_list) if evidence_list else 0
    
    # Detect inconsistencies
    inconsistencies = []
    red_flags = []
    
    # Check for reliability variations
    reliability_scores = [e["reliability_score"] for e in evidence_list]
    if max(reliability_scores) - min(reliability_scores) > 0.3:
        inconsistencies.append("Significant reliability variation across evidence sources")
    
    # Check for completeness issues
    incomplete_areas = [e["area"] for e in evidence_list if e["completeness"] < 0.7]
    if incomplete_areas:
        red_flags.append(f"Incomplete evidence in areas: {', '.join(incomplete_areas)}")
    
    # Pattern analysis
    patterns_detected = []
    if avg_reliability > 0.8 and avg_completeness > 0.8:
        patterns_detected.append("High quality evidence pattern")
    elif avg_reliability < 0.6:
        patterns_detected.append("Low reliability evidence pattern")
        red_flags.append("Multiple low-reliability evidence sources")
    
    return {
        "total_evidence_items": total_evidence_items,
        "average_reliability": avg_reliability,
        "average_completeness": avg_completeness,
        "inconsistencies": inconsistencies,
        "red_flags": red_flags,
        "patterns_detected": patterns_detected,
        "evidence_quality": "high" if avg_reliability > 0.8 else "medium" if avg_reliability > 0.6 else "low"
    }

@tool
def cross_reference_data(claim_data: Dict[str, Any], external_sources: List[str]) -> Dict[str, Any]:
    """Cross-reference claim data with external sources."""
    
    cross_ref_results = {}
    
    for source in external_sources:
        if source == "fraud_database":
            # Simulate fraud database check
            cross_ref_results[source] = {
                "matches_found": 0,
                "similar_patterns": 1,
                "confidence": 0.7,
                "details": "One similar pattern found in historical data"
            }
        
        elif source == "public_records":
            # Simulate public records check
            cross_ref_results[source] = {
                "identity_verified": True,
                "address_verified": True,
                "employment_verified": False,
                "confidence": 0.8
            }
        
        elif source == "social_media":
            # Simulate social media analysis
            cross_ref_results[source] = {
                "activity_consistent": True,
                "location_consistent": True,
                "timeline_consistent": False,
                "confidence": 0.6,
                "concerns": ["Timeline inconsistency with claimed incident"]
            }
        
        elif source == "industry_database":
            # Simulate industry database check
            cross_ref_results[source] = {
                "previous_claims": 2,
                "claim_frequency": "normal",
                "industry_flags": [],
                "confidence": 0.9
            }
    
    # Overall cross-reference assessment
    avg_confidence = sum(result.get("confidence", 0) for result in cross_ref_results.values()) / len(cross_ref_results) if cross_ref_results else 0
    
    concerns = []
    for source, result in cross_ref_results.items():
        if "concerns" in result:
            concerns.extend(result["concerns"])
        if result.get("confidence", 0) < 0.7:
            concerns.append(f"Low confidence in {source} verification")
    
    return {
        "sources_checked": external_sources,
        "cross_reference_results": cross_ref_results,
        "overall_confidence": avg_confidence,
        "concerns_identified": concerns,
        "verification_status": "verified" if avg_confidence > 0.8 and not concerns else "partial" if avg_confidence > 0.6 else "unverified"
    }

@tool
def generate_investigation_findings(analysis_results: Dict[str, Any], cross_ref_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate structured investigation findings."""
    
    findings = []
    
    # Evidence quality finding
    evidence_quality = analysis_results.get("evidence_quality", "medium")
    findings.append({
        "finding_id": "F001",
        "category": "evidence_quality",
        "severity": "low" if evidence_quality == "high" else "medium" if evidence_quality == "medium" else "high",
        "description": f"Evidence quality assessed as {evidence_quality}",
        "impact": "Affects overall case reliability",
        "recommendation": "Accept evidence" if evidence_quality == "high" else "Additional verification needed"
    })
    
    # Cross-reference finding
    verification_status = cross_ref_results.get("verification_status", "partial")
    if verification_status != "verified":
        findings.append({
            "finding_id": "F002",
            "category": "verification",
            "severity": "high" if verification_status == "unverified" else "medium",
            "description": f"Cross-reference verification status: {verification_status}",
            "impact": "May indicate fraudulent activity",
            "recommendation": "Further investigation required" if verification_status == "unverified" else "Additional checks recommended"
        })
    
    # Red flags finding
    red_flags = analysis_results.get("red_flags", [])
    if red_flags:
        findings.append({
            "finding_id": "F003",
            "category": "red_flags",
            "severity": "high",
            "description": f"Red flags identified: {'; '.join(red_flags)}",
            "impact": "Indicates potential fraud or irregularities",
            "recommendation": "Detailed review and possible claim denial"
        })
    
    # Concerns finding
    concerns = cross_ref_results.get("concerns_identified", [])
    if concerns:
        findings.append({
            "finding_id": "F004",
            "category": "concerns",
            "severity": "medium",
            "description": f"Concerns identified: {'; '.join(concerns)}",
            "impact": "Requires attention and clarification",
            "recommendation": "Request additional documentation or clarification"
        })
    
    return findings

class LangGraphInvestigationAgent:
    """Autonomous investigation agent using LangGraph workflows"""
    
    def __init__(self, ollama_endpoint: str = "http://ollama-service:11434"):
        self.agent_id = "langgraph_investigation_001"
        self.ollama_endpoint = ollama_endpoint
        
        # Initialize LLM
        self.llm = ChatOllama(
            base_url=ollama_endpoint,
            model="qwen2.5-coder:32b",
            temperature=0.4  # Balanced temperature for investigation
        )
        
        # Investigation knowledge base
        self.investigation_protocols = {
            "fraud_indicators": [
                "high_amount", "pattern_match", "documentation_issues",
                "timeline_inconsistency", "witness_credibility", "prior_claims"
            ],
            "evidence_types": [
                "financial", "photographic", "documentary", "testimonial", "digital", "forensic"
            ],
            "external_sources": [
                "fraud_database", "public_records", "social_media", "industry_database"
            ]
        }
        
        # Create investigation workflow
        self.workflow = self._create_investigation_workflow()
        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        logger.info(f"Initialized LangGraph Investigation Agent: {self.agent_id}")

    def _create_investigation_workflow(self) -> StateGraph:
        """Create the investigation workflow"""
        
        workflow = StateGraph(InvestigationState)
        
        # Workflow nodes
        workflow.add_node("plan_investigation", self._plan_investigation_node)
        workflow.add_node("collect_evidence", self._collect_evidence_node)
        workflow.add_node("analyze_evidence", self._analyze_evidence_node)
        workflow.add_node("cross_reference", self._cross_reference_node)
        workflow.add_node("deep_analysis", self._deep_analysis_node)
        workflow.add_node("generate_findings", self._generate_findings_node)
        workflow.add_node("create_report", self._create_report_node)
        
        # Workflow edges
        workflow.set_entry_point("plan_investigation")
        workflow.add_edge("plan_investigation", "collect_evidence")
        workflow.add_edge("collect_evidence", "analyze_evidence")
        workflow.add_edge("analyze_evidence", "cross_reference")
        workflow.add_edge("cross_reference", "deep_analysis")
        workflow.add_edge("deep_analysis", "generate_findings")
        workflow.add_edge("generate_findings", "create_report")
        workflow.add_edge("create_report", END)
        
        return workflow

    async def _plan_investigation_node(self, state: InvestigationState) -> InvestigationState:
        """Plan the investigation based on claim data and fraud indicators"""
        claim_data = state["claim_data"]
        
        # Extract fraud indicators from previous agent results
        fraud_analysis = claim_data.get("fraud_analysis", {})
        fraud_indicators = []
        
        if fraud_analysis.get("fraud_score", 0) > 0.6:
            fraud_indicators.append("high_amount")
        if fraud_analysis.get("patterns_detected", []):
            fraud_indicators.append("pattern_match")
        if claim_data.get("documentation_issues", []):
            fraud_indicators.append("documentation_issues")
        
        # Create investigation plan
        investigation_plan = create_investigation_plan.invoke(claim_data, fraud_indicators)
        
        state["investigation_plan"] = investigation_plan
        state["investigation_depth"] = len(investigation_plan["investigation_areas"])
        state["reasoning_chain"].append(f"Investigation planned: {investigation_plan['investigation_type']} with {len(investigation_plan['investigation_areas'])} areas")
        
        return state

    async def _collect_evidence_node(self, state: InvestigationState) -> InvestigationState:
        """Collect evidence for each investigation area"""
        investigation_plan = state["investigation_plan"]
        claim_data = state["claim_data"]
        
        evidence_collected = []
        
        for area in investigation_plan["investigation_areas"]:
            evidence = collect_evidence.invoke(area, claim_data)
            evidence_collected.append(evidence)
        
        state["evidence_collected"] = evidence_collected
        state["reasoning_chain"].append(f"Evidence collected from {len(evidence_collected)} areas")
        
        return state

    async def _analyze_evidence_node(self, state: InvestigationState) -> InvestigationState:
        """Analyze collected evidence for patterns and inconsistencies"""
        evidence_list = state["evidence_collected"]
        
        analysis_results = analyze_evidence_patterns.invoke(evidence_list)
        
        state["analysis_results"] = analysis_results
        state["reasoning_chain"].append(f"Evidence analysis completed - Quality: {analysis_results['evidence_quality']}")
        
        return state

    async def _cross_reference_node(self, state: InvestigationState) -> InvestigationState:
        """Cross-reference claim data with external sources"""
        claim_data = state["claim_data"]
        external_sources = self.investigation_protocols["external_sources"]
        
        cross_ref_results = cross_reference_data.invoke(claim_data, external_sources)
        
        state["cross_references"] = cross_ref_results
        state["reasoning_chain"].append(f"Cross-reference completed - Status: {cross_ref_results['verification_status']}")
        
        return state

    async def _deep_analysis_node(self, state: InvestigationState) -> InvestigationState:
        """Perform deep LLM-powered analysis"""
        
        # Prepare comprehensive context for LLM analysis
        context = {
            "claim_data": state["claim_data"],
            "investigation_plan": state["investigation_plan"],
            "evidence_analysis": state["analysis_results"],
            "cross_references": state["cross_references"]
        }
        
        analysis_prompt = f"""
        Conduct deep investigation analysis of this insurance claim:
        
        Context: {json.dumps(context, indent=2)}
        
        Analyze:
        1. Evidence consistency and reliability
        2. Cross-reference verification results
        3. Potential fraud indicators
        4. Investigation completeness
        5. Risk assessment
        
        Provide detailed investigative insights and recommendations.
        """
        
        messages = [SystemMessage(content="You are an expert insurance investigator with advanced analytical skills and fraud detection expertise.")]
        messages.append(HumanMessage(content=analysis_prompt))
        
        try:
            response = await self.llm.ainvoke(messages)
            deep_analysis = {
                "llm_insights": response.content,
                "analysis_confidence": 0.85,
                "key_concerns": self._extract_concerns(response.content),
                "recommendations": self._extract_recommendations(response.content)
            }
        except Exception as e:
            logger.error(f"Deep analysis LLM failed: {e}")
            deep_analysis = {
                "llm_insights": "Deep analysis unavailable - using rule-based assessment",
                "analysis_confidence": 0.6,
                "key_concerns": ["llm_unavailable"],
                "recommendations": ["manual_review_required"]
            }
        
        state["analysis_results"]["deep_analysis"] = deep_analysis
        state["reasoning_chain"].append("Deep LLM analysis completed")
        
        return state

    def _extract_concerns(self, llm_response: str) -> List[str]:
        """Extract key concerns from LLM response"""
        concerns = []
        concern_keywords = ["concern", "issue", "problem", "inconsistency", "red flag", "suspicious"]
        
        sentences = llm_response.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in concern_keywords):
                concerns.append(sentence.strip())
        
        return concerns[:5]  # Limit to top 5 concerns

    def _extract_recommendations(self, llm_response: str) -> List[str]:
        """Extract recommendations from LLM response"""
        recommendations = []
        rec_keywords = ["recommend", "suggest", "should", "advise", "propose"]
        
        sentences = llm_response.split('.')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in rec_keywords):
                recommendations.append(sentence.strip())
        
        return recommendations[:5]  # Limit to top 5 recommendations

    async def _generate_findings_node(self, state: InvestigationState) -> InvestigationState:
        """Generate structured investigation findings"""
        analysis_results = state["analysis_results"]
        cross_ref_results = state["cross_references"]
        
        findings = generate_investigation_findings.invoke(analysis_results, cross_ref_results)
        
        state["findings"] = findings
        state["reasoning_chain"].append(f"Generated {len(findings)} investigation findings")
        
        return state

    async def _create_report_node(self, state: InvestigationState) -> InvestigationState:
        """Create comprehensive investigation report"""
        
        # Calculate overall confidence score
        evidence_quality_score = 0.8 if state["analysis_results"]["evidence_quality"] == "high" else 0.6 if state["analysis_results"]["evidence_quality"] == "medium" else 0.4
        cross_ref_confidence = state["cross_references"]["overall_confidence"]
        deep_analysis_confidence = state["analysis_results"]["deep_analysis"]["analysis_confidence"]
        
        overall_confidence = (evidence_quality_score + cross_ref_confidence + deep_analysis_confidence) / 3
        
        # Determine final recommendation
        high_severity_findings = [f for f in state["findings"] if f["severity"] == "high"]
        medium_severity_findings = [f for f in state["findings"] if f["severity"] == "medium"]
        
        if len(high_severity_findings) > 1:
            recommendation = "DENY"
            reason = "Multiple high-severity findings indicate fraud"
        elif len(high_severity_findings) == 1:
            recommendation = "INVESTIGATE_FURTHER"
            reason = "High-severity finding requires additional investigation"
        elif len(medium_severity_findings) > 2:
            recommendation = "INVESTIGATE_FURTHER"
            reason = "Multiple medium-severity findings require attention"
        else:
            recommendation = "APPROVE"
            reason = "Investigation findings support claim approval"
        
        state["confidence_score"] = overall_confidence
        
        state["final_report"] = {
            "investigation_id": state["investigation_plan"]["investigation_id"],
            "claim_id": state["claim_data"].get("claim_id"),
            "investigation_type": state["investigation_plan"]["investigation_type"],
            "areas_investigated": state["investigation_plan"]["investigation_areas"],
            "evidence_summary": {
                "total_items": state["analysis_results"]["total_evidence_items"],
                "quality": state["analysis_results"]["evidence_quality"],
                "reliability": state["analysis_results"]["average_reliability"],
                "completeness": state["analysis_results"]["average_completeness"]
            },
            "cross_reference_summary": {
                "sources_checked": len(state["cross_references"]["sources_checked"]),
                "verification_status": state["cross_references"]["verification_status"],
                "concerns": len(state["cross_references"]["concerns_identified"])
            },
            "findings": state["findings"],
            "recommendation": recommendation,
            "reason": reason,
            "confidence_score": overall_confidence,
            "investigation_depth": state["investigation_depth"],
            "llm_insights": state["analysis_results"]["deep_analysis"]["llm_insights"]
        }
        
        state["reasoning_chain"].append(f"Investigation report completed - Recommendation: {recommendation}")
        
        return state

    async def investigate_claim_with_langgraph(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Investigate claim using LangGraph workflow"""
        
        # Initialize state
        initial_state = InvestigationState(
            messages=[HumanMessage(content=f"Investigate claim: {claim_data.get('claim_id')}")],
            claim_data=claim_data,
            investigation_plan={},
            evidence_collected=[],
            analysis_results={},
            cross_references={},
            investigation_depth=0,
            findings=[],
            final_report=None,
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
                "workflow_type": "langgraph_investigation",
                "investigation_report": final_state["final_report"],
                "reasoning_chain": final_state["reasoning_chain"],
                "confidence_score": final_state["confidence_score"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Investigation workflow error: {str(e)}")
            return {
                "error": f"Investigation failed: {str(e)}",
                "agent_id": self.agent_id,
                "workflow_type": "langgraph_investigation"
            }

# FastAPI Application
app = FastAPI(
    title="LangGraph Investigation Agent",
    description="Autonomous investigation with deep analysis and evidence collection",
    version="3.0.0"
)

# Global agent instance
investigation_agent: Optional[LangGraphInvestigationAgent] = None

@app.on_event("startup")
async def startup_event():
    global investigation_agent
    try:
        investigation_agent = LangGraphInvestigationAgent()
        logger.info("LangGraph Investigation Agent started")
    except Exception as e:
        logger.error(f"Failed to start Investigation Agent: {e}")
        # Don't fail startup, continue without agent for now
        pass

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "langgraph-investigation-agent",
        "framework": "LangGraph + LangChain + Ollama",
        "capabilities": [
            "investigation_planning",
            "evidence_collection",
            "pattern_analysis",
            "cross_referencing",
            "deep_llm_analysis",
            "report_generation"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/investigate")
async def investigate_claim(claim_data: Dict[str, Any]):
    """Investigate claim using LangGraph workflow"""
    if not investigation_agent:
        raise HTTPException(status_code=503, detail="Investigation agent not initialized")
    
    result = await investigation_agent.investigate_claim_with_langgraph(claim_data)
    return result

@app.get("/workflow")
async def get_workflow_info():
    return {
        "workflow_type": "LangGraph Investigation",
        "nodes": [
            "plan_investigation",
            "collect_evidence",
            "analyze_evidence",
            "cross_reference",
            "deep_analysis",
            "generate_findings",
            "create_report"
        ],
        "tools": [
            "create_investigation_plan",
            "collect_evidence",
            "analyze_evidence_patterns",
            "cross_reference_data",
            "generate_investigation_findings"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
