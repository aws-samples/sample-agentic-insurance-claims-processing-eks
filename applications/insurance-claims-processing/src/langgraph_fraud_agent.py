"""
LangGraph Fraud Analysis Agent - Industry Standard SIU Integration
AI-assisted fraud analysis with mandatory SIU escalation for high-risk cases
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import operator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State definition for LangGraph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    claim_data: Dict[str, Any]
    fraud_analysis: Dict[str, Any]
    investigation_results: Dict[str, Any]
    agent_memory: Dict[str, Any]
    next_action: str
    confidence_score: float
    reasoning_chain: List[str]

# Tools for the agent
@tool
def analyze_claim_amount(claim_data: dict) -> dict:
    """Analyze claim amount for anomalies and patterns."""
    amount = claim_data.get("claim_amount", 0)
    policy_limit = claim_data.get("policy_limit", 100000)
    
    analysis = {
        "amount": amount,
        "amount_to_limit_ratio": amount / policy_limit if policy_limit > 0 else 0,
        "risk_level": "high" if amount > 50000 else "medium" if amount > 10000 else "low",
        "anomaly_indicators": []
    }
    
    if amount > policy_limit * 0.9:
        analysis["anomaly_indicators"].append("near_policy_limit")
    if amount % 1000 == 0:
        analysis["anomaly_indicators"].append("round_number_suspicious")
    
    return analysis

@tool
def check_fraud_patterns(claim_data: dict, known_patterns: list) -> dict:
    """Check claim against known fraud patterns."""
    matches = []
    total_score = 0.0
    
    for pattern in known_patterns:
        match_score = 0.0
        pattern_features = pattern.get("features", {})
        
        # Pattern matching logic
        if "high_amount" in pattern_features and claim_data.get("claim_amount", 0) > 25000:
            match_score += 0.4
        if "weekend_claim" in pattern_features and "weekend" in claim_data.get("incident_date", ""):
            match_score += 0.3
        if "vague_description" in pattern_features and len(claim_data.get("description", "")) < 50:
            match_score += 0.3
        
        if match_score > 0.5:
            matches.append({
                "pattern_id": pattern.get("id"),
                "match_score": match_score,
                "confidence": pattern.get("confidence", 0.7)
            })
            total_score += match_score
    
    return {
        "pattern_matches": matches,
        "total_pattern_score": min(1.0, total_score),
        "patterns_checked": len(known_patterns)
    }

@tool
def investigate_claimant_history(claimant_info: dict) -> dict:
    """Investigate claimant's historical patterns."""
    # Simulated investigation
    return {
        "previous_claims": 2,
        "claim_frequency": "normal",
        "red_flags": [],
        "credibility_score": 0.8,
        "investigation_depth": "standard"
    }

@tool
def update_agent_memory(memory_data: dict, new_experience: dict) -> dict:
    """Update agent's memory with new experience."""
    if "experiences" not in memory_data:
        memory_data["experiences"] = []
    
    memory_data["experiences"].append({
        **new_experience,
        "timestamp": datetime.utcnow().isoformat(),
        "importance": new_experience.get("fraud_score", 0) * 0.5 + 0.5
    })
    
    # Keep only recent experiences
    memory_data["experiences"] = memory_data["experiences"][-50:]
    
    return memory_data

class LangGraphFraudAgent:
    """LangGraph-powered autonomous fraud detection agent"""
    
    def __init__(self):
        self.agent_id = "langgraph_fraud_001"
        self.fraud_patterns = [
            {
                "id": "pattern_1",
                "features": ["high_amount", "vague_description"],
                "confidence": 0.85
            },
            {
                "id": "pattern_2", 
                "features": ["weekend_claim", "round_number"],
                "confidence": 0.75
            }
        ]
        
        # Initialize LangGraph workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()
        
        # Agent memory
        self.memory = {
            "experiences": [],
            "learned_patterns": [],
            "performance_metrics": {}
        }
        
        # Initialize authentic autonomous LLM - NO MOCK RESPONSES
        from applications.shared.authentic_llm_integration import init_autonomous_llm
        try:
            self.llm_engine = init_autonomous_llm(
                agent_id=self.agent_id,
                agent_type="fraud_detection_agent",
                preferred_model="qwen2.5-coder:32b"
            )
            logger.info("Initialized authentic autonomous LLM for fraud detection")
        except Exception as e:
            logger.warning(f"Failed to initialize autonomous LLM: {e}")
            self.llm_engine = None

        logger.info(f"Initialized LangGraph Fraud Agent: {self.agent_id}")

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for fraud detection"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (states) to the graph
        workflow.add_node("analyze_claim", self._analyze_claim_node)
        workflow.add_node("pattern_matching", self._pattern_matching_node)
        workflow.add_node("deep_investigation", self._deep_investigation_node)
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("decision_making", self._decision_making_node)
        workflow.add_node("learning", self._learning_node)
        
        # Define the workflow edges (transitions)
        workflow.set_entry_point("analyze_claim")
        
        workflow.add_edge("analyze_claim", "pattern_matching")
        workflow.add_edge("pattern_matching", "reasoning")
        
        # Conditional routing based on analysis
        workflow.add_conditional_edges(
            "reasoning",
            self._should_investigate_deeper,
            {
                "investigate": "deep_investigation",
                "decide": "decision_making"
            }
        )
        
        workflow.add_edge("deep_investigation", "decision_making")
        workflow.add_edge("decision_making", "learning")
        workflow.add_edge("learning", END)
        
        return workflow

    async def _analyze_claim_node(self, state: AgentState) -> AgentState:
        """Initial claim analysis node"""
        claim_data = state["claim_data"]
        
        # Use the analyze_claim_amount tool
        amount_analysis = analyze_claim_amount.invoke({"claim_data": claim_data})
        
        # Update state
        state["fraud_analysis"] = {
            "amount_analysis": amount_analysis,
            "initial_risk": amount_analysis["risk_level"]
        }
        
        state["reasoning_chain"].append(f"Analyzed claim amount: ${claim_data.get('claim_amount', 0)} - Risk: {amount_analysis['risk_level']}")
        state["next_action"] = "pattern_matching"
        
        return state

    async def _pattern_matching_node(self, state: AgentState) -> AgentState:
        """Pattern matching analysis node"""
        claim_data = state["claim_data"]
        
        # Check against known fraud patterns
        pattern_results = check_fraud_patterns.invoke({"claim_data": claim_data, "known_patterns": self.fraud_patterns})
        
        # Update fraud analysis
        state["fraud_analysis"]["pattern_analysis"] = pattern_results
        
        # Calculate preliminary fraud score
        amount_risk = state["fraud_analysis"]["amount_analysis"]["amount_to_limit_ratio"]
        pattern_risk = pattern_results["total_pattern_score"]
        preliminary_score = (amount_risk * 0.4) + (pattern_risk * 0.6)
        
        state["confidence_score"] = preliminary_score
        state["reasoning_chain"].append(f"Pattern matching complete: {len(pattern_results['pattern_matches'])} matches found")
        
        return state

    async def _deep_investigation_node(self, state: AgentState) -> AgentState:
        """Deep investigation node for high-risk claims"""
        claim_data = state["claim_data"]
        claimant_info = claim_data.get("claimant_info", {})
        
        # Investigate claimant history
        investigation = investigate_claimant_history.invoke({"claimant_info": claimant_info})
        
        state["investigation_results"] = investigation
        state["reasoning_chain"].append(f"Deep investigation completed - Credibility: {investigation['credibility_score']}")
        
        return state

    async def _reasoning_node(self, state: AgentState) -> AgentState:
        """Advanced reasoning node using LLM"""
        
        # Build reasoning context
        reasoning_context = {
            "claim_amount": state["claim_data"].get("claim_amount"),
            "amount_analysis": state["fraud_analysis"]["amount_analysis"],
            "pattern_matches": state["fraud_analysis"]["pattern_analysis"]["pattern_matches"],
            "confidence_score": state["confidence_score"]
        }
        
        # Authentic autonomous reasoning - NO SIMULATION
        reasoning_result = await self._autonomous_reasoning(reasoning_context)
        
        state["fraud_analysis"]["reasoning"] = reasoning_result
        state["reasoning_chain"].append(f"LLM reasoning: {reasoning_result['conclusion']}")
        
        return state

    async def _autonomous_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Authentic autonomous reasoning using real LLM - NO SIMULATION"""
        from applications.shared.authentic_llm_integration import autonomous_reasoning

        # Prepare input for autonomous reasoning
        input_data = {
            "claim_amount": context["claim_amount"],
            "amount_analysis": context["amount_analysis"],
            "pattern_matches": context["pattern_matches"],
            "claim_data": context
        }

        try:
            # Get authentic autonomous reasoning
            reasoning_result = await autonomous_reasoning(
                domain="fraud_detection",
                input_data=input_data,
                agent_memory=self.memory,
                reasoning_depth="deep"
            )

            return {
                "conclusion": reasoning_result.get("reasoning_chain", ["Autonomous analysis completed"])[0],
                "risk_level": reasoning_result.get("risk_level", "medium"),
                "confidence": reasoning_result.get("confidence_score", 0.7),
                "fraud_indicators": reasoning_result.get("fraud_indicators", []),
                "recommended_actions": reasoning_result.get("recommended_actions", [])
            }

        except Exception as e:
            logger.error(f"Autonomous reasoning failed: {e}")
            # Even in error, no mock responses - return structured error
            return {
                "conclusion": f"Autonomous reasoning error: {str(e)}",
                "risk_level": "unknown",
                "confidence": 0.0,
                "fraud_indicators": [],
                "recommended_actions": ["require_manual_review"],
                "error": True
            }

    async def _decision_making_node(self, state: AgentState) -> AgentState:
        """AI analysis completion - SIU escalation for high-risk cases"""

        # Combine all analysis results
        amount_risk = state["fraud_analysis"]["amount_analysis"]["amount_to_limit_ratio"]
        pattern_risk = state["fraud_analysis"]["pattern_analysis"]["total_pattern_score"]

        # Include investigation results if available
        investigation_factor = 1.0
        if "investigation_results" in state:
            investigation_factor = state["investigation_results"]["credibility_score"]

        # Calculate final fraud score
        final_score = ((amount_risk * 0.3) + (pattern_risk * 0.5) + (0.2 * (1 - investigation_factor)))
        final_score = min(1.0, final_score)

        # Determine SIU escalation requirements (industry standard)
        siu_required = final_score > 0.7  # High fraud probability
        enhanced_investigation = final_score > 0.4  # Moderate risk

        if siu_required:
            recommendation = "SIU_ESCALATION_REQUIRED"
            action_required = "Licensed SIU investigator must review - potential fraud detected"
            regulatory_requirement = "State insurance regulations require SIU investigation"
        elif enhanced_investigation:
            recommendation = "ENHANCED_INVESTIGATION"
            action_required = "Senior claims adjuster review recommended"
            regulatory_requirement = "Enhanced documentation and investigation required"
        else:
            recommendation = "STANDARD_PROCESSING"
            action_required = "Standard claims processing may continue"
            regulatory_requirement = "Basic adjuster review required"

        state["fraud_analysis"]["final_analysis"] = {
            "fraud_score": final_score,
            "siu_escalation_required": siu_required,
            "enhanced_investigation_required": enhanced_investigation,
            "recommendation": recommendation,
            "action_required": action_required,
            "regulatory_requirement": regulatory_requirement,
            "confidence": state["confidence_score"],
            "human_decision_required": True,
            "ai_decision_prohibited": "Industry standards prohibit AI-only fraud decisions"
        }

        state["reasoning_chain"].append(f"AI analysis complete: {recommendation} (Score: {final_score:.2f})")

        return state

    async def _learning_node(self, state: AgentState) -> AgentState:
        """Learning node to update agent memory"""
        
        # Create learning experience
        experience = {
            "claim_id": state["claim_data"].get("claim_id"),
            "fraud_score": state["fraud_analysis"]["final_decision"]["fraud_score"],
            "decision": state["fraud_analysis"]["final_decision"]["decision"],
            "patterns_used": len(state["fraud_analysis"]["pattern_analysis"]["pattern_matches"]),
            "reasoning_steps": len(state["reasoning_chain"])
        }
        
        # Update memory
        self.memory = update_agent_memory.invoke({"memory_data": self.memory, "new_experience": experience})
        state["agent_memory"] = self.memory
        
        state["reasoning_chain"].append("Learning complete - experience stored in memory")
        
        return state

    def _should_investigate_deeper(self, state: AgentState) -> str:
        """Conditional logic to determine if deep investigation is needed"""
        confidence = state["confidence_score"]
        pattern_matches = len(state["fraud_analysis"]["pattern_analysis"]["pattern_matches"])
        
        if confidence > 0.6 or pattern_matches > 1:
            return "investigate"
        else:
            return "decide"

    async def analyze_claim_with_langgraph(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze claim using LangGraph workflow"""
        
        # Initialize state
        initial_state = AgentState(
            messages=[HumanMessage(content=f"Analyze claim: {claim_data.get('claim_id')}")],
            claim_data=claim_data,
            fraud_analysis={},
            investigation_results={},
            agent_memory=self.memory,
            next_action="analyze_claim",
            confidence_score=0.0,
            reasoning_chain=[]
        )
        
        # Execute the workflow
        try:
            final_state = await self.app.ainvoke(initial_state)
            
            return {
                "agent_id": self.agent_id,
                "claim_id": claim_data.get("claim_id"),
                "langgraph_workflow": "completed",
                "fraud_analysis": final_state["fraud_analysis"],
                "investigation_results": final_state.get("investigation_results", {}),
                "reasoning_chain": final_state["reasoning_chain"],
                "agent_memory_updated": True,
                "workflow_type": "langgraph_state_machine",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LangGraph workflow error: {str(e)}")
            return {
                "error": f"Workflow execution failed: {str(e)}",
                "agent_id": self.agent_id,
                "workflow_type": "langgraph_state_machine"
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        return {
            "agent_id": self.agent_id,
            "framework": "LangGraph + LangChain",
            "workflow_type": "state_machine_graph",
            "autonomous": True,
            "capabilities": [
                "graph_based_reasoning",
                "conditional_workflows", 
                "tool_execution",
                "memory_management",
                "state_persistence"
            ],
            "memory_experiences": len(self.memory.get("experiences", [])),
            "fraud_patterns": len(self.fraud_patterns),
            "workflow_nodes": 6,
            "tools_available": 4,
            "last_updated": datetime.utcnow().isoformat()
        }

# FastAPI Application
app = FastAPI(
    title="LangGraph Agentic Fraud Detection",
    description="Advanced agentic AI using LangGraph state machines",
    version="3.0.0"
)

# Global agent instance
langgraph_agent: Optional[LangGraphFraudAgent] = None

@app.on_event("startup")
async def startup_event():
    global langgraph_agent
    langgraph_agent = LangGraphFraudAgent()
    logger.info("LangGraph Agentic Fraud Agent started")

@app.get("/health")
async def health_check():
    """Health check with LangGraph agent status"""
    if langgraph_agent:
        status = langgraph_agent.get_agent_status()
        return {
            "status": "healthy",
            "service": "langgraph-fraud-agent",
            "framework": "LangGraph + LangChain",
            "agent_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
    return {"status": "initializing"}

@app.post("/analyze")
async def analyze_claim(claim_data: Dict[str, Any]):
    """Analyze claim using LangGraph workflow"""
    if not langgraph_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await langgraph_agent.analyze_claim_with_langgraph(claim_data)
    return result

@app.get("/workflow")
async def get_workflow_info():
    """Get LangGraph workflow information"""
    if langgraph_agent:
        return {
            "workflow_type": "LangGraph State Machine",
            "nodes": [
                "analyze_claim",
                "pattern_matching", 
                "deep_investigation",
                "reasoning",
                "decision_making",
                "learning"
            ],
            "tools": [
                "analyze_claim_amount",
                "check_fraud_patterns",
                "investigate_claimant_history", 
                "update_agent_memory"
            ],
            "conditional_routing": True,
            "state_persistence": True
        }
    return {"error": "Agent not initialized"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LangGraph Agentic Fraud Detection Agent",
        "version": "3.0.0",
        "framework": "LangGraph + LangChain",
        "capabilities": [
            "graph_based_workflows",
            "conditional_routing",
            "tool_execution", 
            "state_management",
            "advanced_reasoning"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
