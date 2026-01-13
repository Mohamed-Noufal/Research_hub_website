"""
Main Agent - Router and coordinator
Handles high-level user requests and delegates to specialized agents.
"""
from typing import Dict, List, Optional, Any
from app.agents.base import FlexibleAgent, Tool
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.tools import literature_tools, database_tools
import logging

logger = logging.getLogger(__name__)


class MainAgent:
    """
    Main coordinating agent with lightweight routing capabilities.
    
    Tools (5 core tools):
    1. list_projects - See all user's projects
    2. list_papers_in_library - See all saved papers
    3. get_project_by_name - Find specific project
    4. semantic_search - Quick search across papers
    5. delegate_to_literature_agent - Hand off complex tasks
    
    Routes requests like:
    - "What projects do I have?" → list_projects
    - "Tell me about my ML papers" → semantic_search
    - "Fill all tabs for Project X" → delegate_to_literature_agent
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        db,
        rag_engine: Optional[RAGEngine] = None,
        literature_agent = None  # LiteratureReviewAgent instance
    ):
        self.llm = llm_client
        self.db = db
        self.rag = rag_engine
        self.literature_agent = literature_agent
        self.context = {}
        
        # Create the agent with minimal tools
        self.agent = FlexibleAgent(
            name="MainAgent",
            llm_client=self.llm,
            tools=self._create_tools(),
            max_iterations=3  # Quick routing, not deep work
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create core routing tools"""
        tools = [
            Tool(
                name="list_projects",
                description="List all literature review projects for the user.",
                parameters={},
                function=lambda: literature_tools.list_projects(
                    user_id=self.context.get('user_id'),
                    db=self.db
                )
            ),
            Tool(
                name="list_papers_in_library",
                description="List all papers saved in user's library.",
                parameters={},
                function=lambda: literature_tools.list_papers_in_library(
                    user_id=self.context.get('user_id'),
                    db=self.db
                )
            ),
            Tool(
                name="get_project_by_name",
                description="Find a project by name. Use when user mentions a project like 'Test 1' or 'ML Review'.",
                parameters={"project_name": "str"},
                function=lambda project_name: database_tools.get_project_by_name(
                    project_name=project_name,
                    user_id=self.context.get('user_id'),
                    db=self.db
                )
            ),
            Tool(
                name="quick_search",
                description="Quick semantic search across papers. For simple questions about content.",
                parameters={"query": "str", "top_k": "int (default 5)"},
                function=self._quick_search
            ),
            Tool(
                name="delegate_to_literature_agent",
                description="""Delegate complex literature review tasks to the specialized Literature Review Agent.
                Use this for:
                - "Fill all tabs for project X"
                - "Extract methodology from all papers"
                - "Compare the papers in my project"
                - "Generate a summary of the literature"
                - Any task requiring deep analysis of papers""",
                parameters={
                    "task": "str - The task description to delegate",
                    "project_id": "int - The project ID to work on",
                    "mode": "str (optional) - 'methodology', 'findings', 'comparison', 'synthesis', 'summary', or 'full'"
                },
                function=self._delegate_to_literature_agent
            ),
        ]
        return tools
    
    async def _quick_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Simple search without heavy processing"""
        if not self.rag:
            return [{"error": "Search not available"}]
        
        result = await self.rag.query(
            query_text=query,
            top_k=top_k,
            return_sources=True
        )
        return result.get('source_nodes', [])[:top_k]
    
    async def _delegate_to_literature_agent(
        self,
        task: str,
        project_id: int,
        mode: str = "full"
    ) -> Dict:
        """Pass task to Literature Review Agent"""
        if not self.literature_agent:
            return {"error": "Literature agent not configured"}
        
        # Set context and mode
        self.literature_agent.set_context(
            user_id=self.context.get('user_id'),
            project_id=project_id
        )
        self.literature_agent.set_mode(mode)
        
        # Run the literature agent
        result = await self.literature_agent.process(task)
        return result
    
    def set_context(self, user_id: str, project_id: Optional[int] = None):
        """Set user context for all tools"""
        self.context = {
            'user_id': user_id,
            'project_id': project_id
        }
        self.agent.context = self.context
    
    async def process(self, message: str) -> Dict:
        """
        Process user message with routing logic.
        
        Returns:
            Dict with response and any delegated results
        """
        # Run agent loop
        result = await self.agent.run(message)
        return {
            "response": result,
            "agent": "main"
        }
    
    async def process_streaming(self, message: str):
        """
        Process with streaming for real-time updates.
        
        Yields:
            Status updates as the agent thinks
        """
        async for event in self.agent.run_streaming(message):
            yield event
