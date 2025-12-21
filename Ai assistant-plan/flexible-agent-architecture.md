# Flexible AI Agent Architecture with Tools, Memory & Sub-Agents

## 🧠 Dynamic Agent System (Not Static Flow)

### Core Concept: Agent Decides Its Own Path

```python
# Instead of hardcoded flow:
# step1 → step2 → step3 → step4

# Agent dynamically decides:
USER: "Generate methodology for AI Healthcare project"

AGENT THINKS:
  "I need to find the project first"
  → Uses tool: get_project_by_name
  
  "Now I need the papers"
  → Uses tool: get_project_papers
  
  "Are these papers processed?"
  → Uses tool: check_embeddings
  
  "Paper 3 isn't processed, I should process it"
  → Delegates to: PaperAgent
  
  "Now I can query for methodology"
  → Uses tool: rag_query
  
  "I have enough context, let me generate"
  → Uses tool: generate_content
  
  "Should I update the database?"
  → Uses tool: update_methodology_tab
  
  "Done!"
```

---

## 🏗️ Architecture: ReAct Pattern with Tools

### 1. Base Agent with Tool Selection

```python
# backend/app/agents/base.py

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json

class Tool(BaseModel):
    """Tool definition"""
    name: str
    description: str
    parameters: Dict[str, Any]
    function: callable

class AgentMemory(BaseModel):
    """Conversation memory"""
    messages: List[Dict[str, str]] = []
    context: Dict[str, Any] = {}
    tool_history: List[Dict] = []

class FlexibleAgent:
    """
    Autonomous agent that decides its own actions
    Uses ReAct (Reasoning + Acting) pattern
    """
    
    def __init__(self, name: str, llm_client, tools: List[Tool]):
        self.name = name
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.memory = AgentMemory()
        self.sub_agents = {}  # Can delegate to other agents
    
    async def run(self, task: str, max_iterations: int = 10):
        """
        Main agent loop - decides actions dynamically
        """
        self.memory.messages.append({
            "role": "user",
            "content": task
        })
        
        for iteration in range(max_iterations):
            # STEP 1: Agent thinks about what to do next
            thought = await self._think()
            
            # STEP 2: Agent decides action
            action = await self._decide_action(thought)
            
            if action['type'] == 'finish':
                # Agent decided it's done
                return action['result']
            
            elif action['type'] == 'use_tool':
                # Agent wants to use a tool
                result = await self._execute_tool(
                    action['tool_name'],
                    action['parameters']
                )
                
                # Add result to memory
                self.memory.messages.append({
                    "role": "assistant",
                    "content": f"Used {action['tool_name']}: {result}"
                })
            
            elif action['type'] == 'delegate':
                # Agent wants to delegate to sub-agent
                result = await self._delegate_to_agent(
                    action['agent_name'],
                    action['task']
                )
                
                self.memory.messages.append({
                    "role": "assistant",
                    "content": f"Delegated to {action['agent_name']}: {result}"
                })
            
            elif action['type'] == 'ask_user':
                # Agent needs clarification
                return {
                    'status': 'needs_input',
                    'question': action['question']
                }
        
        return {
            'status': 'max_iterations',
            'message': 'Reached maximum iterations'
        }
    
    async def _think(self) -> str:
        """
        Agent reasons about current state and next action
        """
        prompt = f"""
        You are {self.name}, an AI assistant helping with literature reviews.
        
        Available tools:
        {self._format_tools()}
        
        Available sub-agents:
        {self._format_sub_agents()}
        
        Conversation history:
        {self._format_memory()}
        
        Current context:
        {json.dumps(self.memory.context, indent=2)}
        
        Think step by step:
        1. What is the current goal?
        2. What information do I have?
        3. What information do I need?
        4. What should I do next?
        
        Respond with your reasoning.
        """
        
        thought = await self.llm.complete(prompt)
        return thought
    
    async def _decide_action(self, thought: str) -> Dict:
        """
        Based on reasoning, decide next action
        """
        prompt = f"""
        Based on this reasoning:
        {thought}
        
        Available tools:
        {self._format_tools()}
        
        Available sub-agents:
        {self._format_sub_agents()}
        
        Decide your next action. Respond with JSON:
        
        Option 1 - Use a tool:
        {{
            "type": "use_tool",
            "tool_name": "tool_name",
            "parameters": {{...}},
            "reasoning": "why this tool"
        }}
        
        Option 2 - Delegate to sub-agent:
        {{
            "type": "delegate",
            "agent_name": "agent_name",
            "task": "specific task",
            "reasoning": "why delegate"
        }}
        
        Option 3 - Finish (task complete):
        {{
            "type": "finish",
            "result": "final answer",
            "reasoning": "why done"
        }}
        
        Option 4 - Ask user for clarification:
        {{
            "type": "ask_user",
            "question": "what to ask",
            "reasoning": "why need input"
        }}
        """
        
        response = await self.llm.complete(prompt)
        action = json.loads(response)
        
        # Log decision
        self.memory.tool_history.append({
            'thought': thought,
            'action': action
        })
        
        return action
    
    async def _execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Execute a tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        result = await tool.function(**parameters)
        
        # Update context with result
        self.memory.context[f"last_{tool_name}_result"] = result
        
        return result
    
    async def _delegate_to_agent(self, agent_name: str, task: str) -> Any:
        """Delegate to sub-agent"""
        if agent_name not in self.sub_agents:
            raise ValueError(f"Sub-agent {agent_name} not found")
        
        sub_agent = self.sub_agents[agent_name]
        result = await sub_agent.run(task)
        
        return result
    
    def _format_tools(self) -> str:
        """Format tools for prompt"""
        return "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])
    
    def _format_sub_agents(self) -> str:
        """Format sub-agents for prompt"""
        return "\n".join([
            f"- {name}: {agent.description}"
            for name, agent in self.sub_agents.items()
        ])
    
    def _format_memory(self) -> str:
        """Format conversation memory"""
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.memory.messages[-5:]  # Last 5 messages
        ])
```

---

## 🔧 Tool Definitions

### Database Tools

```python
# backend/app/tools/database_tools.py

async def get_project_by_name(user_id: str, project_name: str, db) -> Dict:
    """Find literature review project by name"""
    result = await db.execute(
        text("""
            SELECT id, title, description
            FROM user_literature_reviews
            WHERE user_id = :user_id
              AND LOWER(title) LIKE LOWER(:pattern)
            LIMIT 1
        """),
        {'user_id': user_id, 'pattern': f'%{project_name}%'}
    )
    
    project = result.fetchone()
    return dict(project) if project else None

async def get_project_papers(project_id: int, db) -> List[Dict]:
    """Get all papers in a project"""
    result = await db.execute(
        text("""
            SELECT p.id, p.title, p.authors, p.abstract
            FROM papers p
            JOIN project_papers pp ON pp.paper_id = p.id
            WHERE pp.project_id = :project_id
        """),
        {'project_id': project_id}
    )
    
    return [dict(row) for row in result.fetchall()]

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
            UPDATE comparison_configs
            SET insights_similarities = :similarities,
                insights_differences = :differences,
                updated_at = NOW()
            WHERE user_id = :user_id AND project_id = :project_id
        """),
        {
            'user_id': user_id,
            'project_id': project_id,
            'similarities': similarities,
            'differences': differences
        }
    )
    
    await db.commit()
    return {'status': 'success'}

# Create tool objects
DATABASE_TOOLS = [
    Tool(
        name="get_project_by_name",
        description="Find a literature review project by name. Use when user mentions a project.",
        parameters={
            "user_id": "string",
            "project_name": "string"
        },
        function=get_project_by_name
    ),
    Tool(
        name="get_project_papers",
        description="Get all papers in a project. Use after finding project.",
        parameters={
            "project_id": "integer"
        },
        function=get_project_papers
    ),
    Tool(
        name="update_comparison_tab",
        description="Update comparison insights in database. Use after generating comparison.",
        parameters={
            "user_id": "string",
            "project_id": "integer",
            "similarities": "string",
            "differences": "string"
        },
        function=update_comparison_tab
    )
]
```

### RAG Tools

```python
# backend/app/tools/rag_tools.py

async def semantic_search(
    query: str,
    user_id: str,
    project_id: Optional[int] = None,
    section_filter: Optional[List[str]] = None,
    top_k: int = 10,
    vector_store = None
) -> List[Dict]:
    """
    Semantic search across papers
    """
    results = await vector_store.similarity_search(
        query=query,
        user_id=user_id,
        filters={
            'project_id': project_id,
            'section_types': section_filter
        },
        top_k=top_k
    )
    
    return [
        {
            'text': r.text,
            'paper_title': r.paper_title,
            'section': r.section_type,
            'similarity': r.similarity
        }
        for r in results
    ]

RAG_TOOLS = [
    Tool(
        name="semantic_search",
        description="Search papers using semantic similarity. Use when you need to find relevant content.",
        parameters={
            "query": "string - what to search for",
            "user_id": "string",
            "project_id": "integer (optional)",
            "section_filter": "list of strings (optional) - e.g. ['methodology', 'results']",
            "top_k": "integer - how many results (default 10)"
        },
        function=semantic_search
    )
]
```

---

## 🤖 Orchestrator Agent with Sub-Agents

```python
# backend/app/agents/orchestrator.py

class OrchestratorAgent(FlexibleAgent):
    """
    Main agent that coordinates everything
    Has access to all tools and can delegate to sub-agents
    """
    
    def __init__(self, llm_client, db, vector_store):
        # Initialize with all tools
        all_tools = DATABASE_TOOLS + RAG_TOOLS + WRITING_TOOLS
        
        super().__init__(
            name="Orchestrator",
            llm_client=llm_client,
            tools=all_tools
        )
        
        # Initialize sub-agents
        self.sub_agents = {
            'paper_processor': PaperProcessorAgent(llm_client, db),
            'content_generator': ContentGeneratorAgent(llm_client),
            'data_updater': DataUpdaterAgent(db)
        }
    
    async def run(self, user_message: str):
        """
        Process user message with full autonomy
        """
        # Add user message to memory
        self.memory.messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Agent decides its own path
        result = await super().run(user_message)
        
        return result

# Example usage:
orchestrator = OrchestratorAgent(llm_client, db, vector_store)

# Agent autonomously decides what to do
result = await orchestrator.run(
    "Generate methodology section for AI Healthcare project"
)

# Agent's internal decision process:
# 1. "I need to find the project" → use get_project_by_name tool
# 2. "I found it, now get papers" → use get_project_papers tool
# 3. "I need methodology content" → use semantic_search tool with section_filter=['methodology']
# 4. "I have content, generate section" → delegate to content_generator sub-agent
# 5. "Section generated, update database" → delegate to data_updater sub-agent
# 6. "Done!" → return result
```

---

## 💾 Persistent Memory

```python
# backend/app/core/agent_memory.py

class PersistentMemory:
    """
    Stores conversation history and context in database
    """
    
    def __init__(self, db, conversation_id: str):
        self.db = db
        self.conversation_id = conversation_id
    
    async def add_message(self, role: str, content: str):
        """Add message to memory"""
        await self.db.execute(
            text("""
                INSERT INTO agent_messages (
                    conversation_id, role, content
                ) VALUES (:conv_id, :role, :content)
            """),
            {
                'conv_id': self.conversation_id,
                'role': role,
                'content': content
            }
        )
        await self.db.commit()
    
    async def get_history(self, last_n: int = 10) -> List[Dict]:
        """Get conversation history"""
        result = await self.db.execute(
            text("""
                SELECT role, content, created_at
                FROM agent_messages
                WHERE conversation_id = :conv_id
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {'conv_id': self.conversation_id, 'limit': last_n}
        )
        
        return [dict(row) for row in reversed(result.fetchall())]
    
    async def update_context(self, key: str, value: Any):
        """Update conversation context"""
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
```

---

## 🎯 Example: Flexible Agent in Action

```python
# User message
USER: "Compare methodologies in my AI Healthcare project"

# Agent's autonomous decision process:

ITERATION 1:
  Thought: "I need to find the project first"
  Action: use_tool(get_project_by_name, {"project_name": "AI Healthcare"})
  Result: {"project_id": 5, "title": "AI in Healthcare Review"}
  Memory updated: project_id = 5

ITERATION 2:
  Thought: "Now I need the papers in this project"
  Action: use_tool(get_project_papers, {"project_id": 5})
  Result: [paper1, paper2, paper3, paper4]
  Memory updated: papers = [...]

ITERATION 3:
  Thought: "I need methodology content from these papers"
  Action: use_tool(semantic_search, {
    "query": "methodology approach techniques",
    "project_id": 5,
    "section_filter": ["methodology"],
    "top_k": 20
  })
  Result: [20 relevant chunks]
  Memory updated: methodology_chunks = [...]

ITERATION 4:
  Thought: "I have enough content, I should generate comparison"
  Action: delegate(content_generator, "Generate methodology comparison from chunks")
  Result: {
    "similarities": "...",
    "differences": "...",
    "table": "..."
  }
  Memory updated: comparison_result = {...}

ITERATION 5:
  Thought: "Comparison generated, should I update the database?"
  Action: use_tool(update_comparison_tab, {
    "user_id": "123",
    "project_id": 5,
    "similarities": "...",
    "differences": "..."
  })
  Result: {"status": "success"}

ITERATION 6:
  Thought: "Task complete, I should finish"
  Action: finish({
    "message": "✓ Generated methodology comparison for AI Healthcare project",
    "details": {...}
  })
```

---

## ✅ This is Truly Flexible Because:

1. **Agent decides its own path** - Not hardcoded
2. **Can use any tool** - Chooses based on situation
3. **Can delegate to sub-agents** - When specialized help needed
4. **Has memory** - Remembers conversation and context
5. **Can ask for clarification** - If uncertain
6. **Adaptive** - Handles unexpected situations

**This is production-ready autonomous AI!** 🚀
