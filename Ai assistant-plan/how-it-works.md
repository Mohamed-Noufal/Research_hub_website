# How the AI Agent System is Built

A learning guide for understanding custom AI agents vs SDK-based platforms.

---

## Table of Contents
1. [SDK vs Custom: What's the Difference?](#1-sdk-vs-custom)
2. [The ReAct Pattern Explained](#2-the-react-pattern)
3. [Agent Architecture Deep Dive](#3-agent-architecture)
4. [Tool System Explained](#4-tool-system)
5. [Pydantic Validation](#5-pydantic-validation)
6. [Multi-Agent Communication](#6-multi-agent-communication)
7. [RAG Integration with LlamaIndex](#7-rag-integration)

---

## 1. SDK vs Custom

### What SDKs Give You (LangChain, CrewAI, AutoGen):
```python
# LangChain example
from langchain.agents import create_react_agent
agent = create_react_agent(llm, tools, prompt)
result = agent.invoke({"input": "Find papers on ML"})
```

**Pros**: Quick to start, batteries included
**Cons**: Less control, harder to customize, dependency hell

### What We Built (Custom):
```python
# Our implementation
agent = FlexibleAgent(
    name="MainAgent",
    llm_client=llm,      # Your own LLM wrapper
    tools=tools,          # Your own tool definitions
    max_iterations=3      # Full control over behavior
)
result = await agent.run("Find papers on ML")
```

**Pros**: Full control, custom validation, easier debugging
**Cons**: More initial work

---

## 2. The ReAct Pattern

ReAct = **Re**ason + **Act**. The agent thinks, then acts, then observes.

### The Loop (from `base.py`):

```
User Input: "Extract methodology from paper 5"
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  ITERATION 1                                                │
├─────────────────────────────────────────────────────────────┤
│  THINK: "I need to extract methodology. I'll use the       │
│          extract_methodology tool with paper_id=5"          │
│                                                             │
│  ACT:   Call extract_methodology(paper_id=5)               │
│                                                             │
│  OBSERVE: {"methodology_summary": "Survey of 100...",      │
│            "data_collection": "Online questionnaire"}       │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  ITERATION 2                                                │
├─────────────────────────────────────────────────────────────┤
│  THINK: "I got the methodology. Now I should save it       │
│          using update_methodology tool"                     │
│                                                             │
│  ACT:   Call update_methodology(paper_id=5, ...)           │
│                                                             │
│  OBSERVE: {"success": true}                                │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  ITERATION 3                                                │
├─────────────────────────────────────────────────────────────┤
│  THINK: "Task complete. I'll respond to the user."         │
│                                                             │
│  RESPOND: "I extracted and saved the methodology for       │
│           paper 5. Key finding: Survey of 100..."          │
└─────────────────────────────────────────────────────────────┘
```

### The Code (simplified from `base.py`):

```python
class FlexibleAgent:
    async def run(self, input_text: str):
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": input_text}
        ]
        
        for iteration in range(self.max_iterations):
            # Ask LLM what to do
            response = await self.llm.complete(messages)
            
            # Check if LLM wants to call a tool
            if "TOOL:" in response:
                tool_name, args = self._parse_tool_call(response)
                
                # Execute the tool
                result = self._execute_tool(tool_name, args)
                
                # Add result to conversation
                messages.append({"role": "tool", "content": str(result)})
            else:
                # LLM is done, return response
                return response
```

---

## 3. Agent Architecture

### Three Agent Types:

```
┌─────────────────────────────────────────────────────────────┐
│                    OrchestratorAgent                         │
│  (Legacy - still works, 23 tools)                           │
│  Used by: Current production                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      MainAgent                               │
│  (New - Router with 5 tools)                                │
│  Purpose: Quick routing, delegates heavy work               │
└─────────────────────────────────────────────────────────────┘
         │
         │ delegates to
         ▼
┌─────────────────────────────────────────────────────────────┐
│                 LiteratureReviewAgent                        │
│  (New - Specialist with mode-based tools)                   │
│  Modes: methodology, findings, comparison, synthesis,       │
│         summary, full                                        │
└─────────────────────────────────────────────────────────────┘
```

### Why Multiple Agents?

**Problem with 1 agent + 23 tools:**
- LLM prompt is HUGE (all tool descriptions)
- LLM gets confused which tool to use
- Expensive (more tokens = more $$$)
- Tool hallucination

**Solution with multi-agent:**
- MainAgent: 5 tools only → small prompt, fast routing
- LiteratureAgent: loads only relevant tools per mode
- Mode `methodology`: 4 tools instead of 23

---

## 4. Tool System

### How Tools Are Defined:

```python
# In orchestrator.py or any agent file

Tool(
    name="extract_methodology",           # What LLM calls it
    description="Extract methodology...", # Tells LLM when to use it
    parameters={                          # What arguments it needs
        "paper_id": "int"
    },
    function=lambda **kwargs: rag_tools.extract_methodology(
        **kwargs,                         # Pass args from LLM
        rag_engine=self.rag,              # Inject dependencies
        llm_client=self.llm
    )
)
```

### How LLM Sees Tools (System Prompt):

```
You have these tools available:

1. extract_methodology
   Description: Extract methodology details from a paper
   Parameters: {"paper_id": "int"}

2. update_methodology
   Description: Save methodology to database
   Parameters: {"paper_id": "int", "methodology_summary": "str", ...}

To use a tool, respond with:
TOOL: tool_name
ARGS: {"param1": "value1", ...}
```

### How LLM Responds:

```
THINK: The user wants methodology for paper 5. I'll use extract_methodology.

TOOL: extract_methodology
ARGS: {"paper_id": 5}
```

### How We Parse and Execute:

```python
# In base.py

def _parse_tool_call(self, response: str):
    # Find "TOOL: xxx" and "ARGS: {...}"
    tool_name = extract_between(response, "TOOL:", "\n")
    args_json = extract_between(response, "ARGS:", "\n")
    return tool_name.strip(), json.loads(args_json)

def _execute_tool(self, name: str, args: dict):
    tool = self.tools_by_name[name]
    return tool.function(**args)  # Call the actual Python function
```

---

## 5. Pydantic Validation

### The Problem:
LLM returns JSON, but it might be garbage:

```json
// LLM output - BAD
{"methodology_summary": "Hi"}  // Too short!

// LLM output - BAD
{"methodology_summry": "..."}  // Typo in key!

// LLM output - BAD
{"methodology_summary": "TODO: fill later"}  // Placeholder!
```

### The Solution (Pydantic):

```python
# In schemas/agent_outputs.py

class MethodologyOutput(BaseModel):
    methodology_summary: str = Field(
        ...,              # Required
        min_length=10     # At least 10 chars
    )
    data_collection: Optional[str] = None
    
    @field_validator('methodology_summary')
    @classmethod
    def not_placeholder(cls, v):
        if v.lower().startswith('todo'):
            raise ValueError('Cannot be placeholder')
        return v
```

### Using Validation in Tools:

```python
# In rag_tools.py

async def extract_methodology(paper_id: int, ...):
    # Get LLM response
    response = await llm.complete(prompt)
    
    # Try to validate
    for attempt in range(3):  # Retry up to 3 times
        try:
            result = MethodologyOutput.model_validate_json(response)
            return result.model_dump()  # Valid! Return dict
        except ValidationError as e:
            # Tell LLM what went wrong
            prompt = f"Error: {e}. Try again..."
            response = await llm.complete(prompt)
    
    # All retries failed
    return {"error": "Validation failed"}
```

---

## 6. Multi-Agent Communication

### How MainAgent Delegates to LiteratureAgent:

```python
# In main_agent.py

async def _delegate_to_literature_agent(
    self,
    task: str,
    project_id: int,
    mode: str = "full"
):
    # 1. Set context (user_id, project_id)
    self.literature_agent.set_context(
        user_id=self.context.get('user_id'),
        project_id=project_id
    )
    
    # 2. Set mode (loads only relevant tools)
    self.literature_agent.set_mode(mode)
    
    # 3. Run the sub-agent
    result = await self.literature_agent.process(task)
    
    return result
```

### Context Passing:

```
User: "Extract methodology for Test Project"
       │
       ▼
MainAgent:
  context = {user_id: "abc", project_id: None}
       │
       │ finds project → id=5
       │
       ▼
MainAgent calls delegate_to_literature_agent(
    task="Extract methodology",
    project_id=5,
    mode="methodology"
)
       │
       ▼
LiteratureAgent:
  context = {user_id: "abc", project_id: 5}  ← Inherited!
  mode = "methodology"
  tools = [extract_methodology, update_methodology, ...]  ← Only 4 tools!
```

---

## 7. RAG Integration with LlamaIndex

### Where LlamaIndex is Used:

```
┌─────────────────────────────────────────────────────────────┐
│  YOU BUILT (Custom)                                         │
│  - FlexibleAgent (ReAct loop)                              │
│  - Tool definitions                                         │
│  - Pydantic validation                                      │
│  - Multi-agent delegation                                   │
└─────────────────────────────────────────────────────────────┘
        │
        │ uses
        ▼
┌─────────────────────────────────────────────────────────────┐
│  LLAMAINDEX (rag_engine.py)                                 │
│  - VectorStoreIndex (in-memory index)                       │
│  - PGVectorStore (PostgreSQL storage)                       │
│  - QueryFusionRetriever (hybrid search)                     │
│  - Nomic embeddings (768 dimensions)                        │
└─────────────────────────────────────────────────────────────┘
        │
        │ stores in
        ▼
┌─────────────────────────────────────────────────────────────┐
│  POSTGRESQL + PGVECTOR                                       │
│  - paper_sections (embedding VECTOR(768))                   │
│  - Cosine similarity search                                 │
└─────────────────────────────────────────────────────────────┘
```

### The RAG Flow:

```python
# In rag_engine.py (simplified)

class RAGEngine:
    async def query(self, query_text: str, top_k: int = 10):
        # 1. Embed the query using Nomic
        query_embedding = self.embed_model.get_query_embedding(query_text)
        
        # 2. Search vector store (LlamaIndex does this)
        retriever = self.index.as_retriever(similarity_top_k=top_k)
        nodes = await retriever.aretrieve(query_text)
        
        # 3. Return relevant chunks
        return {
            "source_nodes": [
                {"text": n.text, "metadata": n.metadata, "score": n.score}
                for n in nodes
            ]
        }
```

### Why We Use LlamaIndex for RAG but Not for Agents:

| Feature | LlamaIndex | Our Custom |
|---------|-----------|------------|
| **Embeddings** | ✅ Easy integration | More work |
| **Vector search** | ✅ Built-in | More work |
| **Hybrid search** | ✅ QueryFusionRetriever | More work |
| **Agent loop** | ❌ Less control | ✅ Full control |
| **Tool validation** | ❌ No Pydantic | ✅ Pydantic |
| **Multi-agent** | ❌ Complex | ✅ Simple |
| **Retry logic** | ❌ Basic | ✅ Custom |

---

## Summary: What You Learned

1. **ReAct Pattern**: Think → Act → Observe loop
2. **Tools**: Python functions with name, description, parameters
3. **Validation**: Pydantic ensures LLM output matches database schema
4. **Multi-Agent**: MainAgent routes, LiteratureAgent specializes
5. **Modes**: Load only relevant tools to reduce cost and confusion
6. **LlamaIndex**: Used for RAG (embeddings, vector search), not agents

---

## Next Steps

1. **Run the system** and watch the logs to see ReAct in action
2. **Add a new tool** by copying an existing one
3. **Add a new mode** to LiteratureReviewAgent
4. **Read the code** at:
   - `app/agents/base.py` - The ReAct loop
   - `app/agents/literature_agent.py` - Mode switching
   - `app/schemas/agent_outputs.py` - Pydantic validation
   - `app/core/rag_engine.py` - LlamaIndex integration
