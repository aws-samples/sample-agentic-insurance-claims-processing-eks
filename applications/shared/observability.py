"""
Comprehensive Observability Library for Agentic AI System
CloudWatch integration with distributed tracing, structured logging, and custom metrics
"""

import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from functools import wraps
import boto3
from botocore.exceptions import ClientError
import threading
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.core.models import subsegment
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Patch AWS services for X-Ray tracing
patch_all()

@dataclass
class AgentMetrics:
    """Agent-specific performance metrics"""
    agent_id: str
    agent_type: str
    processing_time_ms: float
    decision_confidence: float
    memory_usage_mb: float
    workflow_step: str
    correlation_id: str
    timestamp: datetime

@dataclass
class WorkflowEvent:
    """Workflow execution event"""
    workflow_id: str
    step_name: str
    agent_id: str
    input_data_size: int
    output_data_size: int
    execution_time_ms: float
    success: bool
    error_details: Optional[str] = None
    correlation_id: str = ""

@dataclass
class AgentInteraction:
    """Inter-agent communication event"""
    source_agent: str
    target_agent: str
    interaction_type: str  # request, response, notification
    payload_size_bytes: int
    latency_ms: float
    success: bool
    correlation_id: str

class ObservabilityManager:
    """Central observability manager for agentic AI system"""

    def __init__(self,
                 agent_id: str,
                 agent_type: str,
                 aws_region: str = "us-west-2",
                 cluster_name: str = "agentic-eks-cluster"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.aws_region = aws_region
        self.cluster_name = cluster_name

        # Initialize CloudWatch client
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=aws_region)
            self.logs_client = boto3.client('logs', region_name=aws_region)
        except Exception as e:
            print(f"Warning: Could not initialize AWS clients: {e}")
            self.cloudwatch = None
            self.logs_client = None

        # Initialize structured logger
        self.logger = structlog.get_logger().bind(
            agent_id=agent_id,
            agent_type=agent_type,
            cluster=cluster_name
        )

        # Thread-local storage for correlation IDs
        self._local = threading.local()

        # Metrics buffer for batch sending
        self._metrics_buffer: List[AgentMetrics] = []
        self._buffer_lock = threading.Lock()

    def set_correlation_id(self, correlation_id: str = None) -> str:
        """Set correlation ID for current thread context"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        self._local.correlation_id = correlation_id
        return correlation_id

    def get_correlation_id(self) -> str:
        """Get current correlation ID"""
        if not hasattr(self._local, 'correlation_id'):
            self._local.correlation_id = str(uuid.uuid4())
        return self._local.correlation_id

    @contextmanager
    def trace_workflow_step(self, step_name: str, input_data: Dict[str, Any] = None):
        """Context manager for tracing workflow steps with X-Ray"""
        correlation_id = self.get_correlation_id()

        with xray_recorder.in_subsegment(f"{self.agent_type}_{step_name}") as subsegment:
            start_time = time.time()

            # Add metadata to X-Ray trace
            subsegment.put_metadata("agent_id", self.agent_id)
            subsegment.put_metadata("agent_type", self.agent_type)
            subsegment.put_metadata("correlation_id", correlation_id)
            subsegment.put_metadata("step_name", step_name)

            if input_data:
                subsegment.put_metadata("input_size", len(str(input_data)))

            try:
                self.logger.info(
                    "workflow_step_started",
                    workflow_step=step_name,
                    correlation_id=correlation_id,
                    input_data_size=len(str(input_data)) if input_data else 0
                )

                yield correlation_id

                execution_time = (time.time() - start_time) * 1000

                self.logger.info(
                    "workflow_step_completed",
                    workflow_step=step_name,
                    correlation_id=correlation_id,
                    processing_time=execution_time
                )

                subsegment.put_metadata("execution_time_ms", execution_time)
                subsegment.put_metadata("success", True)

            except Exception as e:
                execution_time = (time.time() - start_time) * 1000

                self.logger.error(
                    "workflow_step_failed",
                    workflow_step=step_name,
                    correlation_id=correlation_id,
                    processing_time=execution_time,
                    error=str(e),
                    exc_info=True
                )

                subsegment.put_metadata("execution_time_ms", execution_time)
                subsegment.put_metadata("success", False)
                subsegment.put_metadata("error", str(e))

                raise

    def log_agent_decision(self,
                          decision: str,
                          confidence: float,
                          reasoning: List[str],
                          input_data: Dict[str, Any],
                          processing_time_ms: float):
        """Log agent decision with all context"""
        correlation_id = self.get_correlation_id()

        self.logger.info(
            "agent_decision_made",
            correlation_id=correlation_id,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            processing_time=processing_time_ms,
            input_data_size=len(str(input_data))
        )

        # Send custom metrics to CloudWatch
        self._send_decision_metrics(decision, confidence, processing_time_ms)

    def log_inter_agent_communication(self,
                                    target_agent: str,
                                    interaction_type: str,
                                    payload_size: int,
                                    latency_ms: float,
                                    success: bool):
        """Log communication between agents"""
        correlation_id = self.get_correlation_id()

        self.logger.info(
            "inter_agent_communication",
            correlation_id=correlation_id,
            source_agent=self.agent_id,
            target_agent=target_agent,
            interaction_type=interaction_type,
            payload_size_bytes=payload_size,
            latency_ms=latency_ms,
            success=success
        )

        # Track communication metrics
        self._send_communication_metrics(target_agent, latency_ms, success)

    def log_learning_event(self,
                          learning_type: str,
                          previous_confidence: float,
                          new_confidence: float,
                          outcome: str,
                          lesson_learned: str):
        """Log agent learning events"""
        correlation_id = self.get_correlation_id()

        confidence_improvement = new_confidence - previous_confidence

        self.logger.info(
            "agent_learning_event",
            correlation_id=correlation_id,
            learning_type=learning_type,
            previous_confidence=previous_confidence,
            new_confidence=new_confidence,
            confidence_improvement=confidence_improvement,
            outcome=outcome,
            lesson_learned=lesson_learned
        )

        # Send learning metrics
        self._send_learning_metrics(learning_type, confidence_improvement)

    def log_performance_metrics(self, metrics: Dict[str, float]):
        """Log custom performance metrics"""
        correlation_id = self.get_correlation_id()

        self.logger.info(
            "performance_metrics",
            correlation_id=correlation_id,
            **metrics
        )

        # Send to CloudWatch as custom metrics
        for metric_name, value in metrics.items():
            self._send_custom_metric(metric_name, value)

    def _send_decision_metrics(self, decision: str, confidence: float, processing_time: float):
        """Send agent decision metrics to CloudWatch"""
        if not self.cloudwatch:
            return

        try:
            self.cloudwatch.put_metric_data(
                Namespace='Agentic_AI/Decisions',
                MetricData=[
                    {
                        'MetricName': 'ProcessingTime',
                        'Dimensions': [
                            {'Name': 'AgentType', 'Value': self.agent_type},
                            {'Name': 'AgentId', 'Value': self.agent_id},
                            {'Name': 'Decision', 'Value': decision}
                        ],
                        'Value': processing_time,
                        'Unit': 'Milliseconds'
                    },
                    {
                        'MetricName': 'Confidence',
                        'Dimensions': [
                            {'Name': 'AgentType', 'Value': self.agent_type},
                            {'Name': 'AgentId', 'Value': self.agent_id},
                            {'Name': 'Decision', 'Value': decision}
                        ],
                        'Value': confidence,
                        'Unit': 'None'
                    }
                ]
            )
        except Exception as e:
            self.logger.warning("Failed to send decision metrics", error=str(e))

    def _send_communication_metrics(self, target_agent: str, latency: float, success: bool):
        """Send inter-agent communication metrics"""
        if not self.cloudwatch:
            return

        try:
            self.cloudwatch.put_metric_data(
                Namespace='Agentic_AI/Communication',
                MetricData=[
                    {
                        'MetricName': 'InterAgentLatency',
                        'Dimensions': [
                            {'Name': 'SourceAgent', 'Value': self.agent_id},
                            {'Name': 'TargetAgent', 'Value': target_agent}
                        ],
                        'Value': latency,
                        'Unit': 'Milliseconds'
                    },
                    {
                        'MetricName': 'CommunicationSuccess',
                        'Dimensions': [
                            {'Name': 'SourceAgent', 'Value': self.agent_id},
                            {'Name': 'TargetAgent', 'Value': target_agent}
                        ],
                        'Value': 1.0 if success else 0.0,
                        'Unit': 'None'
                    }
                ]
            )
        except Exception as e:
            self.logger.warning("Failed to send communication metrics", error=str(e))

    def _send_learning_metrics(self, learning_type: str, improvement: float):
        """Send agent learning metrics"""
        if not self.cloudwatch:
            return

        try:
            self.cloudwatch.put_metric_data(
                Namespace='Agentic_AI/Learning',
                MetricData=[
                    {
                        'MetricName': 'ConfidenceImprovement',
                        'Dimensions': [
                            {'Name': 'AgentType', 'Value': self.agent_type},
                            {'Name': 'LearningType', 'Value': learning_type}
                        ],
                        'Value': improvement,
                        'Unit': 'None'
                    }
                ]
            )
        except Exception as e:
            self.logger.warning("Failed to send learning metrics", error=str(e))

    def _send_custom_metric(self, metric_name: str, value: float):
        """Send custom metric to CloudWatch"""
        if not self.cloudwatch:
            return

        try:
            self.cloudwatch.put_metric_data(
                Namespace='Agentic_AI/Custom',
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': [
                            {'Name': 'AgentType', 'Value': self.agent_type},
                            {'Name': 'AgentId', 'Value': self.agent_id}
                        ],
                        'Value': value,
                        'Unit': 'None'
                    }
                ]
            )
        except Exception as e:
            self.logger.warning(f"Failed to send custom metric {metric_name}", error=str(e))

def trace_agent_method(method_name: str = None):
    """Decorator for tracing agent methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get observability manager from self
            obs_manager = getattr(self, 'obs_manager', None)
            if not obs_manager:
                return func(self, *args, **kwargs)

            step_name = method_name or func.__name__

            with obs_manager.trace_workflow_step(step_name):
                start_time = time.time()
                try:
                    result = func(self, *args, **kwargs)
                    processing_time = (time.time() - start_time) * 1000

                    # Log successful execution
                    obs_manager.logger.debug(
                        "method_execution_success",
                        method=step_name,
                        processing_time=processing_time
                    )

                    return result
                except Exception as e:
                    processing_time = (time.time() - start_time) * 1000

                    obs_manager.logger.error(
                        "method_execution_failed",
                        method=step_name,
                        processing_time=processing_time,
                        error=str(e),
                        exc_info=True
                    )
                    raise
        return wrapper
    return decorator

# Global observability instance for easy access
_global_obs_manager: Optional[ObservabilityManager] = None

def init_observability(agent_id: str, agent_type: str, **kwargs) -> ObservabilityManager:
    """Initialize global observability manager"""
    global _global_obs_manager
    _global_obs_manager = ObservabilityManager(agent_id, agent_type, **kwargs)
    return _global_obs_manager

def get_observability() -> Optional[ObservabilityManager]:
    """Get global observability manager"""
    return _global_obs_manager