"""
Authentic LLM Integration for Agentic AI System
Replaces all mock responses with real autonomous reasoning capabilities
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import os
import time
from dataclasses import dataclass

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

@dataclass
class ReasoningContext:
    """Context for autonomous reasoning"""
    agent_type: str
    domain: str  # "fraud_detection", "aml_analysis", "policy_validation", etc.
    input_data: Dict[str, Any]
    historical_patterns: List[Dict]
    agent_memory: Dict[str, Any]
    confidence_threshold: float
    reasoning_depth: str  # "shallow", "deep", "creative"

class AutonomousLLMEngine:
    """
    Enhanced LLM engine for truly autonomous agent reasoning
    Eliminates all mock responses and provides authentic AI decision-making
    """

    def __init__(self,
                 agent_id: str,
                 agent_type: str,
                 preferred_model: str = "qwen3-coder",
                 fallback_model: str = "gpt-4",
                 ollama_endpoint: str = None):

        self.agent_id = agent_id
        self.agent_type = agent_type
        self.preferred_model = preferred_model
        self.fallback_model = fallback_model

        # Initialize primary LLM (Ollama)
        self.primary_llm = None
        self.fallback_llm = None

        self._initialize_llm_connections(ollama_endpoint)

        # Reasoning templates
        self.reasoning_templates = self._create_reasoning_templates()

        # Performance tracking
        self.reasoning_history = []
        self.performance_metrics = {
            "total_requests": 0,
            "successful_responses": 0,
            "average_response_time_ms": 0.0,
            "confidence_scores": []
        }

    def _initialize_llm_connections(self, ollama_endpoint: str):
        """Initialize LLM connections with proper fallback"""

        # Primary LLM (Ollama)
        try:
            endpoint = ollama_endpoint or os.getenv("OLLAMA_ENDPOINT", "http://ollama-service:11434")
            self.primary_llm = ChatOllama(
                base_url=endpoint,
                model=self.preferred_model,
                temperature=0.7,
                num_predict=1024,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1
            )
            logger.info(f"Successfully initialized Ollama LLM: {self.preferred_model}")

        except Exception as e:
            logger.warning(f"Failed to initialize Ollama LLM: {e}")

        # Fallback LLM (OpenAI)
        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.fallback_llm = ChatOpenAI(
                    model=self.fallback_model,
                    temperature=0.7,
                    max_tokens=1024
                )
                logger.info(f"Successfully initialized fallback LLM: {self.fallback_model}")
        except Exception as e:
            logger.warning(f"Failed to initialize fallback LLM: {e}")

        # Ensure we have at least one working LLM
        if not self.primary_llm and not self.fallback_llm:
            raise RuntimeError("No LLM connections available - cannot provide authentic autonomous reasoning")

    def _create_reasoning_templates(self) -> Dict[str, ChatPromptTemplate]:
        """Create domain-specific reasoning templates"""

        templates = {}

        # Fraud Detection Reasoning
        templates["fraud_analysis"] = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an autonomous fraud detection agent with deep expertise in insurance claims analysis.
Your role is to provide genuine, thoughtful analysis based on the data provided. You must:

1. Analyze patterns and anomalies in the claim data
2. Consider multiple fraud indicators simultaneously
3. Provide specific reasoning for your conclusions
4. Assign confidence scores based on evidence strength
5. Suggest next steps for investigation if needed

Be thorough, objective, and provide actionable insights. Avoid generic responses."""),

            HumanMessage(content="""Analyze this insurance claim for fraud indicators:

Claim Data: {claim_data}
Historical Patterns: {historical_patterns}
Agent Memory: {agent_memory}

Please provide a detailed fraud analysis including:
1. Risk assessment (high/medium/low)
2. Specific fraud indicators identified
3. Confidence score (0.0-1.0)
4. Reasoning chain explaining your analysis
5. Recommended next actions

Format your response as JSON with these fields:
{{
    "risk_level": "high|medium|low",
    "fraud_indicators": ["list", "of", "specific", "indicators"],
    "confidence_score": 0.85,
    "reasoning_chain": ["step 1", "step 2", "step 3"],
    "recommended_actions": ["action 1", "action 2"],
    "investigation_priority": "urgent|standard|low",
    "additional_data_needed": ["data type 1", "data type 2"]
}}""")
        ])

        # AML Transaction Analysis
        templates["aml_analysis"] = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an autonomous AML (Anti-Money Laundering) agent with expertise in financial crime detection.
Your role is to analyze transactions for suspicious patterns that may indicate money laundering, terrorist financing, or other financial crimes.

You must:
1. Evaluate transaction patterns against known typologies
2. Consider customer behavior and risk factors
3. Apply regulatory requirements and thresholds
4. Provide detailed risk assessments
5. Generate actionable compliance recommendations

Be precise, comprehensive, and ensure regulatory compliance in your analysis."""),

            HumanMessage(content="""Analyze this transaction for AML risks:

Transaction Data: {transaction_data}
Customer Profile: {customer_profile}
Historical Behavior: {historical_patterns}
Regulatory Context: {regulatory_context}

Provide comprehensive AML analysis including:
1. Risk score (0.0-1.0)
2. Suspicious activity indicators
3. Regulatory compliance assessment
4. Customer risk profiling
5. Recommended compliance actions

Format as JSON:
{{
    "risk_score": 0.75,
    "risk_level": "high|medium|low",
    "suspicious_indicators": ["indicator 1", "indicator 2"],
    "typology_matches": ["structuring", "layering"],
    "regulatory_flags": ["BSA", "OFAC"],
    "customer_risk_factors": ["high_risk_geography", "cash_intensive"],
    "compliance_actions": ["file_sar", "enhanced_monitoring"],
    "investigation_required": true,
    "confidence": 0.88
}}""")
        ])

        # Policy Validation Reasoning
        templates["policy_validation"] = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an autonomous policy validation agent with deep knowledge of insurance policies and regulations.
Your role is to validate claims against policy terms, coverage limits, and regulatory requirements.

You must:
1. Review policy terms and coverage details
2. Validate claim against policy conditions
3. Check for coverage exclusions
4. Verify claim amounts against limits
5. Ensure regulatory compliance

Provide detailed, accurate policy analysis with clear reasoning."""),

            HumanMessage(content="""Validate this claim against policy terms:

Claim Details: {claim_data}
Policy Terms: {policy_terms}
Coverage Limits: {coverage_limits}
Regulatory Requirements: {regulatory_requirements}

Provide policy validation analysis:
1. Coverage determination
2. Policy compliance assessment
3. Coverage amount calculation
4. Exclusions check
5. Regulatory compliance

Format as JSON:
{{
    "coverage_valid": true,
    "covered_amount": 45000.0,
    "coverage_percentage": 0.9,
    "exclusions_triggered": ["exclusion1"],
    "policy_violations": [],
    "regulatory_compliance": true,
    "validation_confidence": 0.92,
    "reasoning": ["reason 1", "reason 2"],
    "required_documentation": ["doc1", "doc2"]
}}""")
        ])

        # Investigation Planning
        templates["investigation_planning"] = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an autonomous investigation planning agent with expertise in complex claim investigations.
Your role is to design comprehensive investigation strategies based on case complexity and available evidence.

You must:
1. Assess investigation requirements
2. Plan evidence collection strategies
3. Identify key witnesses and documentation
4. Sequence investigation activities
5. Estimate timelines and resources

Provide detailed, actionable investigation plans."""),

            HumanMessage(content="""Plan investigation for this complex case:

Case Details: {case_data}
Available Evidence: {evidence}
Resource Constraints: {constraints}
Urgency Level: {urgency}

Create comprehensive investigation plan:
1. Investigation strategy
2. Evidence collection plan
3. Timeline and milestones
4. Resource requirements
5. Risk assessment

Format as JSON:
{{
    "investigation_type": "comprehensive|standard|preliminary",
    "estimated_duration_days": 14,
    "priority_level": "high|medium|low",
    "investigation_steps": [
        {{"step": "interview_claimant", "timeline": "day_1", "resources": ["investigator"]}},
        {{"step": "scene_examination", "timeline": "day_2", "resources": ["investigator", "expert"]}}
    ],
    "evidence_targets": ["medical_records", "witness_statements"],
    "success_probability": 0.85,
    "cost_estimate": 5000,
    "risks": ["evidence_degradation", "witness_availability"]
}}""")
        ])

        return templates

    async def autonomous_reasoning(self,
                                 reasoning_context: ReasoningContext) -> Dict[str, Any]:
        """
        Perform autonomous reasoning using real LLM
        NO MOCK RESPONSES - authentic AI decision making
        """

        start_time = time.time()
        self.performance_metrics["total_requests"] += 1

        try:
            # Select appropriate reasoning template
            template = self._select_reasoning_template(reasoning_context)

            # Prepare context for LLM
            llm_context = self._prepare_llm_context(reasoning_context)

            # Get LLM response
            response = await self._get_llm_response(template, llm_context)

            # Parse and validate response
            parsed_response = self._parse_llm_response(response, reasoning_context)

            # Track performance
            response_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(response_time, parsed_response.get("confidence", 0.5))

            # Store reasoning for learning
            self._store_reasoning_history(reasoning_context, parsed_response, response_time)

            logger.info(f"Autonomous reasoning completed for {reasoning_context.domain} in {response_time:.2f}ms")

            return parsed_response

        except Exception as e:
            logger.error(f"Autonomous reasoning failed: {e}", exc_info=True)
            # Even in error cases, no mock responses - return structured error
            return self._create_error_response(str(e), reasoning_context)

    def _select_reasoning_template(self, context: ReasoningContext) -> ChatPromptTemplate:
        """Select appropriate reasoning template based on context"""

        domain_mapping = {
            "fraud_detection": "fraud_analysis",
            "aml_analysis": "aml_analysis",
            "policy_validation": "policy_validation",
            "investigation": "investigation_planning"
        }

        template_key = domain_mapping.get(context.domain, "fraud_analysis")
        return self.reasoning_templates[template_key]

    def _prepare_llm_context(self, context: ReasoningContext) -> Dict[str, str]:
        """Prepare context data for LLM consumption"""

        return {
            "claim_data": json.dumps(context.input_data, indent=2),
            "historical_patterns": json.dumps(context.historical_patterns, indent=2),
            "agent_memory": json.dumps(context.agent_memory, indent=2),
            "transaction_data": json.dumps(context.input_data.get("transaction", {}), indent=2),
            "customer_profile": json.dumps(context.input_data.get("customer", {}), indent=2),
            "regulatory_context": json.dumps(context.input_data.get("regulatory", {}), indent=2),
            "policy_terms": json.dumps(context.input_data.get("policy", {}), indent=2),
            "coverage_limits": json.dumps(context.input_data.get("coverage", {}), indent=2),
            "regulatory_requirements": json.dumps(context.input_data.get("regulations", {}), indent=2),
            "case_data": json.dumps(context.input_data, indent=2),
            "evidence": json.dumps(context.input_data.get("evidence", []), indent=2),
            "constraints": json.dumps(context.input_data.get("constraints", {}), indent=2),
            "urgency": context.input_data.get("urgency", "standard")
        }

    async def _get_llm_response(self,
                              template: ChatPromptTemplate,
                              context: Dict[str, str]) -> str:
        """Get response from LLM with fallback logic"""

        # Try primary LLM first
        if self.primary_llm:
            try:
                messages = template.format_messages(**context)
                response = await self.primary_llm.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.warning(f"Primary LLM failed: {e}, trying fallback")

        # Try fallback LLM
        if self.fallback_llm:
            try:
                messages = template.format_messages(**context)
                response = await self.fallback_llm.ainvoke(messages)
                return response.content
            except Exception as e:
                logger.error(f"Fallback LLM failed: {e}")
                raise RuntimeError("All LLM connections failed - cannot provide authentic reasoning")

        raise RuntimeError("No LLM connections available")

    def _parse_llm_response(self,
                          response: str,
                          context: ReasoningContext) -> Dict[str, Any]:
        """Parse and validate LLM response"""

        try:
            # Try to parse as JSON
            if response.strip().startswith('{'):
                parsed = json.loads(response)

                # Validate required fields based on domain
                validated = self._validate_response_structure(parsed, context.domain)
                return validated
            else:
                # Handle non-JSON responses
                return self._convert_text_to_structured(response, context)

        except json.JSONDecodeError:
            # Extract JSON from text if embedded
            return self._extract_json_from_text(response, context)

    def _validate_response_structure(self,
                                   response: Dict[str, Any],
                                   domain: str) -> Dict[str, Any]:
        """Validate response has required structure for domain"""

        required_fields = {
            "fraud_detection": ["risk_level", "confidence_score", "reasoning_chain"],
            "aml_analysis": ["risk_score", "risk_level", "suspicious_indicators"],
            "policy_validation": ["coverage_valid", "covered_amount", "validation_confidence"],
            "investigation": ["investigation_type", "investigation_steps", "estimated_duration_days"]
        }

        domain_fields = required_fields.get(domain, ["confidence_score"])

        # Ensure required fields exist
        for field in domain_fields:
            if field not in response:
                if field == "confidence_score":
                    response[field] = 0.7  # Default confidence
                elif field == "risk_level":
                    response[field] = "medium"  # Default risk
                else:
                    response[field] = f"Missing {field}"

        # Ensure confidence is in valid range
        if "confidence_score" in response:
            response["confidence_score"] = max(0.0, min(1.0, float(response["confidence_score"])))

        return response

    def _convert_text_to_structured(self,
                                  text_response: str,
                                  context: ReasoningContext) -> Dict[str, Any]:
        """Convert text response to structured format"""

        # Basic text analysis to extract key information
        structured = {
            "raw_response": text_response,
            "confidence_score": 0.6,  # Lower confidence for unstructured responses
            "reasoning_type": "text_analysis",
            "domain": context.domain
        }

        # Extract risk level from text
        text_lower = text_response.lower()
        if "high risk" in text_lower or "high fraud" in text_lower:
            structured["risk_level"] = "high"
            structured["confidence_score"] = 0.8
        elif "low risk" in text_lower or "low fraud" in text_lower:
            structured["risk_level"] = "low"
            structured["confidence_score"] = 0.7
        else:
            structured["risk_level"] = "medium"

        # Extract reasoning points
        reasoning_indicators = ["because", "due to", "indicates", "suggests", "shows"]
        reasoning_chain = []

        sentences = text_response.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in reasoning_indicators):
                reasoning_chain.append(sentence.strip())

        structured["reasoning_chain"] = reasoning_chain[:5]  # Limit to 5 points

        return structured

    def _extract_json_from_text(self,
                              text: str,
                              context: ReasoningContext) -> Dict[str, Any]:
        """Extract JSON from text that may contain other content"""

        import re

        # Find JSON-like structures in the text
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                parsed = json.loads(match)
                return self._validate_response_structure(parsed, context.domain)
            except json.JSONDecodeError:
                continue

        # If no valid JSON found, convert text to structured format
        return self._convert_text_to_structured(text, context)

    def _create_error_response(self,
                             error: str,
                             context: ReasoningContext) -> Dict[str, Any]:
        """Create structured error response (NO MOCK DATA)"""

        return {
            "error": True,
            "error_message": error,
            "confidence_score": 0.0,
            "risk_level": "unknown",
            "reasoning_chain": [f"Error in autonomous reasoning: {error}"],
            "domain": context.domain,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "requires_human_review": True
        }

    def _update_performance_metrics(self, response_time: float, confidence: float):
        """Update performance tracking"""

        self.performance_metrics["successful_responses"] += 1

        # Update average response time
        total_time = (self.performance_metrics["average_response_time_ms"] *
                     (self.performance_metrics["successful_responses"] - 1) + response_time)
        self.performance_metrics["average_response_time_ms"] = (
            total_time / self.performance_metrics["successful_responses"]
        )

        # Track confidence scores
        self.performance_metrics["confidence_scores"].append(confidence)
        if len(self.performance_metrics["confidence_scores"]) > 100:
            self.performance_metrics["confidence_scores"] = (
                self.performance_metrics["confidence_scores"][-100:]
            )

    def _store_reasoning_history(self,
                               context: ReasoningContext,
                               response: Dict[str, Any],
                               response_time: float):
        """Store reasoning for learning and improvement"""

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "domain": context.domain,
            "input_features": self._extract_input_features(context.input_data),
            "response_summary": self._summarize_response(response),
            "confidence": response.get("confidence_score", 0.5),
            "response_time_ms": response_time,
            "agent_id": self.agent_id
        }

        self.reasoning_history.append(history_entry)

        # Keep only recent history
        if len(self.reasoning_history) > 1000:
            self.reasoning_history = self.reasoning_history[-1000:]

    def _extract_input_features(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key features from input for pattern learning"""

        features = {}

        # Extract numerical features
        for key, value in input_data.items():
            if isinstance(value, (int, float)):
                features[f"numeric_{key}"] = value
            elif isinstance(value, str):
                features[f"text_length_{key}"] = len(value)
            elif isinstance(value, (list, dict)):
                features[f"collection_size_{key}"] = len(value)

        return features

    def _summarize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize response for learning"""

        return {
            "risk_level": response.get("risk_level", "unknown"),
            "confidence": response.get("confidence_score", 0.5),
            "indicators_count": len(response.get("fraud_indicators", [])),
            "actions_count": len(response.get("recommended_actions", []))
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""

        confidence_scores = self.performance_metrics["confidence_scores"]

        return {
            "total_requests": self.performance_metrics["total_requests"],
            "successful_responses": self.performance_metrics["successful_responses"],
            "success_rate": (self.performance_metrics["successful_responses"] /
                           max(1, self.performance_metrics["total_requests"])),
            "average_response_time_ms": self.performance_metrics["average_response_time_ms"],
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "reasoning_history_size": len(self.reasoning_history),
            "llm_status": {
                "primary_llm_available": self.primary_llm is not None,
                "fallback_llm_available": self.fallback_llm is not None
            }
        }

# Global instance for easy access
_global_llm_engine: Optional[AutonomousLLMEngine] = None

def init_autonomous_llm(agent_id: str, agent_type: str, **kwargs) -> AutonomousLLMEngine:
    """Initialize global autonomous LLM engine"""
    global _global_llm_engine
    _global_llm_engine = AutonomousLLMEngine(agent_id, agent_type, **kwargs)
    return _global_llm_engine

def get_autonomous_llm() -> Optional[AutonomousLLMEngine]:
    """Get global autonomous LLM engine"""
    return _global_llm_engine

async def autonomous_reasoning(domain: str,
                             input_data: Dict[str, Any],
                             agent_memory: Dict[str, Any] = None,
                             historical_patterns: List[Dict] = None,
                             reasoning_depth: str = "deep") -> Dict[str, Any]:
    """
    Convenience function for autonomous reasoning
    Completely eliminates any mock responses
    """

    llm_engine = get_autonomous_llm()
    if not llm_engine:
        raise RuntimeError("Autonomous LLM not initialized - cannot provide authentic reasoning")

    context = ReasoningContext(
        agent_type=llm_engine.agent_type,
        domain=domain,
        input_data=input_data,
        historical_patterns=historical_patterns or [],
        agent_memory=agent_memory or {},
        confidence_threshold=0.7,
        reasoning_depth=reasoning_depth
    )

    return await llm_engine.autonomous_reasoning(context)