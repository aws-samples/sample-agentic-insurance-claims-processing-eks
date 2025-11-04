"""
Inter-Agent Negotiation Protocol for Agentic AI System
Enables sophisticated negotiation, collaboration, and resource allocation between agents
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict

class NegotiationType(Enum):
    """Types of negotiations between agents"""
    RESOURCE_ALLOCATION = "resource_allocation"
    TASK_ASSIGNMENT = "task_assignment"
    INFORMATION_SHARING = "information_sharing"
    CONFLICT_RESOLUTION = "conflict_resolution"
    COLLABORATIVE_ANALYSIS = "collaborative_analysis"
    WORKLOAD_BALANCING = "workload_balancing"

class NegotiationStatus(Enum):
    """Status of ongoing negotiations"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    OFFER_MADE = "offer_made"
    COUNTER_OFFER = "counter_offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    COMPLETED = "completed"

class AgentRole(Enum):
    """Roles agents can take in negotiations"""
    INITIATOR = "initiator"
    RESPONDER = "responder"
    MEDIATOR = "mediator"
    OBSERVER = "observer"

@dataclass
class NegotiationOffer:
    """Represents an offer in agent negotiation"""
    offer_id: str
    from_agent: str
    to_agent: str
    negotiation_type: NegotiationType
    proposal: Dict[str, Any]
    resources_requested: Dict[str, float]
    resources_offered: Dict[str, float]
    constraints: List[str]
    priority: float
    confidence: float
    deadline: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class NegotiationHistory:
    """Track negotiation history for learning"""
    negotiation_id: str
    participants: List[str]
    negotiation_type: NegotiationType
    initial_positions: Dict[str, Dict]
    final_agreement: Optional[Dict]
    success: bool
    duration_ms: float
    rounds: int
    satisfaction_scores: Dict[str, float]
    lessons_learned: List[str]

@dataclass
class AgentCapability:
    """Represents an agent's capabilities for negotiation"""
    agent_id: str
    available_resources: Dict[str, float]  # e.g., {"cpu": 0.8, "memory": 0.6, "processing_slots": 3}
    expertise_areas: List[str]  # e.g., ["fraud_detection", "pattern_analysis"]
    current_workload: float  # 0.0 to 1.0
    collaboration_history: Dict[str, float]  # agent_id -> success_rate
    negotiation_style: str  # "cooperative", "competitive", "adaptive"
    trust_scores: Dict[str, float]  # agent_id -> trust_level

class AgentNegotiationEngine:
    """
    Sophisticated negotiation engine for inter-agent communication
    Enables resource sharing, task allocation, and collaborative decision making
    """

    def __init__(self, agent_id: str, agent_type: str, initial_capabilities: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_type = agent_type

        # Agent capabilities and state
        self.capabilities = AgentCapability(
            agent_id=agent_id,
            available_resources=initial_capabilities.get("resources", {}),
            expertise_areas=initial_capabilities.get("expertise", []),
            current_workload=0.0,
            collaboration_history={},
            negotiation_style="adaptive",
            trust_scores={}
        )

        # Active negotiations
        self.active_negotiations: Dict[str, Dict] = {}
        self.negotiation_history: List[NegotiationHistory] = []

        # Learning parameters
        self.learning_rate = 0.1
        self.trust_decay_rate = 0.02
        self.cooperation_threshold = 0.6

        # Communication handlers
        self.message_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.message_handlers.update({
            "negotiation_request": self._handle_negotiation_request,
            "offer": self._handle_offer,
            "counter_offer": self._handle_counter_offer,
            "acceptance": self._handle_acceptance,
            "rejection": self._handle_rejection,
            "resource_query": self._handle_resource_query,
            "collaboration_invite": self._handle_collaboration_invite
        })

    async def initiate_negotiation(self,
                                 target_agent: str,
                                 negotiation_type: NegotiationType,
                                 request: Dict[str, Any],
                                 max_duration_ms: int = 30000) -> str:
        """Initiate a negotiation with another agent"""

        negotiation_id = str(uuid.uuid4())
        deadline = datetime.utcnow() + timedelta(milliseconds=max_duration_ms)

        # Analyze own needs and capabilities
        initial_offer = self._formulate_initial_offer(
            target_agent, negotiation_type, request
        )

        negotiation = {
            "negotiation_id": negotiation_id,
            "type": negotiation_type,
            "participants": [self.agent_id, target_agent],
            "status": NegotiationStatus.INITIATED,
            "current_round": 1,
            "max_rounds": 10,
            "deadline": deadline,
            "initial_request": request,
            "current_offer": initial_offer,
            "history": [],
            "created_at": datetime.utcnow()
        }

        self.active_negotiations[negotiation_id] = negotiation

        # Send negotiation request
        await self._send_message(target_agent, "negotiation_request", {
            "negotiation_id": negotiation_id,
            "from_agent": self.agent_id,
            "type": negotiation_type.value,
            "initial_offer": initial_offer,
            "deadline": deadline.isoformat(),
            "request_details": request
        })

        return negotiation_id

    def _formulate_initial_offer(self,
                               target_agent: str,
                               negotiation_type: NegotiationType,
                               request: Dict[str, Any]) -> NegotiationOffer:
        """Formulate initial offer based on request and agent capabilities"""

        # Calculate what we can offer and what we need
        resources_offered = self._calculate_available_resources()
        resources_requested = self._extract_resource_requirements(request)

        # Adjust offer based on relationship with target agent
        trust_level = self.capabilities.trust_scores.get(target_agent, 0.5)
        collaboration_success = self.capabilities.collaboration_history.get(target_agent, 0.5)

        # Modify offering based on trust and history
        offer_generosity = (trust_level + collaboration_success) / 2
        for resource, amount in resources_offered.items():
            resources_offered[resource] = amount * offer_generosity

        # Generate constraints based on current workload
        constraints = self._generate_constraints()

        return NegotiationOffer(
            offer_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=target_agent,
            negotiation_type=negotiation_type,
            proposal=self._create_proposal(request, resources_offered, resources_requested),
            resources_requested=resources_requested,
            resources_offered=resources_offered,
            constraints=constraints,
            priority=request.get("priority", 0.5),
            confidence=self._calculate_offer_confidence(resources_offered, resources_requested),
            deadline=datetime.utcnow() + timedelta(minutes=5)
        )

    async def _handle_negotiation_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming negotiation request"""

        negotiation_id = message["negotiation_id"]
        from_agent = message["from_agent"]
        negotiation_type = NegotiationType(message["type"])
        initial_offer = message["initial_offer"]

        # Evaluate if we should participate
        should_participate = self._evaluate_negotiation_participation(
            from_agent, negotiation_type, initial_offer, message["request_details"]
        )

        if not should_participate:
            return await self._send_message(from_agent, "rejection", {
                "negotiation_id": negotiation_id,
                "reason": "insufficient_resources_or_interest",
                "alternative_suggestions": self._suggest_alternatives(message["request_details"])
            })

        # Create local negotiation state
        negotiation = {
            "negotiation_id": negotiation_id,
            "type": negotiation_type,
            "participants": [from_agent, self.agent_id],
            "status": NegotiationStatus.IN_PROGRESS,
            "current_round": 1,
            "role": AgentRole.RESPONDER,
            "peer_offer": initial_offer,
            "history": [initial_offer],
            "created_at": datetime.utcnow()
        }

        self.active_negotiations[negotiation_id] = negotiation

        # Formulate counter-offer
        counter_offer = self._formulate_counter_offer(from_agent, initial_offer, message["request_details"])

        # Send counter-offer
        return await self._send_message(from_agent, "counter_offer", {
            "negotiation_id": negotiation_id,
            "counter_offer": counter_offer,
            "reasoning": self._explain_counter_offer(initial_offer, counter_offer),
            "conditions": self._get_acceptance_conditions()
        })

    def _evaluate_negotiation_participation(self,
                                          from_agent: str,
                                          negotiation_type: NegotiationType,
                                          offer: Dict,
                                          request_details: Dict) -> bool:
        """Evaluate whether to participate in a negotiation"""

        # Check trust level
        trust_level = self.capabilities.trust_scores.get(from_agent, 0.5)
        if trust_level < 0.3:
            return False

        # Check resource availability
        required_resources = self._extract_resource_requirements(request_details)
        available_resources = self._calculate_available_resources()

        for resource, amount in required_resources.items():
            if available_resources.get(resource, 0) < amount * 0.5:  # Need at least 50% of required
                return False

        # Check workload
        if self.capabilities.current_workload > 0.8:
            return False

        # Check expertise match
        required_expertise = request_details.get("required_expertise", [])
        if required_expertise:
            expertise_match = len(set(required_expertise) & set(self.capabilities.expertise_areas))
            if expertise_match == 0:
                return False

        # Consider potential benefits
        potential_benefit = self._calculate_potential_benefit(offer, request_details)
        if potential_benefit < 0.3:
            return False

        return True

    def _formulate_counter_offer(self,
                               from_agent: str,
                               initial_offer: Dict,
                               request_details: Dict) -> NegotiationOffer:
        """Formulate a counter-offer based on initial offer"""

        # Analyze the initial offer
        offered_resources = initial_offer.get("resources_offered", {})
        requested_resources = initial_offer.get("resources_requested", {})

        # Calculate our position
        our_available = self._calculate_available_resources()
        our_needs = self._assess_our_needs(request_details)

        # Apply negotiation strategy
        strategy = self._determine_negotiation_strategy(from_agent, initial_offer)

        if strategy == "cooperative":
            # Be generous, seek win-win
            resources_offered = {k: v * 0.8 for k, v in our_available.items()}
            resources_requested = {k: v * 0.7 for k, v in our_needs.items()}
        elif strategy == "competitive":
            # Minimize giving, maximize getting
            resources_offered = {k: v * 0.4 for k, v in our_available.items()}
            resources_requested = {k: v * 1.2 for k, v in our_needs.items()}
        else:  # adaptive
            # Balance based on relationship
            trust_factor = self.capabilities.trust_scores.get(from_agent, 0.5)
            offer_factor = 0.4 + (trust_factor * 0.4)
            request_factor = 1.0 - (trust_factor * 0.3)

            resources_offered = {k: v * offer_factor for k, v in our_available.items()}
            resources_requested = {k: v * request_factor for k, v in our_needs.items()}

        return NegotiationOffer(
            offer_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=from_agent,
            negotiation_type=NegotiationType(initial_offer.get("negotiation_type", "task_assignment")),
            proposal=self._create_counter_proposal(initial_offer, resources_offered, resources_requested),
            resources_requested=resources_requested,
            resources_offered=resources_offered,
            constraints=self._generate_constraints(),
            priority=initial_offer.get("priority", 0.5),
            confidence=self._calculate_offer_confidence(resources_offered, resources_requested),
            deadline=datetime.utcnow() + timedelta(minutes=3)
        )

    async def _handle_offer(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming offer"""
        return await self._handle_counter_offer(message)  # Same logic

    async def _handle_counter_offer(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming counter-offer"""

        negotiation_id = message["negotiation_id"]
        from_agent = message.get("from_agent", message["counter_offer"]["from_agent"])
        counter_offer = message["counter_offer"]

        if negotiation_id not in self.active_negotiations:
            return {"error": "Unknown negotiation"}

        negotiation = self.active_negotiations[negotiation_id]

        # Update negotiation state
        negotiation["current_round"] += 1
        negotiation["peer_offer"] = counter_offer
        negotiation["history"].append(counter_offer)

        # Evaluate the counter-offer
        acceptance_score = self._evaluate_offer(counter_offer, negotiation)

        if acceptance_score > 0.8:
            # Accept the offer
            negotiation["status"] = NegotiationStatus.ACCEPTED
            agreement = self._create_agreement(counter_offer, negotiation)

            await self._send_message(from_agent, "acceptance", {
                "negotiation_id": negotiation_id,
                "agreement": agreement,
                "satisfaction_score": acceptance_score
            })

            # Execute the agreement
            await self._execute_agreement(agreement)

            return {"status": "accepted", "agreement": agreement}

        elif negotiation["current_round"] >= negotiation.get("max_rounds", 10):
            # Max rounds reached, reject
            negotiation["status"] = NegotiationStatus.REJECTED

            await self._send_message(from_agent, "rejection", {
                "negotiation_id": negotiation_id,
                "reason": "max_rounds_exceeded",
                "best_offer_score": acceptance_score
            })

            return {"status": "rejected", "reason": "max_rounds"}

        else:
            # Make another counter-offer
            new_counter_offer = self._refine_offer(counter_offer, negotiation, acceptance_score)

            await self._send_message(from_agent, "counter_offer", {
                "negotiation_id": negotiation_id,
                "counter_offer": new_counter_offer,
                "reasoning": self._explain_counter_offer(counter_offer, new_counter_offer),
                "round": negotiation["current_round"]
            })

            return {"status": "counter_offered", "offer": new_counter_offer}

    def _evaluate_offer(self, offer: Dict, negotiation: Dict) -> float:
        """Evaluate an offer and return acceptance score (0-1)"""

        score = 0.0

        # Evaluate resource exchange
        resources_offered = offer.get("resources_offered", {})
        resources_requested = offer.get("resources_requested", {})

        our_available = self._calculate_available_resources()
        our_needs = self._assess_our_needs(negotiation.get("initial_request", {}))

        # Score based on how well our needs are met
        needs_satisfaction = 0.0
        if our_needs:
            for resource, needed in our_needs.items():
                offered_amount = resources_offered.get(resource, 0)
                satisfaction = min(1.0, offered_amount / needed) if needed > 0 else 1.0
                needs_satisfaction += satisfaction
            needs_satisfaction /= len(our_needs)

        # Score based on how reasonable their requests are
        request_reasonableness = 1.0
        if resources_requested:
            for resource, requested in resources_requested.items():
                available = our_available.get(resource, 0)
                if requested > available:
                    request_reasonableness *= (available / requested)

        # Consider relationship factors
        from_agent = offer.get("from_agent", "")
        trust_bonus = self.capabilities.trust_scores.get(from_agent, 0.5) * 0.1
        history_bonus = self.capabilities.collaboration_history.get(from_agent, 0.5) * 0.1

        # Combine scores
        score = (needs_satisfaction * 0.4 +
                request_reasonableness * 0.4 +
                trust_bonus +
                history_bonus)

        # Apply confidence factor
        confidence = offer.get("confidence", 0.5)
        score *= (0.5 + confidence * 0.5)

        return min(1.0, score)

    def _refine_offer(self, peer_offer: Dict, negotiation: Dict, current_score: float) -> NegotiationOffer:
        """Refine our offer based on peer's offer and negotiation progress"""

        # Make incremental improvements to increase acceptance
        improvement_factor = (1.0 - current_score) * 0.3  # Improve by 30% of the gap

        current_offer = negotiation.get("our_last_offer", {})
        resources_offered = current_offer.get("resources_offered", {})
        resources_requested = current_offer.get("resources_requested", {})

        # Increase what we offer
        for resource, amount in resources_offered.items():
            resources_offered[resource] = amount * (1 + improvement_factor)

        # Decrease what we request
        for resource, amount in resources_requested.items():
            resources_requested[resource] = amount * (1 - improvement_factor * 0.5)

        # Ensure we don't exceed our limits
        our_available = self._calculate_available_resources()
        for resource, amount in resources_offered.items():
            resources_offered[resource] = min(amount, our_available.get(resource, 0) * 0.9)

        refined_offer = NegotiationOffer(
            offer_id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=peer_offer.get("from_agent", ""),
            negotiation_type=NegotiationType(peer_offer.get("negotiation_type", "task_assignment")),
            proposal=self._create_refined_proposal(peer_offer, resources_offered, resources_requested),
            resources_requested=resources_requested,
            resources_offered=resources_offered,
            constraints=self._generate_constraints(),
            priority=peer_offer.get("priority", 0.5),
            confidence=min(1.0, current_score + improvement_factor),
            deadline=datetime.utcnow() + timedelta(minutes=2)
        )

        negotiation["our_last_offer"] = refined_offer.__dict__
        return refined_offer

    async def _execute_agreement(self, agreement: Dict):
        """Execute a negotiated agreement"""

        # Update our resource allocation
        resources_committed = agreement.get("resources_committed", {})
        for resource, amount in resources_committed.items():
            if resource in self.capabilities.available_resources:
                self.capabilities.available_resources[resource] -= amount

        # Update workload
        workload_increase = agreement.get("workload_increase", 0.0)
        self.capabilities.current_workload = min(1.0,
            self.capabilities.current_workload + workload_increase)

        # Record successful collaboration
        peer_agent = agreement.get("peer_agent", "")
        if peer_agent:
            self._update_collaboration_history(peer_agent, True)
            self._update_trust_score(peer_agent, 0.05)  # Small trust increase

    # Helper methods
    def _calculate_available_resources(self) -> Dict[str, float]:
        """Calculate currently available resources"""
        return {k: v * (1.0 - self.capabilities.current_workload)
                for k, v in self.capabilities.available_resources.items()}

    def _extract_resource_requirements(self, request: Dict) -> Dict[str, float]:
        """Extract resource requirements from request"""
        return request.get("resources_needed", {})

    def _generate_constraints(self) -> List[str]:
        """Generate current constraints for offers"""
        constraints = []
        if self.capabilities.current_workload > 0.7:
            constraints.append("high_workload_priority_only")
        if len(self.active_negotiations) > 3:
            constraints.append("limited_concurrent_negotiations")
        return constraints

    def _calculate_offer_confidence(self, offered: Dict, requested: Dict) -> float:
        """Calculate confidence in an offer"""
        # Simplified confidence calculation
        return 0.7 + np.random.random() * 0.3

    def _create_proposal(self, request: Dict, offered: Dict, requested: Dict) -> Dict:
        """Create proposal details"""
        return {
            "task_assignment": request.get("task", ""),
            "resource_exchange": {"offered": offered, "requested": requested},
            "timeline": request.get("timeline", "immediate"),
            "success_criteria": request.get("success_criteria", [])
        }

    def _suggest_alternatives(self, request: Dict) -> List[str]:
        """Suggest alternative approaches"""
        return ["partial_collaboration", "delayed_execution", "resource_sharing"]

    def _explain_counter_offer(self, original: Dict, counter: Dict) -> str:
        """Explain reasoning behind counter-offer"""
        return "Adjusted based on current resource availability and workload constraints"

    def _get_acceptance_conditions(self) -> List[str]:
        """Get conditions for accepting offers"""
        return ["resource_availability_maintained", "workload_manageable"]

    # Placeholder methods (would be implemented based on specific agent needs)
    def _assess_our_needs(self, request: Dict) -> Dict[str, float]:
        return {}

    def _determine_negotiation_strategy(self, from_agent: str, offer: Dict) -> str:
        return "adaptive"

    def _calculate_potential_benefit(self, offer: Dict, request: Dict) -> float:
        return 0.6

    def _create_counter_proposal(self, initial: Dict, offered: Dict, requested: Dict) -> Dict:
        return self._create_proposal({}, offered, requested)

    def _create_agreement(self, offer: Dict, negotiation: Dict) -> Dict:
        return {"agreement_id": str(uuid.uuid4()), "terms": offer}

    def _create_refined_proposal(self, peer_offer: Dict, offered: Dict, requested: Dict) -> Dict:
        return self._create_proposal({}, offered, requested)

    def _update_collaboration_history(self, agent_id: str, success: bool):
        """Update collaboration history with another agent"""
        current_rate = self.capabilities.collaboration_history.get(agent_id, 0.5)
        new_rate = current_rate * 0.9 + (1.0 if success else 0.0) * 0.1
        self.capabilities.collaboration_history[agent_id] = new_rate

    def _update_trust_score(self, agent_id: str, change: float):
        """Update trust score for another agent"""
        current_trust = self.capabilities.trust_scores.get(agent_id, 0.5)
        new_trust = max(0.0, min(1.0, current_trust + change))
        self.capabilities.trust_scores[agent_id] = new_trust

    async def _send_message(self, target_agent: str, message_type: str, content: Dict) -> Dict:
        """Send message to another agent (would be implemented with actual communication)"""
        # This would integrate with the actual inter-agent communication system
        pass

    async def _handle_acceptance(self, message: Dict) -> Dict:
        """Handle acceptance of our offer"""
        negotiation_id = message["negotiation_id"]
        if negotiation_id in self.active_negotiations:
            negotiation = self.active_negotiations[negotiation_id]
            negotiation["status"] = NegotiationStatus.COMPLETED
            await self._execute_agreement(message["agreement"])
        return {"status": "acknowledged"}

    async def _handle_rejection(self, message: Dict) -> Dict:
        """Handle rejection of our offer"""
        negotiation_id = message["negotiation_id"]
        if negotiation_id in self.active_negotiations:
            negotiation = self.active_negotiations[negotiation_id]
            negotiation["status"] = NegotiationStatus.REJECTED
            # Learn from rejection
            self._learn_from_rejection(message, negotiation)
        return {"status": "acknowledged"}

    async def _handle_resource_query(self, message: Dict) -> Dict:
        """Handle query about available resources"""
        return {
            "available_resources": self._calculate_available_resources(),
            "current_workload": self.capabilities.current_workload,
            "expertise_areas": self.capabilities.expertise_areas
        }

    async def _handle_collaboration_invite(self, message: Dict) -> Dict:
        """Handle invitation to collaborate"""
        # Evaluate collaboration opportunity
        benefit_score = self._calculate_potential_benefit(message, message.get("details", {}))

        if benefit_score > self.cooperation_threshold:
            return {"response": "accept", "conditions": self._get_acceptance_conditions()}
        else:
            return {"response": "decline", "reason": "insufficient_benefit"}

    def _learn_from_rejection(self, rejection_message: Dict, negotiation: Dict):
        """Learn from negotiation rejection to improve future offers"""
        reason = rejection_message.get("reason", "unknown")
        # Update negotiation style based on rejection patterns
        # This would implement learning logic for better future negotiations
        pass