"""
LLM Integration for Intelligent Loan Underwriting System
Provides autonomous AI reasoning for loan underwriting agents
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_ollama import ChatOllama

logger = logging.getLogger(__name__)


class UnderwritingLLMEngine:
    """
    LLM engine for autonomous loan underwriting decisions
    Uses qwen3-coder for intelligent analysis and decision-making
    """

    def __init__(self,
                 agent_id: str,
                 agent_type: str,
                 model: str = "qwen3-coder",
                 ollama_endpoint: str = None):

        self.agent_id = agent_id
        self.agent_type = agent_type
        self.model = model

        # Initialize LLM
        endpoint = ollama_endpoint or os.getenv("OLLAMA_ENDPOINT", "http://ollama-service:11434")

        try:
            self.llm = ChatOllama(
                base_url=endpoint,
                model=self.model,
                temperature=0.3,  # Balanced for financial decisions
                num_predict=2048,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1
            )
            logger.info(f"Initialized {agent_type} with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

        # Performance tracking
        self.request_count = 0
        self.successful_responses = 0

    def analyze_credit(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze credit information for loan application"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert credit analyst AI agent for loan underwriting.
Analyze the applicant's credit profile and provide a detailed assessment.

Consider:
- Credit score and history
- Payment history
- Credit utilization
- Recent inquiries
- Derogatory marks
- Debt-to-income ratio

Provide your analysis in JSON format with:
{{
    "credit_risk_level": "low|medium|high|very_high",
    "payment_history_score": <0-100>,
    "credit_utilization": <0-100>,
    "risk_factors": ["factor1", "factor2", ...],
    "positive_factors": ["factor1", "factor2", ...],
    "analysis_summary": "detailed summary",
    "recommendation": "approve|review|deny"
}}"""),
            ("human", "Analyze this credit profile:\n{application_data}")
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({"application_data": str(application_data)})
            self.request_count += 1
            self.successful_responses += 1
            return result
        except Exception as e:
            logger.error(f"Credit analysis failed: {e}")
            return self._get_fallback_credit_analysis()

    def verify_income(self, application_data: Dict[str, Any], documents: List[Dict]) -> Dict[str, Any]:
        """Verify income information from documents and employment data"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert income verification AI agent for loan underwriting.
Verify the applicant's stated income against provided documents and employment information.

Analyze:
- Paystubs and W2 forms
- Bank statements
- Employment history
- Income stability
- Additional income sources

Provide verification results in JSON format:
{{
    "verified_monthly_income": <amount>,
    "verification_confidence": <0-100>,
    "employment_verified": true/false,
    "income_stability_score": <0-100>,
    "discrepancies": ["discrepancy1", ...],
    "verification_notes": "detailed notes",
    "recommendation": "accept|flag_for_review|reject"
}}"""),
            ("human", "Verify income for:\nApplication: {application_data}\nDocuments: {documents}")
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({
                "application_data": str(application_data),
                "documents": str(documents)
            })
            self.request_count += 1
            self.successful_responses += 1
            return result
        except Exception as e:
            logger.error(f"Income verification failed: {e}")
            return self._get_fallback_income_verification()

    def assess_risk(self, application_data: Dict[str, Any],
                   credit_analysis: Dict, income_verification: Dict) -> Dict[str, Any]:
        """Comprehensive risk assessment combining all factors"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert risk assessment AI agent for loan underwriting.
Perform comprehensive risk analysis considering all available information.

Evaluate:
- Credit risk
- Income stability
- Debt-to-income ratio
- Loan-to-value ratio (if applicable)
- Employment stability
- Overall probability of default

Provide risk assessment in JSON format:
{{
    "overall_risk_level": "low|medium|high|very_high",
    "risk_score": <0-100>,
    "probability_of_default": <0-100>,
    "risk_factors": [
        {{"factor": "name", "severity": "high|medium|low", "explanation": "..."}}
    ],
    "mitigating_factors": ["factor1", ...],
    "recommendation": "approve|approve_with_conditions|deny",
    "recommended_interest_rate": <rate>,
    "recommended_loan_amount": <amount>,
    "conditions": ["condition1", ...]
}}"""),
            ("human", """Assess risk for:
Application: {application_data}
Credit Analysis: {credit_analysis}
Income Verification: {income_verification}""")
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({
                "application_data": str(application_data),
                "credit_analysis": str(credit_analysis),
                "income_verification": str(income_verification)
            })
            self.request_count += 1
            self.successful_responses += 1
            return result
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return self._get_fallback_risk_assessment()

    def check_compliance(self, application_data: Dict[str, Any],
                        underwriting_analysis: Dict) -> Dict[str, Any]:
        """Check regulatory compliance for fair lending and other regulations"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert compliance AI agent for loan underwriting.
Verify regulatory compliance including fair lending laws, ability-to-repay rules, and anti-discrimination laws.

Check compliance with:
- Equal Credit Opportunity Act (ECOA)
- Fair Housing Act (FHA)
- Truth in Lending Act (TILA)
- Ability-to-Repay (ATR) rules
- State-specific regulations

Provide compliance check in JSON format:
{{
    "compliant": true/false,
    "regulations_checked": ["regulation1", ...],
    "violations": [
        {{"regulation": "name", "violation": "description", "severity": "high|medium|low"}}
    ],
    "warnings": ["warning1", ...],
    "fair_lending_check": true/false,
    "ability_to_repay_verified": true/false,
    "required_disclosures": ["disclosure1", ...],
    "compliance_notes": "detailed notes"
}}"""),
            ("human", """Check compliance for:
Application: {application_data}
Underwriting Analysis: {underwriting_analysis}""")
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({
                "application_data": str(application_data),
                "underwriting_analysis": str(underwriting_analysis)
            })
            self.request_count += 1
            self.successful_responses += 1
            return result
        except Exception as e:
            logger.error(f"Compliance check failed: {e}")
            return self._get_fallback_compliance_check()

    def make_underwriting_decision(self, all_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Make final underwriting decision based on all agent analyses"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the coordinator AI agent for loan underwriting.
Make the final underwriting decision based on all agent analyses.

Synthesize information from:
- Credit analysis
- Income verification
- Risk assessment
- Compliance check

Make a clear decision with explanation in JSON format:
{{
    "decision": "approved|conditionally_approved|denied",
    "approved_amount": <amount or null>,
    "approved_term_months": <months or null>,
    "interest_rate": <rate or null>,
    "monthly_payment": <payment or null>,
    "conditions": ["condition1", ...],
    "denial_reasons": ["reason1", ...],
    "decision_explanation": "detailed explanation",
    "confidence_score": <0-100>,
    "human_review_required": true/false
}}"""),
            ("human", "Make underwriting decision based on:\n{all_analyses}")
        ])

        try:
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({"all_analyses": str(all_analyses)})
            self.request_count += 1
            self.successful_responses += 1
            return result
        except Exception as e:
            logger.error(f"Underwriting decision failed: {e}")
            return self._get_fallback_decision()

    # Fallback methods for error handling

    def _get_fallback_credit_analysis(self) -> Dict[str, Any]:
        """Fallback credit analysis when LLM fails"""
        return {
            "credit_risk_level": "high",
            "payment_history_score": 0,
            "credit_utilization": 0,
            "risk_factors": ["LLM analysis failed - manual review required"],
            "positive_factors": [],
            "analysis_summary": "Automated analysis unavailable - requires manual review",
            "recommendation": "review"
        }

    def _get_fallback_income_verification(self) -> Dict[str, Any]:
        """Fallback income verification when LLM fails"""
        return {
            "verified_monthly_income": 0,
            "verification_confidence": 0,
            "employment_verified": False,
            "income_stability_score": 0,
            "discrepancies": ["Automated verification failed"],
            "verification_notes": "Manual verification required",
            "recommendation": "flag_for_review"
        }

    def _get_fallback_risk_assessment(self) -> Dict[str, Any]:
        """Fallback risk assessment when LLM fails"""
        return {
            "overall_risk_level": "very_high",
            "risk_score": 100,
            "probability_of_default": 100,
            "risk_factors": [
                {"factor": "Automated risk assessment failed", "severity": "high",
                 "explanation": "Manual underwriting required"}
            ],
            "mitigating_factors": [],
            "recommendation": "deny",
            "recommended_interest_rate": None,
            "recommended_loan_amount": None,
            "conditions": ["Requires manual underwriting"]
        }

    def _get_fallback_compliance_check(self) -> Dict[str, Any]:
        """Fallback compliance check when LLM fails"""
        return {
            "compliant": False,
            "regulations_checked": [],
            "violations": [],
            "warnings": ["Automated compliance check failed - manual review required"],
            "fair_lending_check": False,
            "ability_to_repay_verified": False,
            "required_disclosures": [],
            "compliance_notes": "Manual compliance review required"
        }

    def _get_fallback_decision(self) -> Dict[str, Any]:
        """Fallback decision when LLM fails"""
        return {
            "decision": "denied",
            "approved_amount": None,
            "approved_term_months": None,
            "interest_rate": None,
            "monthly_payment": None,
            "conditions": [],
            "denial_reasons": ["Automated underwriting system unavailable"],
            "decision_explanation": "Application requires manual underwriting due to system unavailability",
            "confidence_score": 0,
            "human_review_required": True
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get LLM performance metrics"""
        success_rate = (self.successful_responses / self.request_count * 100) if self.request_count > 0 else 0

        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "model": self.model,
            "total_requests": self.request_count,
            "successful_responses": self.successful_responses,
            "success_rate": success_rate
        }


def init_underwriting_llm(agent_id: str, agent_type: str, **kwargs) -> UnderwritingLLMEngine:
    """Initialize LLM engine for underwriting agents"""
    return UnderwritingLLMEngine(agent_id=agent_id, agent_type=agent_type, **kwargs)
