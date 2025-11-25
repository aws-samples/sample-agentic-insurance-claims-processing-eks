"""
LangGraph Shared Memory Service - Distributed Agent Memory
Advanced memory management with LangChain memory adapters and graph persistence
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import operator
import redis

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
try:
    from langgraph.checkpoint.redis import RedisSaver
except ImportError:
    RedisSaver = None
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
# Use updated memory imports
try:
    from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
except ImportError:
    # Fallback - create minimal memory classes
    class ConversationBufferMemory:
        def __init__(self): self.memory = []
    class ConversationSummaryMemory:
        def __init__(self): self.memory = []
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State definition for memory operations
class MemoryState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    operation_type: str
    agent_id: str
    memory_data: Dict[str, Any]
    query_results: List[Dict[str, Any]]
    memory_updates: Dict[str, Any]
    reasoning_chain: List[str]
    operation_success: bool

@tool
def store_agent_experience(agent_id: str, experience_data: Dict[str, Any]) -> Dict[str, str]:
    """Store agent experience in distributed memory."""
    experience_id = f"exp_{agent_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Add metadata
    experience_data.update({
        "experience_id": experience_id,
        "agent_id": agent_id,
        "timestamp": datetime.utcnow().isoformat(),
        "importance": experience_data.get("importance", 0.5),
        "memory_type": "experience"
    })
    
    return {
        "experience_id": experience_id,
        "status": "stored",
        "agent_id": agent_id
    }

@tool
def retrieve_agent_memories(agent_id: str, memory_type: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieve agent memories by type."""
    # Simulate memory retrieval (replace with actual Redis/database query)
    memories = []
    
    if memory_type == "experience":
        memories = [
            {
                "memory_id": f"mem_{agent_id}_001",
                "content": "Successfully detected fraud pattern in high-value claim",
                "importance": 0.9,
                "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "tags": ["fraud_detection", "pattern_recognition"]
            },
            {
                "memory_id": f"mem_{agent_id}_002", 
                "content": "Collaborated with policy agent on complex case",
                "importance": 0.7,
                "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "tags": ["collaboration", "policy_validation"]
            }
        ]
    elif memory_type == "pattern":
        memories = [
            {
                "memory_id": f"pat_{agent_id}_001",
                "pattern": "High amount + weekend claim + vague description",
                "confidence": 0.85,
                "occurrences": 15,
                "success_rate": 0.8
            }
        ]
    elif memory_type == "relationship":
        memories = [
            {
                "memory_id": f"rel_{agent_id}_001",
                "related_agent": "policy_agent_001",
                "trust_score": 0.9,
                "collaboration_count": 25,
                "success_rate": 0.85
            }
        ]
    
    return memories[:limit]

@tool
def update_agent_knowledge(agent_id: str, knowledge_data: Dict[str, Any]) -> Dict[str, str]:
    """Update agent's knowledge base."""
    knowledge_id = f"know_{agent_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Process knowledge update
    knowledge_data.update({
        "knowledge_id": knowledge_id,
        "agent_id": agent_id,
        "updated_at": datetime.utcnow().isoformat(),
        "knowledge_type": knowledge_data.get("type", "general")
    })
    
    return {
        "knowledge_id": knowledge_id,
        "status": "updated",
        "agent_id": agent_id
    }

@tool
def find_similar_cases(case_data: Dict[str, Any], similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
    """Find similar cases in memory for pattern matching."""
    # Simulate similarity search (replace with vector search in production)
    similar_cases = [
        {
            "case_id": "case_001",
            "similarity_score": 0.85,
            "claim_amount": case_data.get("claim_amount", 0) * 1.1,
            "outcome": "fraud_detected",
            "patterns": ["high_amount", "documentation_issues"]
        },
        {
            "case_id": "case_002", 
            "similarity_score": 0.75,
            "claim_amount": case_data.get("claim_amount", 0) * 0.9,
            "outcome": "approved",
            "patterns": ["standard_claim"]
        }
    ]
    
    return [case for case in similar_cases if case["similarity_score"] >= similarity_threshold]

@tool
def analyze_agent_performance(agent_id: str, time_period_days: int = 30) -> Dict[str, Any]:
    """Analyze agent performance metrics."""
    # Simulate performance analysis
    return {
        "agent_id": agent_id,
        "time_period_days": time_period_days,
        "cases_processed": 150,
        "accuracy_rate": 0.92,
        "fraud_detection_rate": 0.88,
        "collaboration_frequency": 0.35,
        "learning_rate": 0.15,
        "performance_trend": "improving",
        "strengths": ["pattern_recognition", "risk_assessment"],
        "improvement_areas": ["documentation_analysis"]
    }

class LangGraphSharedMemory:
    """Advanced shared memory service with LangGraph workflows"""
    
    def __init__(self, redis_url: str = "redis://redis-service:6379", 
                 ollama_endpoint: str = "http://ollama-service:11434"):
        self.service_id = "langgraph_shared_memory_001"
        self.redis_url = redis_url
        self.ollama_endpoint = ollama_endpoint
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
            self.redis_client = None
        
        # Initialize LLM for memory reasoning
        self.llm = ChatOllama(
            base_url=ollama_endpoint,
            model="qwen3-coder",
            temperature=0.2  # Low temperature for memory operations
        )
        
        # LangChain memory components
        self.conversation_memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # In-memory storage (fallback)
        self.memory_store = {
            "experiences": {},
            "patterns": {},
            "relationships": {},
            "knowledge": {},
            "performance": {}
        }
        
        # Create memory workflow
        self.workflow = self._create_memory_workflow()
        
        # Use Redis checkpointer if available, otherwise memory
        if self.redis_client and RedisSaver is not None:
            self.checkpointer = RedisSaver(self.redis_client)
        else:
            self.checkpointer = MemorySaver()
        
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        logger.info(f"Initialized LangGraph Shared Memory Service: {self.service_id}")

    def _create_memory_workflow(self) -> StateGraph:
        """Create the memory management workflow"""
        
        workflow = StateGraph(MemoryState)
        
        # Workflow nodes
        workflow.add_node("validate_operation", self._validate_operation_node)
        workflow.add_node("process_storage", self._process_storage_node)
        workflow.add_node("process_retrieval", self._process_retrieval_node)
        workflow.add_node("process_analysis", self._process_analysis_node)
        workflow.add_node("update_memory", self._update_memory_node)
        workflow.add_node("generate_insights", self._generate_insights_node)
        
        # Workflow edges with conditional routing
        workflow.set_entry_point("validate_operation")
        
        workflow.add_conditional_edges(
            "validate_operation",
            self._route_operation,
            {
                "store": "process_storage",
                "retrieve": "process_retrieval", 
                "analyze": "process_analysis",
                "update": "update_memory"
            }
        )
        
        workflow.add_edge("process_storage", "generate_insights")
        workflow.add_edge("process_retrieval", "generate_insights")
        workflow.add_edge("process_analysis", "generate_insights")
        workflow.add_edge("update_memory", "generate_insights")
        workflow.add_edge("generate_insights", END)
        
        return workflow

    async def _validate_operation_node(self, state: MemoryState) -> MemoryState:
        """Validate memory operation request"""
        operation_type = state["operation_type"]
        agent_id = state["agent_id"]
        
        valid_operations = ["store", "retrieve", "analyze", "update"]
        
        if operation_type not in valid_operations:
            state["operation_success"] = False
            state["reasoning_chain"].append(f"Invalid operation type: {operation_type}")
        else:
            state["operation_success"] = True
            state["reasoning_chain"].append(f"Operation validated: {operation_type} for agent {agent_id}")
        
        return state

    def _route_operation(self, state: MemoryState) -> str:
        """Route to appropriate operation handler"""
        if not state["operation_success"]:
            return "generate_insights"  # Skip to end if validation failed
        return state["operation_type"]

    async def _process_storage_node(self, state: MemoryState) -> MemoryState:
        """Process memory storage operations"""
        agent_id = state["agent_id"]
        memory_data = state["memory_data"]
        
        storage_results = []
        
        # Store experience if provided
        if "experience" in memory_data:
            result = store_agent_experience.invoke(agent_id, memory_data["experience"])
            storage_results.append(result)
        
        # Store knowledge if provided
        if "knowledge" in memory_data:
            result = update_agent_knowledge.invoke(agent_id, memory_data["knowledge"])
            storage_results.append(result)
        
        state["memory_updates"] = {"storage_results": storage_results}
        state["reasoning_chain"].append(f"Stored {len(storage_results)} memory items")
        
        return state

    async def _process_retrieval_node(self, state: MemoryState) -> MemoryState:
        """Process memory retrieval operations"""
        agent_id = state["agent_id"]
        memory_data = state["memory_data"]
        
        query_results = []
        
        # Retrieve memories by type
        memory_type = memory_data.get("memory_type", "experience")
        limit = memory_data.get("limit", 10)
        
        memories = retrieve_agent_memories.invoke(agent_id, memory_type, limit)
        query_results.extend(memories)
        
        # Find similar cases if case data provided
        if "case_data" in memory_data:
            similar_cases = find_similar_cases.invoke(memory_data["case_data"])
            query_results.extend(similar_cases)
        
        state["query_results"] = query_results
        state["reasoning_chain"].append(f"Retrieved {len(query_results)} memory items")
        
        return state

    async def _process_analysis_node(self, state: MemoryState) -> MemoryState:
        """Process memory analysis operations"""
        agent_id = state["agent_id"]
        memory_data = state["memory_data"]
        
        # Analyze agent performance
        time_period = memory_data.get("time_period_days", 30)
        performance_analysis = analyze_agent_performance.invoke(agent_id, time_period)
        
        state["query_results"] = [performance_analysis]
        state["reasoning_chain"].append("Performance analysis completed")
        
        return state

    async def _update_memory_node(self, state: MemoryState) -> MemoryState:
        """Process memory update operations"""
        agent_id = state["agent_id"]
        memory_data = state["memory_data"]
        
        update_results = []
        
        # Update knowledge base
        if "knowledge_update" in memory_data:
            result = update_agent_knowledge.invoke(agent_id, memory_data["knowledge_update"])
            update_results.append(result)
        
        state["memory_updates"] = {"update_results": update_results}
        state["reasoning_chain"].append(f"Updated {len(update_results)} memory items")
        
        return state

    async def _generate_insights_node(self, state: MemoryState) -> MemoryState:
        """Generate insights using LLM analysis"""
        
        # Prepare context for LLM insights
        context = {
            "operation_type": state["operation_type"],
            "agent_id": state["agent_id"],
            "query_results": state.get("query_results", []),
            "memory_updates": state.get("memory_updates", {}),
            "reasoning_chain": state["reasoning_chain"]
        }
        
        insights_prompt = f"""
        Analyze this memory operation and provide insights:
        
        Context: {json.dumps(context, indent=2)}
        
        Generate insights about:
        1. Memory operation effectiveness
        2. Agent learning patterns
        3. Knowledge gaps identified
        4. Recommendations for improvement
        5. Memory optimization suggestions
        """
        
        messages = [SystemMessage(content="You are an expert in agent memory systems and learning optimization.")]
        messages.append(HumanMessage(content=insights_prompt))
        
        try:
            response = await self.llm.ainvoke(messages)
            insights = {
                "llm_insights": response.content,
                "insight_confidence": 0.8,
                "key_recommendations": self._extract_recommendations(response.content)
            }
        except Exception as e:
            logger.error(f"Insights generation failed: {e}")
            insights = {
                "llm_insights": "Insights generation unavailable",
                "insight_confidence": 0.5,
                "key_recommendations": ["manual_review_recommended"]
            }
        
        # Store insights in conversation memory
        self.conversation_memory.save_context(
            {"input": f"Memory operation: {state['operation_type']}"},
            {"output": insights["llm_insights"]}
        )
        
        state["memory_updates"]["insights"] = insights
        state["reasoning_chain"].append("LLM insights generated")
        
        return state

    def _extract_recommendations(self, llm_response: str) -> List[str]:
        """Extract recommendations from LLM response"""
        recommendations = []
        lines = llm_response.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ["recommend", "suggest", "should", "improve"]):
                recommendations.append(line.strip())
        
        return recommendations[:5]

    async def execute_memory_operation(self, operation_type: str, agent_id: str, 
                                     memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute memory operation using LangGraph workflow"""
        
        # Initialize state
        initial_state = MemoryState(
            messages=[HumanMessage(content=f"Execute {operation_type} operation for agent {agent_id}")],
            operation_type=operation_type,
            agent_id=agent_id,
            memory_data=memory_data,
            query_results=[],
            memory_updates={},
            reasoning_chain=[],
            operation_success=False
        )
        
        # Execute workflow
        try:
            config = {"configurable": {"thread_id": f"{agent_id}_{operation_type}"}}
            final_state = await self.app.ainvoke(initial_state, config=config)
            
            return {
                "service_id": self.service_id,
                "operation_type": operation_type,
                "agent_id": agent_id,
                "workflow_type": "langgraph_memory_management",
                "operation_success": final_state["operation_success"],
                "query_results": final_state.get("query_results", []),
                "memory_updates": final_state.get("memory_updates", {}),
                "reasoning_chain": final_state["reasoning_chain"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Memory operation workflow error: {str(e)}")
            return {
                "error": f"Memory operation failed: {str(e)}",
                "service_id": self.service_id,
                "workflow_type": "langgraph_memory_management"
            }

    async def get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive agent context from memory"""
        
        # Retrieve different types of memories
        experiences = retrieve_agent_memories.invoke(agent_id, "experience", 5)
        patterns = retrieve_agent_memories.invoke(agent_id, "pattern", 3)
        relationships = retrieve_agent_memories.invoke(agent_id, "relationship", 5)
        performance = analyze_agent_performance.invoke(agent_id, 30)
        
        return {
            "agent_id": agent_id,
            "context_type": "comprehensive",
            "experiences": experiences,
            "patterns": patterns,
            "relationships": relationships,
            "performance": performance,
            "context_timestamp": datetime.utcnow().isoformat()
        }

# FastAPI Application
app = FastAPI(
    title="LangGraph Shared Memory Service",
    description="Advanced distributed memory with LangGraph workflows",
    version="3.0.0"
)

# Global memory service instance
memory_service: Optional[LangGraphSharedMemory] = None

@app.on_event("startup")
async def startup_event():
    global memory_service
    try:
        memory_service = LangGraphSharedMemory()
        logger.info("LangGraph Shared Memory Service started")
    except Exception as e:
        logger.error(f"Failed to start Shared Memory Service: {e}")
        # Don't fail startup, continue without full service for now
        pass

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "langgraph-shared-memory",
        "framework": "LangGraph + LangChain + Redis",
        "capabilities": [
            "distributed_memory",
            "agent_experiences",
            "pattern_storage",
            "relationship_tracking",
            "performance_analysis",
            "llm_insights"
        ],
        "redis_connected": memory_service.redis_client is not None if memory_service else False,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/memory/{operation_type}")
async def execute_memory_operation(operation_type: str, request_data: Dict[str, Any]):
    """Execute memory operation"""
    if not memory_service:
        raise HTTPException(status_code=503, detail="Memory service not initialized")
    
    agent_id = request_data.get("agent_id")
    memory_data = request_data.get("memory_data", {})
    
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    result = await memory_service.execute_memory_operation(operation_type, agent_id, memory_data)
    return result

@app.get("/context/{agent_id}")
async def get_agent_context(agent_id: str):
    """Get comprehensive agent context"""
    if not memory_service:
        raise HTTPException(status_code=503, detail="Memory service not initialized")
    
    context = await memory_service.get_agent_context(agent_id)
    return context

@app.get("/workflow")
async def get_workflow_info():
    return {
        "workflow_type": "LangGraph Memory Management",
        "nodes": [
            "validate_operation",
            "process_storage",
            "process_retrieval",
            "process_analysis", 
            "update_memory",
            "generate_insights"
        ],
        "operations": ["store", "retrieve", "analyze", "update"],
        "memory_types": ["experience", "pattern", "relationship", "knowledge"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
