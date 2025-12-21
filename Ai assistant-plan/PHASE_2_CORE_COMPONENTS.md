# Phase 2: Core Components with LlamaIndex

**Duration**: Week 3-4  
**Goal**: Build LlamaIndex RAG engine, LLM client, flexible agent framework, and memory system

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 1 is complete**:

```bash
# 1. Verify Phase 1 tables exist
psql -U postgres -d your_database -c "\dt" | grep -E "paper_chunks|agent_conversations|agent_messages"
# Expected: All Phase 1 tables listed

# 2. Verify pgvector extension
psql -U postgres -d your_database -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Expected: pgvector extension shown

# 3. Verify LlamaIndex installed
python -c "from llama_index.core import VectorStoreIndex; print('✓ LlamaIndex ready')"
# Expected: "✓ LlamaIndex ready"

# 4. Verify Groq API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✓ API key loaded' if os.getenv('GROQ_API_KEY') else '❌ Missing API key')"
# Expected: "✓ API key loaded"

# 5. Check project structure
ls backend/app/agents backend/app/tools backend/app/core
# Expected: Directories exist from Phase 1
```

**✅ You should have**:
- All Phase 1 database tables created
- LlamaIndex installed
- Groq API key configured
- Project directories created

**❌ If missing, complete Phase 1 first**

---

## ✅ Checklist

### LlamaIndex RAG Engine
- [ ] Create `backend/app/core/rag_engine.py`
- [ ] Setup PGVectorStore with LlamaIndex
- [ ] Configure embedding model
- [ ] Test document ingestion
- [ ] Test semantic search

### LLM Client
- [ ] Create `backend/app/core/llm_client.py`
- [ ] Implement Groq wrapper with LlamaIndex
- [ ] Add token counting
- [ ] Add cost tracking
- [ ] Implement retry logic

### Flexible Agent Framework
- [ ] Create `backend/app/agents/base.py`
- [ ] Implement ReAct loop
- [ ] Add tool execution
- [ ] Add sub-agent delegation
- [ ] Implement memory management

### Memory System
- [ ] Create `backend/app/core/memory.py`
- [ ] Implement conversation memory
- [ ] Add context management
- [ ] Add persistent storage

---

## 📋 Implementation

### 1. LlamaIndex RAG Engine

Create `backend/app/core/rag_engine.py`:

```python
from llama_index.core import VectorStoreIndex, Settings, StorageContext
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy import make_url
import os

class RAGEngine:
    """
    LlamaIndex-powered RAG engine with pgvector
    """
    
    def __init__(self, db_url: str = None):
        # Database connection
        db_url = db_url or os.getenv('DATABASE_URL')
        url = make_url(db_url)
        
        # Initialize embedding model
        self.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en-v1.5"
        )
        
        # Initialize LLM
        self.llm = Groq(
            model="llama-3.1-70b-versatile",
            api_key=os.getenv('GROQ_API_KEY')
        )
        
        # Configure LlamaIndex settings
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize vector store
        self.vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="paper_chunks",
            embed_dim=384  # bge-small dimension
        )
        
        # Create storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # Initialize index
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context
        )
    
    async def ingest_paper(self, paper_id: int, text: str, metadata: dict = None):
        """
        Ingest a paper into the vector store
        """
        from llama_index.core import Document
        
        # Create document
        doc = Document(
            text=text,
            metadata={
                "paper_id": paper_id,
                **(metadata or {})
            }
        )
        
        # Parse into nodes (chunks)
        parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        nodes = parser.get_nodes_from_documents([doc])
        
        # Insert into vector store
        self.index.insert_nodes(nodes)
        
        return len(nodes)
    
    async def query(
        self,
        query_text: str,
        filters: dict = None,
        top_k: int = 10
    ):
        """
        Semantic search using LlamaIndex
        """
        from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
        
        # Build metadata filters
        metadata_filters = None
        if filters:
            filter_list = []
            
            if filters.get('project_id'):
                filter_list.append(
                    ExactMatchFilter(key="project_id", value=filters['project_id'])
                )
            
            if filters.get('section_type'):
                filter_list.append(
                    ExactMatchFilter(key="section_type", value=filters['section_type'])
                )
            
            if filter_list:
                metadata_filters = MetadataFilters(filters=filter_list)
        
        # Create query engine
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            filters=metadata_filters
        )
        
        # Execute query
        response = query_engine.query(query_text)
        
        return {
            'answer': str(response),
            'source_nodes': [
                {
                    'text': node.node.text,
                    'score': node.score,
                    'metadata': node.node.metadata
                }
                for node in response.source_nodes
            ]
        }
    
    async def retrieve_only(
        self,
        query_text: str,
        filters: dict = None,
        top_k: int = 10
    ):
        """
        Retrieve relevant chunks without LLM generation
        """
        retriever = self.index.as_retriever(
            similarity_top_k=top_k
        )
        
        nodes = retriever.retrieve(query_text)
        
        return [
            {
                'text': node.node.text,
                'score': node.score,
                'metadata': node.node.metadata
            }
            for node in nodes
        ]
```

### 2. LLM Client with Cost Tracking

Create `backend/app/core/llm_client.py`:

```python
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
import time
from sqlalchemy import text
from typing import Optional
import os

class LLMClient:
    """Groq LLM client with tracking"""
    
    def __init__(self, db=None):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.db = db
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        self.pricing = {
            "llama-3.1-70b-versatile": {"input": 0.00059, "output": 0.00079},
            "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00008}
        }
    
    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def complete(
        self,
        prompt: str,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        start_time = time.time()
        
        try:
            input_tokens = self.count_tokens(prompt)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            output_text = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            duration_ms = int((time.time() - start_time) * 1000)
            
            if self.db:
                await self._log_usage(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost_usd=cost,
                    duration_ms=duration_ms,
                    success=True
                )
            
            return output_text
            
        except Exception as e:
            if self.db:
                await self._log_usage(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    model=model,
                    success=False,
                    error=str(e)
                )
            raise
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = self.pricing.get(model, self.pricing["llama-3.1-70b-versatile"])
        return round((input_tokens / 1000) * pricing["input"] + (output_tokens / 1000) * pricing["output"], 6)
    
    async def _log_usage(self, **kwargs):
        await self.db.execute(
            text("""
                INSERT INTO llm_usage_logs (
                    user_id, conversation_id, model,
                    input_tokens, output_tokens, total_tokens,
                    cost_usd, duration_ms, success, error
                ) VALUES (
                    :user_id, :conversation_id, :model,
                    :input_tokens, :output_tokens, :total_tokens,
                    :cost_usd, :duration_ms, :success, :error
                )
            """),
            kwargs
        )
        await self.db.commit()
```

### 3. Flexible Agent Base Class

Create `backend/app/agents/base.py`:

```python
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel
import json

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, str]
    function: Callable

class AgentMemory:
    def __init__(self):
        self.messages: List[Dict] = []
        self.context: Dict[str, Any] = {}
        self.tool_history: List[Dict] = []
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def add_tool_result(self, tool_name: str, result: Any):
        self.context[f"last_{tool_name}_result"] = result
        self.tool_history.append({"tool": tool_name, "result": result})
    
    def get_recent_messages(self, n: int = 5) -> List[Dict]:
        return self.messages[-n:]

class FlexibleAgent:
    """Autonomous agent with ReAct pattern"""
    
    def __init__(self, name: str, llm_client, tools: List[Tool]):
        self.name = name
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.memory = AgentMemory()
        self.sub_agents: Dict[str, 'FlexibleAgent'] = {}
    
    async def run(self, task: str, max_iterations: int = 10) -> Dict:
        self.memory.add_message("user", task)
        
        for iteration in range(max_iterations):
            thought = await self._think()
            action = await self._decide_action(thought)
            
            if action['type'] == 'finish':
                return action['result']
            
            elif action['type'] == 'use_tool':
                result = await self._execute_tool(
                    action['tool_name'],
                    action['parameters']
                )
                self.memory.add_tool_result(action['tool_name'], result)
                self.memory.add_message("assistant", f"Used {action['tool_name']}: {result}")
            
            elif action['type'] == 'delegate':
                result = await self._delegate_to_agent(
                    action['agent_name'],
                    action['task']
                )
                self.memory.add_message("assistant", f"Delegated to {action['agent_name']}: {result}")
            
            elif action['type'] == 'ask_user':
                return {'status': 'needs_input', 'question': action['question']}
        
        return {'status': 'max_iterations', 'message': 'Reached maximum iterations'}
    
    async def _think(self) -> str:
        prompt = f"""You are {self.name}, an AI assistant.

Available tools:
{self._format_tools()}

Conversation history:
{self._format_memory()}

Current context:
{json.dumps(self.memory.context, indent=2)}

Think step by step:
1. What is the goal?
2. What information do I have?
3. What should I do next?

Provide your reasoning."""
        
        return await self.llm.complete(prompt)
    
    async def _decide_action(self, thought: str) -> Dict:
        prompt = f"""Based on this reasoning:
{thought}

Available tools:
{self._format_tools()}

Decide your next action. Respond with JSON only:

{{
    "type": "use_tool" | "delegate" | "finish" | "ask_user",
    "tool_name": "...",
    "parameters": {{}},
    "result": "...",
    "reasoning": "..."
}}"""
        
        response = await self.llm.complete(prompt, temperature=0.3)
        return json.loads(response)
    
    async def _execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        return await tool.function(**parameters)
    
    async def _delegate_to_agent(self, agent_name: str, task: str) -> Any:
        if agent_name not in self.sub_agents:
            raise ValueError(f"Sub-agent {agent_name} not found")
        
        return await self.sub_agents[agent_name].run(task)
    
    def _format_tools(self) -> str:
        return "\n".join([
            f"- {name}: {tool.description}\n  Parameters: {tool.parameters}"
            for name, tool in self.tools.items()
        ])
    
    def _format_memory(self) -> str:
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.memory.get_recent_messages()
        ])
```

---

## 🧪 Testing

Create `backend/test_phase2.py`:

```python
import asyncio
from backend.app.core.rag_engine import RAGEngine
from backend.app.core.llm_client import LLMClient

async def test_rag_engine():
    rag = RAGEngine()
    
    # Test ingestion
    num_chunks = await rag.ingest_paper(
        paper_id=999,
        text="This is a test paper about AI in healthcare.",
        metadata={"section_type": "abstract"}
    )
    print(f"✓ RAG ingestion: {num_chunks} chunks created")
    
    # Test retrieval
    results = await rag.retrieve_only("AI healthcare", top_k=5)
    print(f"✓ RAG retrieval: {len(results)} results")

async def test_llm_client():
    llm = LLMClient()
    response = await llm.complete("Say hello in one word")
    print(f"✓ LLM client: {response}")

if __name__ == "__main__":
    asyncio.run(test_rag_engine())
    asyncio.run(test_llm_client())
    print("\n✅ Phase 2 verification complete!")
```

---

## 📝 Deliverables

- ✅ LlamaIndex RAG engine with pgvector
- ✅ LLM client with cost tracking
- ✅ Flexible agent base class
- ✅ Memory management system
- ✅ All tests passing

---

## ⏭️ Next Phase

Proceed to **Phase 3: Tools & Sub-Agents** to build specialized tools and orchestrator.
