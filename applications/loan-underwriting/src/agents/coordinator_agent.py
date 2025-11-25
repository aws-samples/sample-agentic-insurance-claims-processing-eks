"""
LangGraph Coordinator Agent for Intelligent Loan Underwriting
Orchestrates multi-agent underwriting workflow with autonomous decision-making
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, TypedDict, Annotated
import operator
import os

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage

# Import local modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_models import (
    LoanApplication, LoanStatus, RiskLevel,
    CreditAnalysis, IncomeVerification, RiskAssessment,
    ComplianceCheck, UnderwritingDecision
)
from shared.llm_integration import init_underwriting_llm

logger = logging.getLogger(__name__)


# ============================================================================
# State Definition for LangGraph
# ============================================================================

class UnderwritingState(TypedDict):
    """State object passed between agents in the workflow"""
    # Application data
    application: Dict[str, Any]
    application_id: str

    # Agent outputs
    credit_analysis: Dict[str, Any]
    income_verification: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    compliance_check: Dict[str, Any]
    final_decision: Dict[str, Any]

    # Workflow control
    current_step: str
    errors: Annotated[List[str], operator.add]
    agent_logs: Annotated[List[Dict], operator.add]
    requires_human_review: bool

    # Metadata
    started_at: datetime
    processing_time_seconds: float


# ============================================================================
# Coordinator Agent Class
# ============================================================================

class LoanUnderwritingCoordinator:
    """
    Main coordinator agent that orchestrates the loan underwriting workflow
    Uses LangGraph for state management and agent coordination
    """

    def __init__(self, ollama_endpoint: str = "http://ollama-service:11434"):
        self.agent_id = "coordinator_001"
        self.ollama_endpoint = ollama_endpoint

        # Initialize LLM for coordination decisions
        model_name = os.getenv("MODEL_NAME", "qwen3-coder")
        self.llm = ChatOllama(
            base_url=ollama_endpoint,
            model=model_name,
            temperature=0.3
        )

        # Initialize specialized LLM engine
        try:
            self.llm_engine = init_underwriting_llm(
                agent_id=self.agent_id,
                agent_type="coordinator",
                ollama_endpoint=ollama_endpoint
            )
            logger.info("Initialized coordinator LLM engine")
        except Exception as e:
            logger.error(f"Failed to initialize LLM engine: {e}")
            self.llm_engine = None

        # Initialize LangGraph workflow
        self.workflow = self._create_workflow()

        # Performance metrics
        self.applications_processed = 0
        self.total_processing_time = 0.0

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for loan underwriting"""

        # Create the graph
        workflow = StateGraph(UnderwritingState)

        # Add nodes for each agent (using run_ prefix to avoid conflicts with state keys)
        workflow.add_node("run_credit_analysis", self._credit_analysis_node)
        workflow.add_node("run_income_verification", self._income_verification_node)
        workflow.add_node("run_risk_assessment", self._risk_assessment_node)
        workflow.add_node("run_compliance_check", self._compliance_check_node)
        workflow.add_node("run_make_decision", self._make_decision_node)
        workflow.add_node("run_human_review", self._human_review_node)

        # Define the workflow edges
        workflow.set_entry_point("run_credit_analysis")

        # Sequential flow with conditional branching
        workflow.add_edge("run_credit_analysis", "run_income_verification")
        workflow.add_edge("run_income_verification", "run_risk_assessment")
        workflow.add_edge("run_risk_assessment", "run_compliance_check")

        # After compliance check, decide if human review is needed
        workflow.add_conditional_edges(
            "run_compliance_check",
            self._should_require_human_review,
            {
                "human_review": "run_human_review",
                "make_decision": "run_make_decision"
            }
        )

        workflow.add_edge("run_human_review", "run_make_decision")
        workflow.add_edge("run_make_decision", END)

        return workflow.compile()

    # ========================================================================
    # Agent Node Functions
    # ========================================================================

    async def _credit_analysis_node(self, state: UnderwritingState) -> Dict:
        """Credit analysis agent node"""
        logger.info(f"[{state['application_id']}] Starting credit analysis")

        try:
            if self.llm_engine:
                result = self.llm_engine.analyze_credit(state['application'])
            else:
                result = self._mock_credit_analysis(state['application'])

            state['credit_analysis'] = result
            state['current_step'] = "credit_analysis"
            state['agent_logs'].append({
                "agent": "credit_analysis",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "summary": result.get('analysis_summary', '')
            })

            logger.info(f"[{state['application_id']}] Credit analysis completed: {result.get('recommendation')}")

        except Exception as e:
            logger.error(f"Credit analysis failed: {e}")
            state['errors'].append(f"Credit analysis error: {str(e)}")
            state['credit_analysis'] = {"error": str(e), "recommendation": "review"}

        return state

    async def _income_verification_node(self, state: UnderwritingState) -> Dict:
        """Income verification agent node"""
        logger.info(f"[{state['application_id']}] Starting income verification")

        try:
            documents = state['application'].get('uploaded_documents', [])

            if self.llm_engine:
                result = self.llm_engine.verify_income(state['application'], documents)
            else:
                result = self._mock_income_verification(state['application'])

            state['income_verification'] = result
            state['current_step'] = "income_verification"
            state['agent_logs'].append({
                "agent": "income_verification",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "verified_income": result.get('verified_monthly_income', 0)
            })

            logger.info(f"[{state['application_id']}] Income verification completed")

        except Exception as e:
            logger.error(f"Income verification failed: {e}")
            state['errors'].append(f"Income verification error: {str(e)}")
            state['income_verification'] = {"error": str(e), "recommendation": "flag_for_review"}

        return state

    async def _risk_assessment_node(self, state: UnderwritingState) -> Dict:
        """Risk assessment agent node"""
        logger.info(f"[{state['application_id']}] Starting risk assessment")

        try:
            if self.llm_engine:
                result = self.llm_engine.assess_risk(
                    state['application'],
                    state['credit_analysis'],
                    state['income_verification']
                )
            else:
                result = self._mock_risk_assessment(state)

            state['risk_assessment'] = result
            state['current_step'] = "risk_assessment"
            state['agent_logs'].append({
                "agent": "risk_assessment",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "risk_level": result.get('overall_risk_level'),
                "recommendation": result.get('recommendation')
            })

            logger.info(f"[{state['application_id']}] Risk assessment completed: {result.get('overall_risk_level')}")

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            state['errors'].append(f"Risk assessment error: {str(e)}")
            state['risk_assessment'] = {"error": str(e), "recommendation": "deny"}

        return state

    async def _compliance_check_node(self, state: UnderwritingState) -> Dict:
        """Compliance check agent node"""
        logger.info(f"[{state['application_id']}] Starting compliance check")

        try:
            underwriting_data = {
                "credit_analysis": state.get('credit_analysis', {}),
                "income_verification": state.get('income_verification', {}),
                "risk_assessment": state.get('risk_assessment', {})
            }

            if self.llm_engine:
                result = self.llm_engine.check_compliance(
                    state['application'],
                    underwriting_data
                )
            else:
                result = self._mock_compliance_check()

            state['compliance_check'] = result
            state['current_step'] = "compliance_check"
            state['agent_logs'].append({
                "agent": "compliance",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "compliant": result.get('compliant', True),
                "violations": len(result.get('violations', []))
            })

            logger.info(f"[{state['application_id']}] Compliance check completed")

        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            state['errors'].append(f"Compliance check error: {str(e)}")
            state['compliance_check'] = {"error": str(e), "compliant": False}

        return state

    async def _make_decision_node(self, state: UnderwritingState) -> Dict:
        """Make final underwriting decision"""
        logger.info(f"[{state['application_id']}] Making final decision")

        try:
            all_analyses = {
                "application": state['application'],
                "credit_analysis": state.get('credit_analysis', {}),
                "income_verification": state.get('income_verification', {}),
                "risk_assessment": state.get('risk_assessment', {}),
                "compliance_check": state.get('compliance_check', {})
            }

            if self.llm_engine:
                result = self.llm_engine.make_underwriting_decision(all_analyses)
            else:
                result = self._mock_final_decision(state)

            # Calculate processing time
            processing_time = (datetime.utcnow() - state['started_at']).total_seconds()
            state['processing_time_seconds'] = processing_time

            state['final_decision'] = result
            state['current_step'] = "completed"
            state['agent_logs'].append({
                "agent": "coordinator",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
                "decision": result.get('decision'),
                "confidence": result.get('confidence_score'),
                "processing_time_seconds": processing_time
            })

            logger.info(f"[{state['application_id']}] Decision: {result.get('decision')} "
                       f"(confidence: {result.get('confidence_score')}%)")

        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            state['errors'].append(f"Decision error: {str(e)}")
            state['final_decision'] = {
                "decision": "denied",
                "denial_reasons": ["System error during decision making"],
                "human_review_required": True
            }

        return state

    async def _human_review_node(self, state: UnderwritingState) -> Dict:
        """Flag application for human review"""
        logger.info(f"[{state['application_id']}] Flagged for human review")

        state['requires_human_review'] = True
        state['agent_logs'].append({
            "agent": "human_review_coordinator",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending_human_review",
            "reason": "High-risk or complex application"
        })

        return state

    def _should_require_human_review(self, state: UnderwritingState) -> str:
        """Determine if human review is required"""

        # Check for compliance violations
        compliance = state.get('compliance_check', {})
        if not compliance.get('compliant', True):
            return "human_review"

        # Check risk level
        risk = state.get('risk_assessment', {})
        if risk.get('overall_risk_level') in ['high', 'very_high']:
            return "human_review"

        # Check for significant discrepancies
        income_ver = state.get('income_verification', {})
        if len(income_ver.get('discrepancies', [])) > 2:
            return "human_review"

        # Check for errors
        if len(state.get('errors', [])) > 0:
            return "human_review"

        return "make_decision"

    # ========================================================================
    # Main Processing Function
    # ========================================================================

    async def process_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a loan application through the complete underwriting workflow

        Args:
            application_data: Complete loan application data

        Returns:
            Processing results including decision and all agent analyses
        """

        application_id = application_data.get('application_id', 'UNKNOWN')
        logger.info(f"Starting underwriting process for {application_id}")

        # Initialize state
        initial_state: UnderwritingState = {
            "application": application_data,
            "application_id": application_id,
            "credit_analysis": {},
            "income_verification": {},
            "risk_assessment": {},
            "compliance_check": {},
            "final_decision": {},
            "current_step": "initialized",
            "errors": [],
            "agent_logs": [],
            "requires_human_review": False,
            "started_at": datetime.utcnow(),
            "processing_time_seconds": 0.0
        }

        try:
            # Execute the workflow
            final_state = await self.workflow.ainvoke(initial_state)

            # Update metrics
            self.applications_processed += 1
            self.total_processing_time += final_state['processing_time_seconds']

            return {
                "application_id": application_id,
                "status": "completed",
                "decision": final_state.get('final_decision', {}),
                "credit_analysis": final_state.get('credit_analysis', {}),
                "income_verification": final_state.get('income_verification', {}),
                "risk_assessment": final_state.get('risk_assessment', {}),
                "compliance_check": final_state.get('compliance_check', {}),
                "requires_human_review": final_state.get('requires_human_review', False),
                "processing_time_seconds": final_state['processing_time_seconds'],
                "agent_logs": final_state.get('agent_logs', []),
                "errors": final_state.get('errors', [])
            }

        except Exception as e:
            logger.error(f"Workflow execution failed for {application_id}: {e}")
            return {
                "application_id": application_id,
                "status": "error",
                "error": str(e),
                "decision": {
                    "decision": "denied",
                    "denial_reasons": [f"System error: {str(e)}"],
                    "human_review_required": True
                }
            }

    # ========================================================================
    # Mock Functions for Testing (when LLM is unavailable)
    # ========================================================================

    def _mock_credit_analysis(self, application: Dict) -> Dict:
        """Mock credit analysis for testing"""
        financial_info = application.get('financial_info', {})
        credit_score = financial_info.get('credit_score', 650)

        return {
            "credit_risk_level": "low" if credit_score >= 720 else "medium" if credit_score >= 640 else "high",
            "payment_history_score": min(credit_score / 8.5, 100),
            "credit_utilization": 35.0,
            "risk_factors": ["Limited credit history"] if credit_score < 700 else [],
            "positive_factors": ["Good payment history"] if credit_score >= 700 else [],
            "analysis_summary": f"Credit score: {credit_score}",
            "recommendation": "approve" if credit_score >= 680 else "review"
        }

    def _mock_income_verification(self, application: Dict) -> Dict:
        """Mock income verification for testing"""
        financial_info = application.get('financial_info', {})
        monthly_income = financial_info.get('monthly_income', 0)

        return {
            "verified_monthly_income": monthly_income,
            "verification_confidence": 85.0,
            "employment_verified": True,
            "income_stability_score": 80.0,
            "discrepancies": [],
            "verification_notes": "Income verified through paystubs",
            "recommendation": "accept"
        }

    def _mock_risk_assessment(self, state: Dict) -> Dict:
        """Mock risk assessment for testing"""
        return {
            "overall_risk_level": "medium",
            "risk_score": 45.0,
            "probability_of_default": 12.0,
            "risk_factors": [
                {"factor": "debt_to_income", "severity": "medium", "explanation": "DTI at 38%"}
            ],
            "mitigating_factors": ["Stable employment", "Good credit history"],
            "recommendation": "approve_with_conditions",
            "recommended_interest_rate": 6.5,
            "recommended_loan_amount": state['application']['loan_details']['requested_amount'],
            "conditions": ["Maintain employment", "Debt-to-income monitoring"]
        }

    def _mock_compliance_check(self) -> Dict:
        """Mock compliance check for testing"""
        return {
            "compliant": True,
            "regulations_checked": ["ECOA", "TILA", "ATR"],
            "violations": [],
            "warnings": [],
            "fair_lending_check": True,
            "ability_to_repay_verified": True,
            "required_disclosures": ["TILA disclosure", "Privacy notice"],
            "compliance_notes": "All regulatory requirements met"
        }

    def _mock_final_decision(self, state: Dict) -> Dict:
        """Mock final decision for testing"""
        loan_details = state['application'].get('loan_details', {})

        return {
            "decision": "conditionally_approved",
            "approved_amount": loan_details.get('requested_amount'),
            "approved_term_months": loan_details.get('loan_term_months'),
            "interest_rate": 6.5,
            "monthly_payment": 500.0,
            "conditions": ["Submit final paystub", "Maintain employment"],
            "denial_reasons": [],
            "decision_explanation": "Application meets underwriting guidelines with conditions",
            "confidence_score": 85.0,
            "human_review_required": False
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get coordinator performance metrics"""
        avg_time = (self.total_processing_time / self.applications_processed
                   if self.applications_processed > 0 else 0)

        return {
            "applications_processed": self.applications_processed,
            "average_processing_time_seconds": avg_time,
            "llm_metrics": self.llm_engine.get_performance_metrics() if self.llm_engine else {}
        }


# ============================================================================
# Singleton Instance
# ============================================================================

_coordinator_instance = None

def get_coordinator(ollama_endpoint: str = None) -> LoanUnderwritingCoordinator:
    """Get or create coordinator singleton"""
    global _coordinator_instance
    if _coordinator_instance is None:
        _coordinator_instance = LoanUnderwritingCoordinator(
            ollama_endpoint=ollama_endpoint or os.getenv("OLLAMA_ENDPOINT", "http://ollama-service:11434")
        )
    return _coordinator_instance
