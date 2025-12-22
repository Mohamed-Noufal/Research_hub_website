# AI Assistant Implementation Plan - Customized for Your Project

## 🎯 Overview

This plan integrates an AI assistant into your existing literature review platform, leveraging:
- **Existing Nomic Embeddings**: `nomic-ai/nomic-embed-text-v1.5` (768 dimensions) already in `EnhancedVectorService`
- **LlamaIndex RAG Framework**: For easy RAG implementation and learning
- **Docling PDF Parser**: For accurate extraction of equations, images, tables, and academic content
- **Groq LLM**: For fast, cost-effective AI responses
- **Existing Database**: Seamless integration with current tables and workflows

---

## 📊 Current State Analysis

### ✅ Already Implemented
- **Vector Search**: `EnhancedVectorService` with Nomic embeddings (768 dims)
- **Database**: PostgreSQL with pgvector extension (v0.8.1)
- **Embeddings**: 768-dimensional vectors for papers
- **Hybrid Search**: Semantic + keyword search
- **Category System**: AI/CS, Medicine, Agriculture, Humanities, Economics

### 🔧 What We're Adding
- **Agent System**: 6 new tables for conversations, messages, tool calls, and logs
- **LlamaIndex RAG**: Easy-to-use RAG framework with your Nomic embeddings
- **Docling Parser**: Extract equations, images, tables from PDFs
- **AI Assistant**: Chat interface with autonomous task execution
- **Real-time Updates**: WebSocket for UI synchronization

---

## 📋 Phase 1: Foundation & Database Setup ✅ COMPLETED

### Database Migration ✅
- [x] Created `020_agent_system.sql` with 6 tables:
  - `paper_chunks`: Store PDF chunks with embeddings (768 dims for Nomic)
  - `agent_conversations`: Track user conversations
  - `agent_messages`: Store chat history
  - `agent_tool_calls`: Log tool executions
  - `llm_usage_logs`: Track LLM costs
  - `rag_usage_logs`: Monitor RAG performance

### Project Structure ✅
- [x] Created `backend/app/agents/` directory
- [x] Created `backend/app/tools/` directory
- [x] Updated `config.py` with AI agent settings

### Dependencies ✅
```txt
# Core (already have)
fastapi, sqlalchemy, psycopg2-binary, pgvector

# LlamaIndex (RAG Framework)
llama-index-core              # Core RAG functionality
llama-index-llms-groq         # Groq LLM integration
llama-index-embeddings-huggingface  # Use YOUR Nomic model
llama-index-vector-stores-postgres  # pgvector integration

# AI & Embeddings
sentence-transformers  # Your existing Nomic model
groq                   # LLM
tiktoken              # Token counting

# PDF Parsing
docling               # Academic PDF parser
docling-core          # Core parsing engine

# Utilities
tenacity              # Retry logic
websockets            # Real-time updates
redis                 # Caching
```

---

## 📋 Phase 2: Core Components with LlamaIndex + Nomic

### 2.1 RAG Engine (LlamaIndex + YOUR Nomic Embeddings)

**File**: `backend/app/core/rag_engine.py`

```python
from llama_index.core import VectorStoreIndex, Settings, StorageContext, Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.node_parser import SentenceSplitter
from sqlalchemy import make_url
import os

class RAGEngine:
    """
    LlamaIndex-powered RAG engine using YOUR Nomic embeddings
    """
    
    def __init__(self, db_url: str = None):
        # Database connection
        db_url = db_url or os.getenv('DATABASE_URL')
        url = make_url(db_url)
        
        # Use YOUR existing Nomic model!
        self.embed_model = HuggingFaceEmbedding(
            model_name="nomic-ai/nomic-embed-text-v1.5",
            trust_remote_code=True
        )
        
        # Initialize Groq LLM
        self.llm = Groq(
            model="llama-3.1-70b-versatile",
            api_key=os.getenv('GROQ_API_KEY')
        )
        
        # Configure LlamaIndex global settings
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize pgvector store
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
    
    async def ingest_paper_with_docling(self, paper_id: int, pdf_path: str):
        """
        Parse PDF with Docling and ingest into LlamaIndex
        """
        from docling.document_converter import DocumentConverter
        
        # Parse PDF with Docling (extracts equations, images, tables)
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        documents = []
        for element in result.document.iterate_items():
            # Create LlamaIndex Document with metadata
            doc = Document(
                text=element.text,
                metadata={
                    "paper_id": paper_id,
                    "section_type": element.label,
                    "has_equation": element.has_math,
                    "has_table": element.has_table,
                    "has_image": element.has_figure
                }
            )
            documents.append(doc)
        
        # Parse into nodes (chunks) with LlamaIndex
        parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        nodes = parser.get_nodes_from_documents(documents)
        
        # Insert into vector store (uses YOUR Nomic embeddings automatically!)
        self.index.insert_nodes(nodes)
        
        return len(nodes)
    
    async def query(
        self,
        query_text: str,
        project_id: int = None,
        section_filter: list = None,
        top_k: int = 10
    ):
        """
        Query using LlamaIndex with filters
        """
        from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
        
        # Build metadata filters
        filters = []
        if project_id:
            filters.append(
                ExactMatchFilter(key="project_id", value=project_id)
            )
        if section_filter:
            filters.append(
                ExactMatchFilter(key="section_type", value=section_filter)
            )
        
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        # Create query engine
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            filters=metadata_filters
        )
        
        # Execute query (uses YOUR Nomic embeddings!)
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

### 2.2 LLM Client with Groq

**File**: `backend/app/core/llm_client.py`

```python
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken
import time
from sqlalchemy import text
import os

class LLMClient:
    """Groq LLM client with cost tracking"""
    
    def __init__(self, db=None):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.db = db
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Groq pricing (per 1M tokens)
        self.pricing = {
            "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
            "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08}
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(
        self,
        prompt: str,
        model: str = "llama-3.1-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        user_id: str = None,
        conversation_id: str = None
    ) -> str:
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            output_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
            # Calculate cost
            cost = (input_tokens / 1_000_000) * self.pricing[model]["input"] + \
                   (output_tokens / 1_000_000) * self.pricing[model]["output"]
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log usage
            if self.db:
                await self._log_usage(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens,
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

### 2.3 Flexible Agent Base Class

**File**: `backend/app/agents/base.py`

```python
from typing import List, Dict, Any, Callable
from pydantic import BaseModel
import json

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, str]
    function: Callable

class FlexibleAgent:
    """Autonomous agent with ReAct pattern"""
    
    def __init__(self, name: str, llm_client, tools: List[Tool]):
        self.name = name
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.memory = []
        self.context = {}
    
    async def run(self, task: str, max_iterations: int = 10):
        """Main agent loop - decides actions dynamically"""
        self.memory.append({"role": "user", "content": task})
        
        for iteration in range(max_iterations):
            # Agent thinks
            thought = await self._think()
            
            # Agent decides action
            action = await self._decide_action(thought)
            
            if action['type'] == 'finish':
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
        
        return {'status': 'max_iterations'}
    
    async def _think(self) -> str:
        prompt = f"""You are {self.name}, an AI assistant.

Available tools:
{self._format_tools()}

Conversation history:
{self._format_memory()}

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
    "type": "use_tool" | "finish" | "ask_user",
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
    
    def _format_tools(self) -> str:
        return "\n".join([
            f"- {name}: {tool.description}\n  Parameters: {tool.parameters}"
            for name, tool in self.tools.items()
        ])
    
    def _format_memory(self) -> str:
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.memory[-5:]
        ])
```

---

## 📋 Phase 3: Tools & Integration

### Database Tools (Use YOUR existing tables)

**File**: `backend/app/tools/database_tools.py`

```python
from sqlalchemy import text
from typing import List, Dict

async def get_project_papers(project_id: int, db) -> List[Dict]:
    """Get papers from YOUR existing project_papers table"""
    result = await db.execute(
        text("""
            SELECT p.id, p.title, p.authors, p.abstract
            FROM papers p
            JOIN project_papers pp ON pp.paper_id = p.id
            WHERE pp.project_id = :project_id
        """),
        {'project_id': project_id}
    )
    return [dict(row._mapping) for row in result.fetchall()]

async def update_comparison_tab(
    user_id: str,
    project_id: int,
    similarities: str,
    differences: str,
    db
):
    """Update YOUR existing comparison_configs table"""
    await db.execute(
        text("""
            INSERT INTO comparison_configs 
            (user_id, project_id, insights_similarities, insights_differences)
            VALUES (:user_id, :project_id, :similarities, :differences)
            ON CONFLICT (user_id, project_id) DO UPDATE SET
                insights_similarities = EXCLUDED.insights_similarities,
                insights_differences = EXCLUDED.insights_differences
        """),
        {
            'user_id': user_id,
            'project_id': project_id,
            'similarities': similarities,
            'differences': differences
        }
    )
    await db.commit()
```

---

## 🎯 Key Benefits of Using LlamaIndex

### 1. **Easy RAG Implementation**
- ✅ Built-in chunking and parsing
- ✅ Automatic embedding generation
- ✅ Query engine with filters
- ✅ Response synthesis

### 2. **Learning Opportunity**
- ✅ Well-documented framework
- ✅ Active community
- ✅ Many examples and tutorials
- ✅ Easy to experiment

### 3. **Flexibility**
- ✅ Use YOUR Nomic embeddings
- ✅ Use YOUR pgvector database
- ✅ Integrate with YOUR tables
- ✅ Customize as needed

### 4. **Advanced Features**
- ✅ Multi-document queries
- ✅ Metadata filtering
- ✅ Response synthesis
- ✅ Streaming responses

---

## 📊 Success Metrics

- ✅ Phase 1: Database tables created ✅
- ⏳ Phase 2: RAG engine with LlamaIndex + Nomic + Docling
- ⏳ Phase 3: Tools integrated with existing tables
- ⏳ Phase 4: Chat UI working
- ⏳ Phase 5: Tests passing
- ⏳ Phase 6: Production deployment

---

## 🚀 Next Steps

1. **Install LlamaIndex packages** (you're doing this now)
2. **Implement RAG engine** with LlamaIndex + Nomic + Docling
3. **Create agent tools** for database operations
4. **Build chat API** and frontend
5. **Test end-to-end** workflows
6. **Deploy** to production

**Ready to proceed to Phase 2!** 🎯
