"""
Dynamic Workflow Engine for Agentic AI System
Enables agents to modify their workflows based on performance and learned patterns
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
from collections import defaultdict, deque

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class WorkflowNodeType(Enum):
    """Types of workflow nodes"""
    PROCESSING = "processing"
    DECISION = "decision"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    VALIDATION = "validation"

@dataclass
class WorkflowMetrics:
    """Performance metrics for workflow components"""
    node_id: str
    execution_count: int = 0
    total_execution_time_ms: float = 0.0
    success_rate: float = 1.0
    confidence_scores: List[float] = field(default_factory=list)
    error_count: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)

@dataclass
class WorkflowNode:
    """Dynamic workflow node with adaptive capabilities"""
    node_id: str
    name: str
    node_type: WorkflowNodeType
    function: Callable
    required_confidence: float = 0.7
    timeout_ms: int = 5000
    retry_count: int = 2
    priority: int = 1
    enabled: bool = True
    learned_patterns: List[Dict] = field(default_factory=list)
    performance_threshold: float = 0.8

@dataclass
class WorkflowEdge:
    """Dynamic workflow edge with adaptive routing"""
    from_node: str
    to_node: str
    condition: Optional[Callable] = None
    weight: float = 1.0
    success_rate: float = 1.0
    usage_count: int = 0
    adaptive_threshold: float = 0.6

@dataclass
class WorkflowPattern:
    """Learned workflow patterns"""
    pattern_id: str
    trigger_conditions: Dict[str, Any]
    node_sequence: List[str]
    success_rate: float
    performance_gain: float
    usage_count: int
    created_at: datetime
    confidence: float = 0.8

class DynamicWorkflowEngine:
    """
    Engine for creating and adapting workflows based on performance
    Enables true agentic behavior through workflow evolution
    """

    def __init__(self, agent_id: str, base_confidence_threshold: float = 0.7):
        self.agent_id = agent_id
        self.base_confidence_threshold = base_confidence_threshold

        # Workflow components
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: List[WorkflowEdge] = []
        self.patterns: Dict[str, WorkflowPattern] = {}

        # Performance tracking
        self.node_metrics: Dict[str, WorkflowMetrics] = {}
        self.workflow_history: deque = deque(maxlen=1000)
        self.adaptation_history: List[Dict] = []

        # Learning parameters
        self.learning_rate = 0.1
        self.exploration_rate = 0.15
        self.pattern_detection_window = 50

        # Current workflow state
        self.current_workflow: Optional[StateGraph] = None
        self.workflow_version = 1

    def add_node(self,
                 node_id: str,
                 name: str,
                 node_type: WorkflowNodeType,
                 function: Callable,
                 **kwargs) -> WorkflowNode:
        """Add a node to the workflow with adaptive parameters"""

        node = WorkflowNode(
            node_id=node_id,
            name=name,
            node_type=node_type,
            function=function,
            **kwargs
        )

        self.nodes[node_id] = node
        self.node_metrics[node_id] = WorkflowMetrics(node_id=node_id)

        return node

    def add_edge(self,
                 from_node: str,
                 to_node: str,
                 condition: Optional[Callable] = None,
                 **kwargs) -> WorkflowEdge:
        """Add an edge with adaptive routing capabilities"""

        edge = WorkflowEdge(
            from_node=from_node,
            to_node=to_node,
            condition=condition,
            **kwargs
        )

        self.edges.append(edge)
        return edge

    def build_workflow(self, entry_point: str) -> StateGraph:
        """Build the current workflow graph with adaptive routing"""

        workflow = StateGraph(dict)  # Use dict as state type for flexibility

        # Add all enabled nodes
        for node in self.nodes.values():
            if node.enabled:
                wrapped_function = self._wrap_node_function(node)
                workflow.add_node(node.node_id, wrapped_function)

        # Set entry point
        workflow.set_entry_point(entry_point)

        # Add edges with adaptive conditions
        for edge in self.edges:
            if self._should_include_edge(edge):
                if edge.condition:
                    # Create adaptive conditional edge
                    adaptive_condition = self._create_adaptive_condition(edge)
                    workflow.add_conditional_edges(
                        edge.from_node,
                        adaptive_condition,
                        self._get_conditional_mapping(edge)
                    )
                else:
                    workflow.add_edge(edge.from_node, edge.to_node)

        # Add END edges for terminal nodes
        self._add_end_edges(workflow)

        self.current_workflow = workflow
        return workflow

    def _wrap_node_function(self, node: WorkflowNode) -> Callable:
        """Wrap node function with performance tracking and adaptation"""

        async def wrapped_function(state: Dict[str, Any]) -> Dict[str, Any]:
            start_time = time.time()
            node_id = node.node_id

            try:
                # Check if node should be executed based on adaptive criteria
                if not self._should_execute_node(node, state):
                    return state

                # Execute the original function
                if asyncio.iscoroutinefunction(node.function):
                    result = await node.function(state)
                else:
                    result = node.function(state)

                # Track successful execution
                execution_time = (time.time() - start_time) * 1000
                self._record_node_success(node_id, execution_time, state, result)

                # Check for pattern learning opportunities
                self._learn_from_execution(node_id, state, result, True)

                return result

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self._record_node_failure(node_id, execution_time, str(e))

                # Learn from failure
                self._learn_from_execution(node_id, state, {"error": str(e)}, False)

                # Decide whether to retry or skip
                if self._should_retry_node(node, state):
                    return await wrapped_function(state)  # Retry
                else:
                    # Graceful degradation
                    return self._get_fallback_result(node, state, str(e))

        return wrapped_function

    def _should_execute_node(self, node: WorkflowNode, state: Dict[str, Any]) -> bool:
        """Determine if a node should be executed based on adaptive criteria"""

        metrics = self.node_metrics[node.node_id]

        # Always execute if no history
        if metrics.execution_count == 0:
            return True

        # Check success rate threshold
        if metrics.success_rate < node.performance_threshold:
            # Consider skipping low-performing nodes
            if np.random.random() > node.performance_threshold:
                return False

        # Check confidence requirements
        current_confidence = state.get("confidence_score", 1.0)
        if current_confidence < node.required_confidence:
            return False

        # Check learned patterns
        for pattern in node.learned_patterns:
            if self._pattern_matches(pattern, state):
                # Execute based on pattern confidence
                return pattern.get("should_execute", True)

        return True

    def _create_adaptive_condition(self, edge: WorkflowEdge) -> Callable:
        """Create an adaptive condition function for routing"""

        def adaptive_condition(state: Dict[str, Any]) -> str:
            # Use original condition if available
            if edge.condition:
                original_result = edge.condition(state)

                # Apply adaptive learning
                success_rate = edge.success_rate

                # Explore alternative paths occasionally
                if np.random.random() < self.exploration_rate:
                    alternative = self._get_alternative_path(edge.from_node, state)
                    if alternative and alternative != edge.to_node:
                        return alternative

                # Use learned patterns to modify routing
                learned_route = self._get_learned_route(edge.from_node, state)
                if learned_route and learned_route != original_result:
                    # Use learned route if confidence is high enough
                    pattern = self._get_routing_pattern(edge.from_node, learned_route)
                    if pattern and pattern.confidence > 0.8:
                        return learned_route

                return original_result

            # Default routing based on performance
            return edge.to_node

        return adaptive_condition

    def _record_node_success(self,
                           node_id: str,
                           execution_time: float,
                           input_state: Dict,
                           output_state: Dict):
        """Record successful node execution"""

        metrics = self.node_metrics[node_id]
        metrics.execution_count += 1
        metrics.total_execution_time_ms += execution_time

        # Update success rate
        total_attempts = metrics.execution_count + metrics.error_count
        metrics.success_rate = metrics.execution_count / total_attempts

        # Track confidence if available
        confidence = output_state.get("confidence_score", 0.8)
        metrics.confidence_scores.append(confidence)
        if len(metrics.confidence_scores) > 100:
            metrics.confidence_scores.pop(0)

        metrics.last_updated = datetime.utcnow()

        # Record in workflow history
        self.workflow_history.append({
            "timestamp": datetime.utcnow(),
            "node_id": node_id,
            "execution_time_ms": execution_time,
            "success": True,
            "confidence": confidence,
            "input_features": self._extract_features(input_state),
            "output_features": self._extract_features(output_state)
        })

    def _record_node_failure(self, node_id: str, execution_time: float, error: str):
        """Record failed node execution"""

        metrics = self.node_metrics[node_id]
        metrics.error_count += 1

        # Update success rate
        total_attempts = metrics.execution_count + metrics.error_count
        if total_attempts > 0:
            metrics.success_rate = metrics.execution_count / total_attempts

        metrics.last_updated = datetime.utcnow()

        # Record in workflow history
        self.workflow_history.append({
            "timestamp": datetime.utcnow(),
            "node_id": node_id,
            "execution_time_ms": execution_time,
            "success": False,
            "error": error
        })

    def _learn_from_execution(self,
                            node_id: str,
                            input_state: Dict,
                            output_state: Dict,
                            success: bool):
        """Learn patterns from node execution"""

        # Extract features for pattern learning
        input_features = self._extract_features(input_state)

        # Create experience record
        experience = {
            "node_id": node_id,
            "input_features": input_features,
            "success": success,
            "timestamp": datetime.utcnow(),
            "confidence": output_state.get("confidence_score", 0.5)
        }

        # Update node's learned patterns
        self._update_learned_patterns(node_id, experience)

        # Check for workflow-level patterns
        if len(self.workflow_history) >= self.pattern_detection_window:
            self._detect_workflow_patterns()

    def _extract_features(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features from state for pattern learning"""

        features = {}

        # Extract numerical features
        for key, value in state.items():
            if isinstance(value, (int, float)):
                features[key] = value
            elif isinstance(value, str):
                features[f"{key}_length"] = len(value)
            elif isinstance(value, dict):
                # Extract nested features
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, (int, float)):
                        features[f"{key}_{nested_key}"] = nested_value

        return features

    def _update_learned_patterns(self, node_id: str, experience: Dict):
        """Update learned patterns for a specific node"""

        node = self.nodes[node_id]

        # Simple pattern learning: group by input features
        feature_signature = json.dumps(experience["input_features"], sort_keys=True)

        # Find or create pattern
        existing_pattern = None
        for pattern in node.learned_patterns:
            if pattern.get("feature_signature") == feature_signature:
                existing_pattern = pattern
                break

        if existing_pattern:
            # Update existing pattern
            existing_pattern["count"] += 1
            existing_pattern["success_rate"] = (
                existing_pattern["success_rate"] * (existing_pattern["count"] - 1) +
                (1.0 if experience["success"] else 0.0)
            ) / existing_pattern["count"]
            existing_pattern["last_seen"] = experience["timestamp"]
        else:
            # Create new pattern
            new_pattern = {
                "feature_signature": feature_signature,
                "input_features": experience["input_features"],
                "success_rate": 1.0 if experience["success"] else 0.0,
                "count": 1,
                "first_seen": experience["timestamp"],
                "last_seen": experience["timestamp"],
                "should_execute": experience["success"]
            }
            node.learned_patterns.append(new_pattern)

        # Limit pattern storage
        if len(node.learned_patterns) > 50:
            # Remove oldest patterns
            node.learned_patterns.sort(key=lambda p: p["last_seen"])
            node.learned_patterns = node.learned_patterns[-50:]

    def _detect_workflow_patterns(self):
        """Detect high-level workflow patterns for optimization"""

        recent_history = list(self.workflow_history)[-self.pattern_detection_window:]

        # Group by successful execution sequences
        successful_sequences = []
        current_sequence = []

        for entry in recent_history:
            if entry["success"]:
                current_sequence.append(entry["node_id"])
            else:
                if len(current_sequence) >= 2:
                    successful_sequences.append(current_sequence.copy())
                current_sequence = []

        # Add final sequence
        if len(current_sequence) >= 2:
            successful_sequences.append(current_sequence)

        # Find common patterns
        pattern_counts = defaultdict(int)
        for sequence in successful_sequences:
            for i in range(len(sequence) - 1):
                pattern = tuple(sequence[i:i+2])
                pattern_counts[pattern] += 1

        # Create or update workflow patterns
        for pattern_tuple, count in pattern_counts.items():
            if count >= 3:  # Minimum threshold for pattern recognition
                pattern_id = f"workflow_pattern_{hash(pattern_tuple)}"

                if pattern_id in self.patterns:
                    # Update existing pattern
                    self.patterns[pattern_id].usage_count += count
                    self.patterns[pattern_id].confidence = min(1.0,
                        self.patterns[pattern_id].confidence + self.learning_rate)
                else:
                    # Create new pattern
                    self.patterns[pattern_id] = WorkflowPattern(
                        pattern_id=pattern_id,
                        trigger_conditions={},
                        node_sequence=list(pattern_tuple),
                        success_rate=1.0,  # Will be refined over time
                        performance_gain=0.1,  # Initial estimate
                        usage_count=count,
                        created_at=datetime.utcnow(),
                        confidence=0.6
                    )

    def adapt_workflow(self) -> bool:
        """Adapt the workflow based on learned patterns and performance"""

        adaptations_made = False

        # 1. Disable underperforming nodes
        for node_id, metrics in self.node_metrics.items():
            if metrics.execution_count >= 10:  # Minimum threshold
                if metrics.success_rate < 0.3:  # Poor performance
                    if self.nodes[node_id].enabled:
                        self.nodes[node_id].enabled = False
                        adaptations_made = True
                        self._log_adaptation("disabled_node", node_id,
                                           f"Success rate: {metrics.success_rate}")

        # 2. Adjust confidence thresholds
        for node_id, node in self.nodes.items():
            metrics = self.node_metrics[node_id]
            if len(metrics.confidence_scores) >= 10:
                avg_confidence = np.mean(metrics.confidence_scores)
                if avg_confidence > 0.9 and node.required_confidence < 0.9:
                    # Increase threshold for high-performing nodes
                    node.required_confidence = min(0.9, node.required_confidence + 0.1)
                    adaptations_made = True
                    self._log_adaptation("increased_threshold", node_id,
                                       f"New threshold: {node.required_confidence}")

        # 3. Add shortcut paths for successful patterns
        for pattern in self.patterns.values():
            if pattern.confidence > 0.8 and pattern.usage_count > 5:
                # Check if shortcut already exists
                shortcut_exists = any(
                    edge.from_node == pattern.node_sequence[0] and
                    edge.to_node == pattern.node_sequence[-1]
                    for edge in self.edges
                )

                if not shortcut_exists and len(pattern.node_sequence) > 2:
                    # Add shortcut edge
                    shortcut_edge = WorkflowEdge(
                        from_node=pattern.node_sequence[0],
                        to_node=pattern.node_sequence[-1],
                        condition=lambda state: self._pattern_matches_state(pattern, state),
                        weight=pattern.confidence
                    )
                    self.edges.append(shortcut_edge)
                    adaptations_made = True
                    self._log_adaptation("added_shortcut", pattern.pattern_id,
                                       f"From {pattern.node_sequence[0]} to {pattern.node_sequence[-1]}")

        if adaptations_made:
            self.workflow_version += 1

        return adaptations_made

    def _log_adaptation(self, adaptation_type: str, target: str, details: str):
        """Log workflow adaptations for observability"""

        adaptation = {
            "timestamp": datetime.utcnow(),
            "adaptation_type": adaptation_type,
            "target": target,
            "details": details,
            "workflow_version": self.workflow_version
        }

        self.adaptation_history.append(adaptation)

        # Keep only recent adaptations
        if len(self.adaptation_history) > 100:
            self.adaptation_history = self.adaptation_history[-100:]

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get comprehensive workflow performance statistics"""

        stats = {
            "workflow_version": self.workflow_version,
            "total_nodes": len(self.nodes),
            "enabled_nodes": len([n for n in self.nodes.values() if n.enabled]),
            "total_edges": len(self.edges),
            "learned_patterns": len(self.patterns),
            "total_executions": sum(m.execution_count for m in self.node_metrics.values()),
            "adaptations_made": len(self.adaptation_history),
            "node_performance": {}
        }

        for node_id, metrics in self.node_metrics.items():
            if metrics.execution_count > 0:
                stats["node_performance"][node_id] = {
                    "success_rate": metrics.success_rate,
                    "avg_execution_time": metrics.total_execution_time_ms / metrics.execution_count,
                    "execution_count": metrics.execution_count,
                    "avg_confidence": np.mean(metrics.confidence_scores) if metrics.confidence_scores else 0.0
                }

        return stats

    # Helper methods (implementations would be added based on specific needs)
    def _should_include_edge(self, edge: WorkflowEdge) -> bool:
        """Determine if edge should be included in current workflow"""
        return edge.success_rate > 0.3

    def _get_conditional_mapping(self, edge: WorkflowEdge) -> Dict[str, str]:
        """Get conditional mapping for edge routing"""
        return {True: edge.to_node, False: "END"}

    def _add_end_edges(self, workflow: StateGraph):
        """Add END edges for terminal nodes"""
        # Implementation would identify terminal nodes and add END edges
        pass

    def _should_retry_node(self, node: WorkflowNode, state: Dict) -> bool:
        """Determine if node should be retried on failure"""
        return False  # Simplified for now

    def _get_fallback_result(self, node: WorkflowNode, state: Dict, error: str) -> Dict:
        """Get fallback result for failed node"""
        return {**state, "error": error, "confidence_score": 0.0}

    def _pattern_matches(self, pattern: Dict, state: Dict) -> bool:
        """Check if state matches a learned pattern"""
        return False  # Simplified for now

    def _get_alternative_path(self, from_node: str, state: Dict) -> Optional[str]:
        """Get alternative routing path for exploration"""
        return None  # Simplified for now

    def _get_learned_route(self, from_node: str, state: Dict) -> Optional[str]:
        """Get learned routing based on patterns"""
        return None  # Simplified for now

    def _get_routing_pattern(self, from_node: str, to_node: str) -> Optional[WorkflowPattern]:
        """Get routing pattern between nodes"""
        return None  # Simplified for now

    def _pattern_matches_state(self, pattern: WorkflowPattern, state: Dict) -> bool:
        """Check if current state matches pattern conditions"""
        return True  # Simplified for now