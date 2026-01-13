"""
Literature Review Agent - Specialized agent for literature review tasks
Supports mode-based tool loading for focused, efficient operation.
"""
from typing import Dict, List, Optional, Any
from app.agents.base import FlexibleAgent, Tool
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.tools import literature_tools, database_tools, rag_tools, master_tools
import logging

logger = logging.getLogger(__name__)


# Mode-to-tools mapping
# NOTE: Synthesis tab is user-editable only, not automated by AI
MODE_TOOLS = {
    'methodology': ['get_paper_sections', 'extract_methodology', 'update_methodology', 'get_methodology'],
    'findings': ['get_paper_sections', 'extract_findings', 'update_findings', 'get_findings'],
    'comparison': ['get_project_papers', 'compare_papers', 'update_comparison', 'get_comparison'],
    # 'synthesis' removed - user-only tab
    'summary': ['get_methodology', 'get_findings', 'get_comparison', 'update_summary', 'get_summary'],
    'full': None,  # All tools
}


class LiteratureReviewAgent:
    """
    Specialized agent for literature review tasks.
    
    Modes:
    - 'methodology': Focus on methodology extraction/editing
    - 'findings': Focus on findings extraction/editing
    - 'comparison': Focus on comparing papers
    - 'synthesis': Focus on synthesis and research gaps
    - 'summary': Focus on generating/editing summary
    - 'full': All tools available (default)
    
    Each mode loads only relevant tools to:
    1. Reduce token usage in prompts
    2. Prevent tool hallucination
    3. Keep agent focused on the task
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        db,
        rag_engine: Optional[RAGEngine] = None
    ):
        self.llm = llm_client
        self.db = db
        self.rag = rag_engine
        self.context = {}
        self.current_mode = 'full'
        self.agent = None
        
        # Initialize with full tools
        self._rebuild_agent()
    
    def _rebuild_agent(self):
        """Rebuild agent with tools for current mode"""
        tools = self._create_tools_for_mode(self.current_mode)
        self.agent = FlexibleAgent(
            name=f"LiteratureReviewAgent[{self.current_mode}]",
            llm_client=self.llm,
            tools=tools,
            max_iterations=12  # Higher limit for deep multi-paper analysis
        )
        if self.context:
            self.agent.context = self.context
    
    def set_mode(self, mode: str):
        """
        Switch agent mode, reloading tools.
        
        Args:
            mode: One of 'methodology', 'findings', 'comparison', 'synthesis', 'summary', 'full'
        """
        if mode not in MODE_TOOLS:
            logger.warning(f"Unknown mode '{mode}', defaulting to 'full'")
            mode = 'full'
        
        if mode != self.current_mode:
            self.current_mode = mode
            self._rebuild_agent()
            logger.info(f"LiteratureReviewAgent mode switched to: {mode}")
    
    def set_context(self, user_id: str, project_id: Optional[int] = None):
        """Set user context"""
        self.context = {
            'user_id': user_id,
            'project_id': project_id
        }
        if self.agent:
            self.agent.context = self.context
    
    def _create_tools_for_mode(self, mode: str) -> List[Tool]:
        """Create tools based on current mode"""
        all_tools = self._create_all_tools()
        
        if mode == 'full' or MODE_TOOLS.get(mode) is None:
            return all_tools
        
        # Filter to mode-specific tools
        allowed_names = MODE_TOOLS[mode]
        return [t for t in all_tools if t.name in allowed_names]
    
    def _create_all_tools(self) -> List[Tool]:
        """Create all available tools"""
        tools = [
            # ==================== READ TOOLS ====================
            Tool(
                name="get_project_papers",
                description="Get all papers in the current project.",
                parameters={},
                function=lambda: database_tools.get_project_papers(
                    project_id=self.context.get('project_id'),
                    db=self.db
                )
            ),
            Tool(
                name="get_paper_sections",
                description="Get parsed sections from a paper (abstract, methodology, results).",
                parameters={
                    "paper_id": "int",
                    "section_types": "list of str (optional)"
                },
                function=lambda **kwargs: literature_tools.get_paper_sections(
                    **kwargs, db=self.db
                )
            ),
            Tool(
                name="get_methodology",
                description="Get saved methodology data for papers in project.",
                parameters={"paper_id": "int (optional)"},
                function=lambda paper_id=None: literature_tools.get_methodology(
                    project_id=self.context.get('project_id'),
                    paper_id=paper_id,
                    db=self.db
                )
            ),
            Tool(
                name="get_findings",
                description="Get saved findings for papers in project.",
                parameters={"paper_id": "int (optional)"},
                function=lambda paper_id=None: literature_tools.get_findings(
                    project_id=self.context.get('project_id'),
                    paper_id=paper_id,
                    db=self.db
                )
            ),
            Tool(
                name="get_comparison",
                description="Get comparison insights for the project.",
                parameters={},
                function=lambda: literature_tools.get_comparison(
                    project_id=self.context.get('project_id'),
                    db=self.db
                )
            ),
            # get_synthesis removed - synthesis is user-only tab
            Tool(
                name="get_summary",
                description="Get the literature review summary.",
                parameters={},
                function=lambda: literature_tools.get_summary(
                    project_id=self.context.get('project_id'),
                    db=self.db
                )
            ),
            
            # ==================== EXTRACT TOOLS ====================
            Tool(
                name="extract_methodology",
                description="Extract methodology details from a paper using RAG + LLM.",
                parameters={"paper_id": "int"},
                function=lambda paper_id: rag_tools.extract_methodology(
                    paper_id=paper_id,
                    project_id=self.context.get('project_id'),
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
            Tool(
                name="extract_findings",
                description="Extract key findings from a paper using RAG + LLM.",
                parameters={"paper_id": "int"},
                function=lambda paper_id: rag_tools.extract_findings(
                    paper_id=paper_id,
                    project_id=self.context.get('project_id'),
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
            Tool(
                name="compare_papers",
                description="Compare multiple papers on a specific aspect.",
                parameters={
                    "paper_ids": "list of int",
                    "aspect": "str (methodology, findings, etc.)"
                },
                function=lambda **kwargs: rag_tools.compare_papers(
                    **kwargs,
                    project_id=self.context.get('project_id'),
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
            Tool(
                name="find_research_gaps",
                description="Identify research gaps across all papers in project.",
                parameters={},
                function=lambda: rag_tools.find_research_gaps(
                    project_id=self.context.get('project_id'),
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
            
            # ==================== WRITE TOOLS ====================
            Tool(
                name="update_methodology",
                description="Save methodology data for a paper.",
                parameters={
                    "paper_id": "int",
                    "methodology_summary": "str",
                    "data_collection": "str (optional)",
                    "analysis_methods": "str (optional)",
                    "sample_size": "str (optional)"
                },
                function=lambda **kwargs: database_tools.update_methodology(
                    user_id=self.context.get('user_id'),
                    project_id=self.context.get('project_id'),
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="update_findings",
                description="Save findings for a paper.",
                parameters={
                    "paper_id": "int",
                    "key_finding": "str",
                    "limitations": "str (optional)"
                },
                function=lambda **kwargs: database_tools.update_findings(
                    user_id=self.context.get('user_id'),
                    project_id=self.context.get('project_id'),
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="update_comparison",
                description="Save comparison insights.",
                parameters={
                    "similarities": "str",
                    "differences": "str"
                },
                function=lambda **kwargs: database_tools.update_comparison(
                    user_id=self.context.get('user_id'),
                    project_id=self.context.get('project_id'),
                    **kwargs,
                    db=self.db
                )
            ),
            # update_synthesis removed - synthesis is user-only tab
            Tool(
                name="update_summary",
                description="Save the literature review summary.",
                parameters={
                    "summary_text": "str",
                    "key_insights": "list of str (optional)",
                    "research_gaps": "list of str (optional)",
                    "future_directions": "str (optional)"
                },
                function=lambda **kwargs: literature_tools.update_summary(
                    user_id=self.context.get('user_id'),
                    project_id=self.context.get('project_id'),
                    **kwargs,
                    db=self.db
                )
            ),
            
            # ==================== MASTER TOOL ====================
            Tool(
                name="fill_all_tabs",
                description="Fill methodology, findings, comparison, and summary tabs for all papers. Synthesis tab is user-only.",
                parameters={},
                function=lambda: master_tools.fill_all_tabs(
                    project_id=self.context.get('project_id'),
                    user_id=self.context.get('user_id'),
                    db=self.db,
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            ),
        ]
        return tools
    
    async def process(self, message: str) -> Dict:
        """
        Process user message in current mode.
        
        Returns:
            Dict with response and mode info
        """
        result = await self.agent.run(message)
        return {
            "response": result,
            "agent": "literature_review",
            "mode": self.current_mode
        }
    
    async def process_streaming(self, message: str):
        """
        Process with streaming for real-time updates.
        
        Yields:
            Status updates as the agent thinks
        """
        async for event in self.agent.run_streaming(message):
            yield event
