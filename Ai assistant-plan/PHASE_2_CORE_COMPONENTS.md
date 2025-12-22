# Phase 2: Core Components with LlamaIndex + Nomic + Docling

**Duration**: Week 3-4  
**Goal**: Build RAG engine using LlamaIndex with YOUR Nomic embeddings, Groq LLM, Docling PDF parsing, and flexible agent framework

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 1 is complete**:

```bash
# 1. Verify Phase 1 tables exist
docker exec postgres-paper-search psql -U postgres -d research_db -c "\dt" | grep -E "paper_chunks|agent_conversations"
# Expected: All Phase 1 tables listed

# 2. Verify pgvector extension
docker exec postgres-paper-search psql -U postgres -d research_db -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
# Expected: pgvector extension shown

# 3. Verify LlamaIndex installed
.venv\Scripts\python.exe -c "from llama_index.core import VectorStoreIndex; print('✓ LlamaIndex ready')"
# Expected: "✓ LlamaIndex ready"

# 4. Verify Groq API key
.venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✓ API key loaded' if os.getenv('GROQ_API_KEY') else '❌ Missing API key')"
# Expected: "✓ API key loaded"

# 5. Verify Docling installed
.venv\Scripts\python.exe -c "from docling.document_converter import DocumentConverter; print('✓ Docling ready')"
# Expected: "✓ Docling ready"
```

**✅ You should have**:
- All Phase 1 database tables created
- LlamaIndex packages installed
- Groq API key configured
- Docling installed
- Project directories created

**❌ If missing, complete Phase 1 first**

---

## ✅ Checklist

### RAG Engine with LlamaIndex
- [ ] Create `backend/app/core/rag_engine.py`
- [ ] Setup LlamaIndex with YOUR Nomic embeddings
- [ ] Configure PGVectorStore with paper_chunks table
- [ ] Implement Docling PDF parsing
- [ ] Test document ingestion
- [ ] Test semantic search

### LLM Client
- [ ] Create `backend/app/core/llm_client.py`
- [ ] Implement Groq wrapper
- [ ] Add token counting
- [ ] Add cost tracking to llm_usage_logs
- [ ] Implement retry logic
- [ ] Test LLM connectivity

### Flexible Agent Framework
- [ ] Create `backend/app/agents/base.py`
- [ ] Implement Tool class
- [ ] Implement FlexibleAgent class
- [ ] Add ReAct loop (Think → Act → Observe)
- [ ] Add memory management
- [ ] Test with simple tools

### Memory System
- [ ] Create `backend/app/core/memory.py`
- [ ] Implement conversation memory
- [ ] Add context management
- [ ] Add persistent storage to agent_messages
- [ ] Test memory retrieval

---

## 📋 Step-by-Step Implementation

### 1. RAG Engine with LlamaIndex + YOUR Nomic Embeddings

Create `backend/app/core/rag_engine.py`:

```python
"""
RAG Engine using LlamaIndex with YOUR existing Nomic embeddings
Integrates with Docling for academic PDF parsing
"""
from llama_index.core import VectorStoreIndex, Settings, StorageContext, Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from sqlalchemy import make_url
from docling.document_converter import DocumentConverter
import os

class RAGEngine:
    """
    LlamaIndex-powered RAG engine using YOUR Nomic embeddings (768 dims)
    Parses PDFs with Docling to extract equations, tables, images
    """
    
    def __init__(self, db_url: str = None):
        # Database connection
        db_url = db_url or os.getenv('DATABASE_URL')
        url = make_url(db_url)
        
        # Use YOUR existing Nomic model (same as EnhancedVectorService)
        print("🔧 Initializing Nomic embeddings (nomic-ai/nomic-embed-text-v1.5)...")
        self.embed_model = HuggingFaceEmbedding(
            model_name="nomic-ai/nomic-embed-text-v1.5",
            trust_remote_code=True
        )
        
        # Initialize Groq LLM
        print("🔧 Initializing Groq LLM (llama-3.1-70b-versatile)...")
        self.llm = Groq(
            model="llama-3.1-70b-versatile",
            api_key=os.getenv('GROQ_API_KEY')
        )
        
        # Configure LlamaIndex global settings
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize pgvector store (connects to YOUR paper_chunks table)
        print("🔧 Connecting to pgvector (paper_chunks table)...")
        self.vector_store = PGVectorStore.from_params(
            database=url.database,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="paper_chunks",
            embed_dim=768  # YOUR Nomic model dimension
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
        
        print("✅ RAG Engine initialized successfully!")
    
    async def ingest_paper_with_docling(
        self, 
        paper_id: int, 
        pdf_path: str,
        metadata: dict = None
    ) -> dict:
        """
        Parse PDF with Docling and ingest into LlamaIndex
        
        Args:
            paper_id: ID from YOUR papers table
            pdf_path: Path to PDF file
            metadata: Optional metadata (project_id, etc.)
        
        Returns:
            dict with ingestion stats
        """
        print(f"\n📄 Processing paper {paper_id} with Docling...")
        
        # Parse PDF with Docling (extracts equations, images, tables)
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        documents = []
        stats = {
            'total_elements': 0,
            'equations': 0,
            'tables': 0,
            'images': 0,
            'text_chunks': 0
        }
        
        # Convert Docling elements to LlamaIndex Documents
        for element in result.document.iterate_items():
            stats['total_elements'] += 1
            
            # Track special elements
            if hasattr(element, 'has_math') and element.has_math:
                stats['equations'] += 1
            if hasattr(element, 'has_table') and element.has_table:
                stats['tables'] += 1
            if hasattr(element, 'has_figure') and element.has_figure:
                stats['images'] += 1
            
            # Create LlamaIndex Document with rich metadata
            doc = Document(
                text=element.text,
                metadata={
                    "paper_id": paper_id,
                    "section_type": element.label if hasattr(element, 'label') else "unknown",
                    "has_equation": getattr(element, 'has_math', False),
                    "has_table": getattr(element, 'has_table', False),
                    "has_image": getattr(element, 'has_figure', False),
                    **(metadata or {})
                }
            )
            documents.append(doc)
        
        print(f"  📊 Extracted {stats['total_elements']} elements:")
        print(f"     - {stats['equations']} equations")
        print(f"     - {stats['tables']} tables")
        print(f"     - {stats['images']} images")
        
        # Parse into nodes (chunks) with LlamaIndex
        parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        nodes = parser.get_nodes_from_documents(documents)
        stats['text_chunks'] = len(nodes)
        
        print(f"  ✂️  Created {len(nodes)} text chunks")
        
        # Insert into vector store (uses YOUR Nomic embeddings automatically!)
        print(f"  🧠 Generating embeddings with YOUR Nomic model...")
        self.index.insert_nodes(nodes)
        
        print(f"  ✅ Successfully ingested paper {paper_id}")
        
        return stats
    
    async def query(
        self,
        query_text: str,
        project_id: int = None,
        section_filter: list = None,
        top_k: int = 10,
        return_sources: bool = True
    ) -> dict:
        """
        Query using LlamaIndex with filters
        
        Args:
            query_text: Natural language query
            project_id: Filter by YOUR project_id
            section_filter: Filter by section types (e.g., ['methodology', 'results'])
            top_k: Number of results
            return_sources: Include source chunks
        
        Returns:
            dict with answer and source nodes
        """
        print(f"\n🔍 Querying: '{query_text}'")
        
        # Build metadata filters
        filters = []
        if project_id:
            filters.append(
                ExactMatchFilter(key="project_id", value=project_id)
            )
            print(f"  📁 Filtering by project_id={project_id}")
        
        if section_filter:
            for section in section_filter:
                filters.append(
                    ExactMatchFilter(key="section_type", value=section)
                )
            print(f"  📑 Filtering by sections: {section_filter}")
        
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        # Create query engine
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            filters=metadata_filters
        )
        
        # Execute query (uses YOUR Nomic embeddings!)
        print(f"  🧠 Searching with YOUR Nomic embeddings...")
        response = query_engine.query(query_text)
        
        result = {
            'answer': str(response),
            'source_nodes': []
        }
        
        if return_sources:
            result['source_nodes'] = [
                {
                    'text': node.node.text,
                    'score': node.score,
                    'metadata': node.node.metadata,
                    'paper_id': node.node.metadata.get('paper_id'),
                    'section_type': node.node.metadata.get('section_type'),
                    'has_equation': node.node.metadata.get('has_equation', False),
                    'has_table': node.node.metadata.get('has_table', False)
                }
                for node in response.source_nodes
            ]
            print(f"  ✅ Found {len(result['source_nodes'])} relevant chunks")
        
        return result
    
    async def retrieve_only(
        self,
        query_text: str,
        project_id: int = None,
        top_k: int = 10
    ) -> list:
        """
        Retrieve relevant chunks without LLM generation
        Useful for getting context without generating answer
        """
        print(f"\n🔍 Retrieving chunks for: '{query_text}'")
        
        # Build filters
        filters = []
        if project_id:
            filters.append(
                ExactMatchFilter(key="project_id", value=project_id)
            )
        
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        # Create retriever
        retriever = self.index.as_retriever(
            similarity_top_k=top_k,
            filters=metadata_filters
        )
        
        # Retrieve nodes
        nodes = retriever.retrieve(query_text)
        
        chunks = [
            {
                'text': node.node.text,
                'score': node.score,
                'metadata': node.node.metadata
            }
            for node in nodes
        ]
        
        print(f"  ✅ Retrieved {len(chunks)} chunks")
        return chunks
```

**Test the RAG Engine**:

Create `backend/test_rag_engine.py`:

```python
import asyncio
from app.core.rag_engine import RAGEngine

async def test_rag():
    # Initialize
    rag = RAGEngine()
    
    # Test ingestion (use a sample PDF)
    stats = await rag.ingest_paper_with_docling(
        paper_id=999,
        pdf_path="path/to/sample.pdf",
        metadata={"project_id": 1}
    )
    print(f"\n✅ Ingestion stats: {stats}")
    
    # Test query
    result = await rag.query(
        query_text="What methodology was used?",
        project_id=1,
        section_filter=["methodology"],
        top_k=5
    )
    print(f"\n✅ Query result: {result['answer']}")
    print(f"   Sources: {len(result['source_nodes'])} chunks")
    
    # Test retrieval only
    chunks = await rag.retrieve_only(
        query_text="machine learning",
        top_k=3
    )
    print(f"\n✅ Retrieved {len(chunks)} chunks")

if __name__ == "__main__":
    asyncio.run(test_rag())
```

Run test:
```bash
cd backend
.venv\Scripts\python.exe test_rag_engine.py
```

---

### 2. LLM Client with Groq

Create `backend/app/core/llm_client.py`:

```python
"""
Groq LLM client with cost tracking and retry logic
Logs all usage to llm_usage_logs table
"""
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
import time
from sqlalchemy import text
from typing import Optional
import os

class LLMClient:
    """Groq LLM client with automatic cost tracking"""
    
    def __init__(self, db=None):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.db = db
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Groq pricing (per 1M tokens) - Updated prices
        self.pricing = {
            "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
            "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
            "llama-3.2-90b-vision-preview": {"input": 0.90, "output": 0.90}
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
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
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate completion with Groq
        
        Args:
            prompt: User prompt
            model: Groq model name
            temperature: 0-1, higher = more creative
            max_tokens: Max output tokens
            user_id: For logging
            conversation_id: For logging
            system_prompt: Optional system message
        
        Returns:
            Generated text
        """
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            output_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate cost
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log usage to YOUR llm_usage_logs table
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
            
            print(f"💰 LLM cost: ${cost:.6f} ({input_tokens} in + {output_tokens} out tokens)")
            
            return output_text
            
        except Exception as e:
            # Log error
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
        """Calculate cost in USD"""
        pricing = self.pricing.get(model, self.pricing["llama-3.1-70b-versatile"])
        cost = (input_tokens / 1_000_000) * pricing["input"] + \
               (output_tokens / 1_000_000) * pricing["output"]
        return round(cost, 6)
    
    async def _log_usage(self, **kwargs):
        """Log to YOUR llm_usage_logs table"""
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

**Test LLM Client**:

```python
# backend/test_llm_client.py
import asyncio
from app.core.llm_client import LLMClient

async def test_llm():
    llm = LLMClient()
    
    # Test simple completion
    response = await llm.complete(
        prompt="Explain machine learning in one sentence",
        model="llama-3.1-8b-instant"  # Cheaper model for testing
    )
    print(f"✅ Response: {response}")
    
    # Test with system prompt
    response = await llm.complete(
        prompt="What is deep learning?",
        system_prompt="You are a helpful AI research assistant. Be concise.",
        temperature=0.3
    )
    print(f"✅ Response: {response}")

if __name__ == "__main__":
    asyncio.run(test_llm())
```

---

### 3. Flexible Agent Base Class

Create `backend/app/agents/base.py`:

```python
"""
Flexible agent framework with ReAct pattern
Agents can use tools, maintain memory, and make autonomous decisions
"""
from typing import List, Dict, Any, Callable
from pydantic import BaseModel
import json

class Tool(BaseModel):
    """Tool definition for agents"""
    name: str
    description: str
    parameters: Dict[str, str]
    function: Callable
    
    class Config:
        arbitrary_types_allowed = True

class FlexibleAgent:
    """
    Autonomous agent using ReAct (Reasoning + Acting) pattern
    
    Flow:
    1. Think: Agent reasons about current state
    2. Act: Agent decides to use tool, delegate, or finish
    3. Observe: Agent sees result and updates memory
    4. Repeat until task complete
    """
    
    def __init__(self, name: str, llm_client, tools: List[Tool]):
        self.name = name
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.memory = []
        self.context = {}
    
    async def run(self, task: str, max_iterations: int = 10) -> Dict:
        """
        Main agent loop - decides actions dynamically
        
        Args:
            task: User task description
            max_iterations: Max thinking iterations
        
        Returns:
            Final result or status
        """
        self.memory.append({"role": "user", "content": task})
        
        for iteration in range(max_iterations):
            print(f"\n🤖 Iteration {iteration + 1}/{max_iterations}")
            
            # STEP 1: Agent thinks
            thought = await self._think()
            print(f"💭 Thought: {thought[:200]}...")
            
            # STEP 2: Agent decides action
            action = await self._decide_action(thought)
            print(f"🎯 Action: {action['type']} - {action.get('tool_name', 'N/A')}")
            
            if action['type'] == 'finish':
                print(f"✅ Task complete!")
                return action['result']
            
            elif action['type'] == 'use_tool':
                result = await self._execute_tool(
                    action['tool_name'],
                    action['parameters']
                )
                self.memory.append({
                    "role": "assistant",
                    "content": f"Used {action['tool_name']}: {result}"
                })
                print(f"🔧 Tool result: {str(result)[:200]}...")
            
            elif action['type'] == 'ask_user':
                return {
                    'status': 'needs_input',
                    'question': action['question']
                }
        
        return {
            'status': 'max_iterations',
            'message': 'Reached maximum iterations without completing task'
        }
    
    async def _think(self) -> str:
        """Agent reasons about current state"""
        prompt = f"""You are {self.name}, an AI assistant for literature review.

Available tools:
{self._format_tools()}

Conversation history:
{self._format_memory()}

Current context:
{json.dumps(self.context, indent=2)}

Think step by step:
1. What is the current goal?
2. What information do I have?
3. What information do I need?
4. What should I do next?

Provide your reasoning."""
        
        return await self.llm.complete(prompt, temperature=0.7)
    
    async def _decide_action(self, thought: str) -> Dict:
        """Based on reasoning, decide next action"""
        prompt = f"""Based on this reasoning:
{thought}

Available tools:
{self._format_tools()}

Decide your next action. Respond with JSON ONLY (no markdown, no explanation):

{{
    "type": "use_tool" | "finish" | "ask_user",
    "tool_name": "tool_name_here",
    "parameters": {{"param1": "value1"}},
    "result": "final answer if finishing",
    "question": "question for user if asking",
    "reasoning": "why this action"
}}"""
        
        response = await self.llm.complete(prompt, temperature=0.3)
        
        # Parse JSON (handle markdown code blocks)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        return json.loads(response.strip())
    
    async def _execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Execute a tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available: {list(self.tools.keys())}")
        
        tool = self.tools[tool_name]
        return await tool.function(**parameters)
    
    def _format_tools(self) -> str:
        """Format tools for prompt"""
        return "\n".join([
            f"- {name}: {tool.description}\n  Parameters: {tool.parameters}"
            for name, tool in self.tools.items()
        ])
    
    def _format_memory(self) -> str:
        """Format conversation memory"""
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.memory[-5:]  # Last 5 messages
        ])
```

**Test Agent**:

```python
# backend/test_agent.py
import asyncio
from app.agents.base import FlexibleAgent, Tool
from app.core.llm_client import LLMClient

# Simple test tool
async def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny, 72°F"

async def test_agent():
    llm = LLMClient()
    
    tools = [
        Tool(
            name="get_weather",
            description="Get current weather for a location",
            parameters={"location": "string - city name"},
            function=get_weather
        )
    ]
    
    agent = FlexibleAgent("TestAgent", llm, tools)
    
    result = await agent.run("What's the weather in San Francisco?")
    print(f"\n✅ Final result: {result}")

if __name__ == "__main__":
    asyncio.run(test_agent())
```

---

### 4. Memory Management

Create `backend/app/core/memory.py`:

```python
"""
Conversation memory management
Stores messages in YOUR agent_messages table
"""
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime

class ConversationMemory:
    """
    Persistent conversation memory
    Stores in YOUR agent_messages table
    """
    
    def __init__(self, db, conversation_id: str):
        self.db = db
        self.conversation_id = conversation_id
    
    async def add_message(
        self,
        role: str,
        content: str,
        metadata: dict = None
    ):
        """
        Add message to memory
        
        Args:
            role: 'user', 'assistant', 'system', or 'tool'
            content: Message content
            metadata: Optional metadata
        """
        await self.db.execute(
            text("""
                INSERT INTO agent_messages (
                    conversation_id, role, content, metadata
                ) VALUES (:conv_id, :role, :content, :metadata)
            """),
            {
                'conv_id': self.conversation_id,
                'role': role,
                'content': content,
                'metadata': metadata or {}
            }
        )
        await self.db.commit()
    
    async def get_history(self, last_n: int = 10) -> List[Dict]:
        """Get conversation history"""
        result = await self.db.execute(
            text("""
                SELECT role, content, metadata, created_at
                FROM agent_messages
                WHERE conversation_id = :conv_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {'conv_id': self.conversation_id, 'limit': last_n}
        )
        
        messages = [dict(row._mapping) for row in reversed(result.fetchall())]
        return messages
    
    async def update_context(self, key: str, value: Any):
        """Update conversation context in agent_conversations table"""
        await self.db.execute(
            text("""
                UPDATE agent_conversations
                SET metadata = jsonb_set(
                    COALESCE(metadata, '{}'::jsonb),
                    :key_path,
                    :value::jsonb
                )
                WHERE id = :conv_id
            """),
            {
                'conv_id': self.conversation_id,
                'key_path': f'{{{key}}}',
                'value': json.dumps(value)
            }
        )
        await self.db.commit()
    
    async def get_context(self) -> Dict:
        """Get conversation context"""
        result = await self.db.execute(
            text("""
                SELECT metadata
                FROM agent_conversations
                WHERE id = :conv_id
            """),
            {'conv_id': self.conversation_id}
        )
        
        row = result.fetchone()
        return row.metadata if row else {}
```

---

## 🧪 Verification

Create `backend/test_phase2.py`:

```python
import asyncio
from app.core.rag_engine import RAGEngine
from app.core.llm_client import LLMClient
from app.agents.base import FlexibleAgent, Tool

async def test_all():
    print("=" * 60)
    print("🧪 Phase 2 Verification Test")
    print("=" * 60)
    
    # Test RAG Engine
    print("\n1️⃣ Testing RAG Engine...")
    rag = RAGEngine()
    print("   ✅ RAG Engine initialized")
    
    # Test LLM Client
    print("\n2️⃣ Testing LLM Client...")
    llm = LLMClient()
    response = await llm.complete("Say hello in one word", model="llama-3.1-8b-instant")
    print(f"   ✅ LLM response: {response}")
    
    # Test Agent
    print("\n3️⃣ Testing Flexible Agent...")
    async def test_tool(message: str) -> str:
        return f"Tool executed: {message}"
    
    tools = [
        Tool(
            name="test_tool",
            description="A test tool",
            parameters={"message": "string"},
            function=test_tool
        )
    ]
    
    agent = FlexibleAgent("TestAgent", llm, tools)
    print("   ✅ Agent initialized")
    
    print("\n" + "=" * 60)
    print("✅ Phase 2 verification PASSED!")
    print("=" * 60)
    print("\n🎯 Next steps:")
    print("   1. Test with real PDF using Docling")
    print("   2. Proceed to Phase 3: Tools & Agents")

if __name__ == "__main__":
    asyncio.run(test_all())
```

Run verification:
```bash
cd backend
.venv\Scripts\python.exe test_phase2.py
```

---

## 📝 Deliverables

- ✅ RAG engine with LlamaIndex + YOUR Nomic embeddings + Docling
- ✅ LLM client with Groq + cost tracking
- ✅ Flexible agent base class with ReAct pattern
- ✅ Memory management with persistent storage
- ✅ All tests passing

---

## ⏭️ Next Phase

Proceed to **Phase 3: Tools & Sub-Agents** to build specialized tools for YOUR database tables.
