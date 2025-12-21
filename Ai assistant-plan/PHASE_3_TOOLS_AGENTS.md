# Phase 3: Tools & Sub-Agents

**Duration**: Week 5  
**Goal**: Build all tools and specialized sub-agents with LlamaIndex integration

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 2 is complete**:

```bash
# 1. Verify RAG engine exists
python -c "from backend.app.core.rag_engine import RAGEngine; print('✓ RAG engine ready')"
# Expected: "✓ RAG engine ready"

# 2. Verify LLM client exists
python -c "from backend.app.core.llm_client import LLMClient; print('✓ LLM client ready')"
# Expected: "✓ LLM client ready"

# 3. Verify base agent exists
python -c "from backend.app.agents.base import FlexibleAgent; print('✓ Base agent ready')"
# Expected: "✓ Base agent ready"

# 4. Test LlamaIndex query
python -c "
from backend.app.core.rag_engine import RAGEngine
import asyncio
rag = RAGEngine()
result = asyncio.run(rag.retrieve_only('test', top_k=1))
print('✓ LlamaIndex working')
"
# Expected: "✓ LlamaIndex working"
```

**✅ You should have**:
- RAG engine with LlamaIndex
- LLM client with Groq
- Flexible agent base class
- All Phase 2 components tested

**❌ If missing, complete Phase 2 first**

---

## ✅ Checklist

### Database Tools
- [ ] Create `backend/app/tools/database_tools.py`
- [ ] Implement `get_project_by_name`
- [ ] Implement `get_project_papers`
- [ ] Implement `update_comparison_tab`
- [ ] Implement `update_methodology_tab`
- [ ] Implement `update_findings_tab`

### RAG Tools
- [ ] Create `backend/app/tools/rag_tools.py`
- [ ] Implement `semantic_search`
- [ ] Implement `rerank_results`
- [ ] Implement `compress_context`

### Orchestrator Agent
- [ ] Create `backend/app/agents/orchestrator.py`
- [ ] Initialize with all tools
- [ ] Add sub-agent management
- [ ] Test full workflow

---

## 📋 Implementation

### 1. Database Tools

Create `backend/app/tools/database_tools.py`:

```python
from sqlalchemy import text
from typing import List, Dict, Optional
from backend.app.agents.base import Tool

async def get_project_by_name(user_id: str, project_name: str, db) -> Optional[Dict]:
    """Find literature review project by name"""
    result = await db.execute(
        text("""
            SELECT id, title, description
            FROM user_literature_reviews
            WHERE user_id = :user_id
              AND LOWER(title) LIKE LOWER(:pattern)
            ORDER BY similarity(title, :project_name) DESC
            LIMIT 1
        """),
        {
            'user_id': user_id,
            'pattern': f'%{project_name}%',
            'project_name': project_name
        }
    )
    
    project = result.fetchone()
    return dict(project._mapping) if project else None

async def get_project_papers(project_id: int, db) -> List[Dict]:
    """Get all papers in a project"""
    result = await db.execute(
        text("""
            SELECT p.id, p.title, p.authors, p.abstract, p.publication_date
            FROM papers p
            JOIN project_papers pp ON pp.paper_id = p.id
            WHERE pp.project_id = :project_id
            ORDER BY pp.added_at DESC
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
) -> Dict:
    """Update comparison insights"""
    await db.execute(
        text("""
            INSERT INTO comparison_configs (
                user_id, project_id,
                insights_similarities, insights_differences
            ) VALUES (
                :user_id, :project_id, :similarities, :differences
            )
            ON CONFLICT (user_id, project_id)
            DO UPDATE SET
                insights_similarities = EXCLUDED.insights_similarities,
                insights_differences = EXCLUDED.insights_differences,
                updated_at = NOW()
        """),
        {
            'user_id': user_id,
            'project_id': project_id,
            'similarities': similarities,
            'differences': differences
        }
    )
    
    await db.commit()
    return {'status': 'success', 'tab': 'comparison'}

# Create tool definitions
def create_database_tools(db):
    return [
        Tool(
            name="get_project_by_name",
            description="Find a literature review project by name. Use when user mentions a project.",
            parameters={
                "user_id": "string - user ID",
                "project_name": "string - project name to search"
            },
            function=lambda **kwargs: get_project_by_name(**kwargs, db=db)
        ),
        Tool(
            name="get_project_papers",
            description="Get all papers in a project. Use after finding project.",
            parameters={
                "project_id": "integer - project ID"
            },
            function=lambda **kwargs: get_project_papers(**kwargs, db=db)
        ),
        Tool(
            name="update_comparison_tab",
            description="Update comparison insights. Use after generating comparison.",
            parameters={
                "user_id": "string",
                "project_id": "integer",
                "similarities": "string - similarities text",
                "differences": "string - differences text"
            },
            function=lambda **kwargs: update_comparison_tab(**kwargs, db=db)
        )
    ]
```

### 2. RAG Tools

Create `backend/app/tools/rag_tools.py`:

```python
from backend.app.agents.base import Tool
from typing import List, Dict, Optional

async def semantic_search(
    query: str,
    user_id: str,
    project_id: Optional[int] = None,
    section_filter: Optional[List[str]] = None,
    top_k: int = 10,
    vector_store = None
) -> List[Dict]:
    """Semantic search across papers"""
    filters = {}
    if project_id:
        filters['project_id'] = project_id
    if section_filter:
        filters['section_types'] = section_filter
    
    results = await vector_store.similarity_search(
        query=query,
        user_id=user_id,
        filters=filters,
        top_k=top_k
    )
    
    return results

def create_rag_tools(vector_store):
    return [
        Tool(
            name="semantic_search",
            description="Search papers using semantic similarity. Use when you need to find relevant content.",
            parameters={
                "query": "string - what to search for",
                "user_id": "string - user ID",
                "project_id": "integer (optional) - limit to project",
                "section_filter": "list of strings (optional) - e.g. ['methodology', 'results']",
                "top_k": "integer - how many results (default 10)"
            },
            function=lambda **kwargs: semantic_search(**kwargs, vector_store=vector_store)
        )
    ]
```

### 3. Orchestrator Agent

Create `backend/app/agents/orchestrator.py`:

```python
from backend.app.agents.base import FlexibleAgent
from backend.app.tools.database_tools import create_database_tools
from backend.app.tools.rag_tools import create_rag_tools

class OrchestratorAgent(FlexibleAgent):
    """
    Main agent that coordinates all operations
    """
    
    def __init__(self, llm_client, db, vector_store):
        # Combine all tools
        all_tools = (
            create_database_tools(db) +
            create_rag_tools(vector_store)
        )
        
        super().__init__(
            name="Orchestrator",
            llm_client=llm_client,
            tools=all_tools
        )
        
        self.db = db
        self.vector_store = vector_store
    
    async def process_user_message(
        self,
        user_id: str,
        message: str,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        Process user message with full autonomy
        """
        # Add context
        self.memory.context['user_id'] = user_id
        if project_id:
            self.memory.context['project_id'] = project_id
        
        # Run agent
        result = await self.run(message)
        
        return result
```

---

## 🧪 Testing

Create `test_phase3.py`:

```python
import asyncio
from backend.app.agents.orchestrator import OrchestratorAgent
from backend.app.core.llm_client import LLMClient
from backend.app.core.vector_store import VectorStore

async def test_orchestrator():
    llm = LLMClient(db)
    vector_store = VectorStore(db)
    orchestrator = OrchestratorAgent(llm, db, vector_store)
    
    result = await orchestrator.process_user_message(
        user_id="test_user",
        message="Find my AI Healthcare project",
        project_id=None
    )
    
    print(f"✓ Orchestrator result: {result}")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
```

---

## 📝 Deliverables

- ✅ Database tools for all operations
- ✅ RAG tools for semantic search
- ✅ Orchestrator agent with all tools
- ✅ Tool integration tested

---

## ⏭️ Next Phase

Proceed to **Phase 4: API & Frontend Integration**.
