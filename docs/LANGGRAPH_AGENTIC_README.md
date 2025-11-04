# LangGraph Agentic Insurance System 🤖

## Truly Autonomous Multi-Agent AI with LangGraph & LangChain

[![LangGraph](https://img.shields.io/badge/LangGraph-v0.2.16-FF6B6B?logo=python)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-v0.2.16-4ECDC4?logo=python)](https://langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Qwen2.5--Coder:32b-45B7D1)](https://ollama.com/)
[![Redis](https://img.shields.io/badge/Redis-Memory-DC382D?logo=redis)](https://redis.io/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-EKS-326CE5?logo=kubernetes)](https://kubernetes.io/)

**Revolutionary autonomous insurance claims processing with graph-based AI workflows, advanced reasoning, and true agent autonomy.**

## 🧠 What Makes This Truly Agentic?

### **Graph-Based Reasoning Workflows**
- **LangGraph State Machines**: Each agent uses sophisticated state graphs for decision-making
- **Conditional Routing**: Dynamic workflow paths based on real-time analysis
- **State Persistence**: Redis-backed checkpointing for complex multi-step processes
- **Tool Execution**: Agents autonomously select and execute tools based on context

### **Advanced LLM-Powered Autonomy**
- **Autonomous Decision Making**: Agents make independent decisions using Qwen2.5-Coder:32B
- **Multi-Step Reasoning**: Complex reasoning chains with intermediate state management
- **Context-Aware Processing**: Agents maintain and utilize conversation history
- **Self-Directed Learning**: Agents update their knowledge based on outcomes

### **True Multi-Agent Collaboration**
- **Dynamic Agent Coordination**: Coordinator intelligently routes work between agents
- **Collaborative Investigation**: Agents share findings and build on each other's work
- **Distributed Memory**: Shared knowledge base with agent-specific experiences
- **Trust-Based Relationships**: Agents develop trust scores with collaborators

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Agentic System                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Coordinator   │    │  Fraud Agent    │    │Policy Agent  │ │
│  │   LangGraph     │◄──►│   LangGraph     │◄──►│  LangGraph   │ │
│  │   Workflows     │    │   Workflows     │    │  Workflows   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                      │       │
│           ▼                       ▼                      ▼       │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ Investigation   │    │ Shared Memory   │    │    Redis     │ │
│  │    Agent        │◄──►│    Service      │◄──►│ Checkpoints  │ │
│  │  LangGraph      │    │   LangGraph     │    │   & Memory   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                      │       │
│           └───────────────────────┼──────────────────────┘       │
│                                   ▼                              │
│                          ┌──────────────┐                        │
│                          │ Ollama LLM   │                        │
│                          │Qwen2.5-Coder │                        │
│                          │     32B      │                        │
│                          └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Key Agentic Features

### **1. LangGraph State Machines**
Each agent operates as a sophisticated state machine:

```python
# Example: Fraud Agent Workflow
workflow = StateGraph(AgentState)
workflow.add_node("analyze_claim", self._analyze_claim_node)
workflow.add_node("pattern_matching", self._pattern_matching_node)
workflow.add_node("deep_investigation", self._deep_investigation_node)
workflow.add_node("reasoning", self._reasoning_node)
workflow.add_node("decision_making", self._decision_making_node)

# Conditional routing based on analysis
workflow.add_conditional_edges(
    "reasoning",
    self._should_investigate_deeper,
    {
        "investigate": "deep_investigation",
        "decide": "decision_making"
    }
)
```

### **2. Autonomous Tool Selection**
Agents autonomously choose and execute tools:

```python
@tool
def analyze_claim_amount(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze claim amount for anomalies and patterns."""
    # Tool implementation
    
@tool
def check_fraud_patterns(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check claim against known fraud patterns."""
    # Tool implementation
```

### **3. Advanced Memory Management**
Distributed memory with LangChain integration:

```python
# Redis-backed checkpointing
self.checkpointer = RedisSaver(self.redis_client)
self.app = self.workflow.compile(checkpointer=self.checkpointer)

# LangChain memory components
self.conversation_memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)
```

### **4. Multi-Agent Coordination**
Intelligent agent orchestration:

```python
# Dynamic agent routing
workflow.add_conditional_edges(
    "evaluate_collaboration",
    self._needs_collaboration,
    {
        "collaborate": "coordinate_investigation",
        "aggregate": "aggregate_results"
    }
)
```

## 📦 Service Architecture

### **LangGraph Coordinator** (`langgraph_agentic_coordinator.py`)
- **Purpose**: Autonomous multi-agent orchestration
- **Framework**: LangGraph state machine with 7 nodes
- **Features**: Dynamic routing, collaboration detection, LLM reasoning
- **Port**: 8000

### **LangGraph Fraud Agent** (`langgraph_fraud_agent.py`)
- **Purpose**: Advanced fraud detection with graph workflows
- **Framework**: LangGraph with 6-node workflow
- **Features**: Pattern matching, deep investigation, tool execution
- **Port**: 8001

### **LangGraph Policy Agent** (`langgraph_policy_agent.py`)
- **Purpose**: Autonomous policy validation
- **Framework**: LangGraph with 6-node workflow
- **Features**: Coverage analysis, compliance checking, risk assessment
- **Port**: 8002

### **LangGraph Investigation Agent** (`langgraph_investigation_agent.py`)
- **Purpose**: Deep autonomous investigation
- **Framework**: LangGraph with 7-node workflow
- **Features**: Evidence collection, cross-referencing, report generation
- **Port**: 8003

### **LangGraph Shared Memory** (`langgraph_shared_memory.py`)
- **Purpose**: Distributed agent memory and learning
- **Framework**: LangGraph with Redis persistence
- **Features**: Experience storage, pattern learning, performance analysis
- **Port**: 8080

## 🛠️ Quick Deployment

### 1. Build and Deploy
```bash
# Build the LangGraph system
cd insurance-claims-processing/scripts
./build-langgraph-system.sh
```

### 2. Test the System
```bash
# Run comprehensive tests
./test-langgraph-agentic.sh
```

### 3. Access the System
```bash
# Port forward to coordinator
kubectl port-forward -n langgraph-insurance svc/langgraph-coordinator 8000:8000

# Access API documentation
open http://localhost:8000/docs
```

## 🧪 Testing Agentic Capabilities

### **Test 1: Simple Claim Processing**
```bash
curl -X POST "http://localhost:8000/coordinate" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-TEST-001",
    "policy_number": "POL-123456789",
    "claim_amount": 5000.00,
    "claim_type": "collision",
    "description": "Minor fender bender"
  }'
```

### **Test 2: High-Risk Fraud Detection**
```bash
curl -X POST "http://localhost:8000/coordinate" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-FRAUD-001",
    "claim_amount": 75000.00,
    "description": "Total loss due to fire",
    "red_flags": ["high_amount", "vague_description"]
  }'
```

### **Test 3: Memory Operations**
```bash
# Store agent experience
curl -X POST "http://localhost:8080/memory/store" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "fraud_agent_001",
    "memory_data": {
      "experience": {
        "claim_id": "CLM-TEST-001",
        "outcome": "approved",
        "fraud_score": 0.2
      }
    }
  }'

# Retrieve agent context
curl "http://localhost:8080/context/fraud_agent_001"
```

## 📊 Workflow Examples

### **Fraud Agent Workflow**
```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│Analyze Claim│───►│Pattern Matching │───►│    Reasoning    │
└─────────────┘    └─────────────────┘    └─────────────────┘
                                                    │
                                          ┌─────────▼─────────┐
                                          │  Need Deep Inv?   │
                                          └─────────┬─────────┘
                                                    │
                                    ┌───────────────┼───────────────┐
                                    ▼               ▼               ▼
                            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                            │Deep Invest. │ │   Decision  │ │  Learning   │
                            └─────────────┘ └─────────────┘ └─────────────┘
```

### **Coordinator Workflow**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Analyze Claim│───►│Route Agents │───►│Execute //   │───►│Evaluate     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                        ┌─────────▼─────────┐
                                                        │Need Collaboration?│
                                                        └─────────┬─────────┘
                                                                  │
                                                  ┌───────────────┼───────────────┐
                                                  ▼               ▼               ▼
                                          ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                                          │Coordinate   │ │Aggregate    │ │Autonomous   │
                                          │Investigation│ │Results      │ │Decision     │
                                          └─────────────┘ └─────────────┘ └─────────────┘
```

## 🔧 Configuration

### **LangGraph Configuration**
```yaml
# ConfigMap: langgraph-config
LANGGRAPH_CHECKPOINT_BACKEND: "redis"
LANGGRAPH_MEMORY_BACKEND: "redis"
LANGCHAIN_TRACING_V2: "true"
LANGCHAIN_PROJECT: "insurance-agentic-system"
```

### **Agent Configuration**
```python
# Each agent configured with:
self.llm = ChatOllama(
    base_url=ollama_endpoint,
    model="qwen2.5-coder:32b",
    temperature=0.7  # Varies by agent type
)

self.workflow = self._create_workflow()
self.checkpointer = RedisSaver(self.redis_client)
self.app = self.workflow.compile(checkpointer=self.checkpointer)
```

## 📈 Performance & Scaling

### **Auto-Scaling Configuration**
```yaml
# HPA for each service
minReplicas: 3
maxReplicas: 15
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
```

### **Resource Requirements**
- **Coordinator**: 512Mi-1Gi RAM, 250m-500m CPU
- **Agents**: 512Mi-1Gi RAM, 250m-500m CPU each
- **Ollama LLM**: 8-16Gi RAM, 2-4 CPU, 1 GPU (G5.xlarge)
- **Redis**: 512Mi-1Gi RAM, 250m-500m CPU

## 🔍 Monitoring & Observability

### **Health Checks**
```bash
# Check all services
kubectl get pods -n langgraph-insurance

# Service-specific health
curl http://localhost:8000/health  # Coordinator
curl http://localhost:8001/health  # Fraud Agent
curl http://localhost:8002/health  # Policy Agent
curl http://localhost:8003/health  # Investigation Agent
curl http://localhost:8080/health  # Shared Memory
```

### **Workflow Monitoring**
```bash
# Get workflow information
curl http://localhost:8000/workflow
curl http://localhost:8001/workflow
curl http://localhost:8002/workflow
curl http://localhost:8003/workflow
curl http://localhost:8080/workflow
```

### **Memory Analysis**
```bash
# Agent performance analysis
curl "http://localhost:8080/memory/analyze" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "fraud_agent_001", "memory_data": {"time_period_days": 30}}'
```

## 🎯 Agentic Capabilities Demonstrated

### ✅ **Autonomous Decision Making**
- Agents make independent decisions using LLM reasoning
- No hardcoded rules - decisions emerge from context and learning
- Dynamic workflow routing based on real-time analysis

### ✅ **Graph-Based Reasoning**
- Complex multi-step reasoning with state persistence
- Conditional workflow paths based on intermediate results
- Tool selection and execution based on context

### ✅ **Multi-Agent Collaboration**
- Agents autonomously decide when to collaborate
- Dynamic coordination based on case complexity
- Shared learning and knowledge transfer

### ✅ **Persistent Memory & Learning**
- Redis-backed state persistence across sessions
- Agent experiences stored and retrieved for learning
- Performance tracking and improvement over time

### ✅ **Advanced Tool Usage**
- Agents select appropriate tools based on context
- Tool execution integrated into reasoning workflows
- Results fed back into decision-making processes

## 🚀 Advanced Features

### **State Persistence**
```python
# Automatic state checkpointing
config = {"configurable": {"thread_id": claim_id}}
final_state = await self.app.ainvoke(initial_state, config=config)
```

### **Tool Integration**
```python
# Tools automatically available to agents
@tool
def analyze_claim_amount(claim_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze claim amount for anomalies."""
    return analysis_result

# Tool execution in workflow
amount_analysis = analyze_claim_amount.invoke(claim_data)
```

### **Memory Management**
```python
# Distributed memory operations
memory_result = await self.execute_memory_operation(
    operation_type="store",
    agent_id="fraud_agent_001", 
    memory_data=experience_data
)
```

## 🎉 Benefits of LangGraph Conversion

### **Before (Basic Agentic)**
- Simple rule-based decisions
- Limited multi-agent coordination
- Basic memory storage
- Linear processing workflows

### **After (LangGraph Agentic)**
- ✅ **Graph-based reasoning workflows**
- ✅ **Advanced LLM-powered autonomy**
- ✅ **Sophisticated state management**
- ✅ **True multi-agent collaboration**
- ✅ **Persistent memory with learning**
- ✅ **Dynamic tool selection**
- ✅ **Conditional workflow routing**
- ✅ **State checkpointing & recovery**

## 🔮 Future Enhancements

- **Human-in-the-Loop Integration**: Seamless human oversight when needed
- **Advanced Vector Memory**: Semantic similarity search for experiences
- **Multi-Modal Processing**: Image and document analysis capabilities
- **Federated Learning**: Cross-deployment knowledge sharing
- **Real-Time Streaming**: Event-driven processing with Kafka integration

---

## 🎯 Ready to Experience True AI Agency?

This LangGraph-powered system represents the cutting edge of autonomous AI agents. Deploy it today and witness:

- **Agents that truly think and reason**
- **Dynamic collaboration between AI entities**
- **Learning and adaptation over time**
- **Complex decision-making without human intervention**
- **Graph-based workflows that mirror human reasoning**

**The future of autonomous AI is here. Deploy it now!** 🚀

```bash
# Get started in 3 commands
cd insurance-claims-processing/scripts
./build-langgraph-system.sh
./test-langgraph-agentic.sh
```
