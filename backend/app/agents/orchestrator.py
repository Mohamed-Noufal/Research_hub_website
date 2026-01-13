"""
Orchestrator Agent - Main entry point for user requests
Classifies intent, plans execution, delegates to tools
"""
from typing import Dict, List, Optional, Any
from app.agents.base import FlexibleAgent, Tool
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.tools import database_tools, rag_tools, pdf_tools, literature_tools, master_tools
import json

class OrchestratorAgent:
    """
    Main orchestrator agent
    Handles user requests and delegates to appropriate tools
    """
    
    
    def __init__(self, llm_client: LLMClient, db, rag_engine: Optional[RAGEngine] = None):
        self.llm = llm_client
        self.db = db
        self.rag = rag_engine
        
        # Active context - persists across conversation turns to avoid redundant lookups
        self.active_context = {
            'current_project': None,  # {'id': int, 'name': str}
            'current_paper': None,    # {'id': int, 'title': str}
            'resolved_papers': []     # List of {'id': int, 'title': str} seen in conversation
        }
        
        # Initialize tools (only include RAG tools if RAG is available)
        self.tools = self._create_tools()
        
        # Create flexible agent
        self.agent = FlexibleAgent(
            name="LiteratureReviewAssistant",
            llm_client=llm_client,
            tools=self.tools
        )
    
    def _create_tools(self) -> List[Tool]:
        """Create all available tools"""
        tools = [
            # Database tools (always available)
            Tool(
                name="get_project_by_name",
                description="Find a project by name (supports fuzzy matching). Use this when user mentions a project name like 'Test 1' or 'Literature Review'.",
                parameters={
                    "project_name": "str",
                    "user_id": "str"
                },
                function=lambda **kwargs: database_tools.get_project_by_name(
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="get_project_papers",
                description="Get all papers in a project. Useful to see what papers are available for comparison or context.",
                parameters={"project_id": "int"},
                function=lambda project_id: database_tools.get_project_papers(
                    project_id=project_id,
                    db=self.db
                )
            ),
            Tool(
                name="update_comparison",
                description="Update comparison insights for a project in the database. Use this after generating comparison text.",
                parameters={
                    "user_id": "str",
                    "project_id": "int",
                    "similarities": "str",
                    "differences": "str"
                },
                function=lambda **kwargs: database_tools.update_comparison(
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="update_findings",
                description="Update findings for a specific paper. Use this after extracting findings.",
                parameters={
                    "user_id": "str",
                    "project_id": "int",
                    "paper_id": "int",
                    "key_finding": "str",
                    "limitations": "str"
                },
                function=lambda **kwargs: database_tools.update_findings(
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="update_methodology",
                description="Update methodology analysis for a specific paper in a project. Use after extracting methodology details.",
                parameters={
                    "user_id": "str",
                    "project_id": "int",
                    "paper_id": "int",
                    "methodology_summary": "str (optional)",
                    "data_collection": "str (optional)",
                    "analysis_methods": "str (optional)",
                    "sample_size": "str (optional)"
                },
                function=lambda **kwargs: database_tools.update_methodology(
                    **kwargs,
                    db=self.db
                )
            ),
            Tool(
                name="update_synthesis",
                description="Update synthesis data for a project including synthesis text, key themes, and research gaps.",
                parameters={
                    "user_id": "str",
                    "project_id": "int",
                    "synthesis_text": "str (optional)",
                    "key_themes": "list of str (optional)",
                    "research_gaps": "list of str (optional)"
                },
                function=lambda **kwargs: database_tools.update_synthesis(
                    **kwargs,
                    db=self.db
                )
            ),
            
            # ==================== NEW LITERATURE REVIEW TOOLS ====================
            
            # READ: Paper Content
            Tool(
                name="get_paper_sections",
                description="Get parsed sections from a paper's PDF (abstract, methodology, results, etc.). Use this to read actual paper content.",
                parameters={
                    "paper_id": "int",
                    "section_types": "list of str (optional) - e.g. ['methodology', 'results']"
                },
                function=lambda **kwargs: literature_tools.get_paper_sections(
                    **kwargs, db=self.db
                )
            ),
            Tool(
                name="get_paper_tables",
                description="Get all tables extracted from a paper's PDF.",
                parameters={"paper_id": "int"},
                function=lambda paper_id: literature_tools.get_paper_tables(
                    paper_id=paper_id, db=self.db
                )
            ),
            Tool(
                name="get_paper_details",
                description="Get paper metadata (title, abstract, authors, etc.).",
                parameters={"paper_id": "int"},
                function=lambda paper_id: literature_tools.get_paper_details(
                    paper_id=paper_id, db=self.db
                )
            ),
            
            # READ: Literature Review Tabs
            Tool(
                name="get_methodology",
                description="Get saved methodology analysis from a project. Shows sample size, data collection, analysis methods.",
                parameters={
                    "project_id": "int",
                    "paper_id": "int (optional) - if not provided, returns all papers' methodology"
                },
                function=lambda **kwargs: literature_tools.get_methodology(
                    **kwargs, db=self.db
                )
            ),
            Tool(
                name="get_findings",
                description="Get saved findings/key results from papers in a project.",
                parameters={
                    "project_id": "int",
                    "paper_id": "int (optional)"
                },
                function=lambda **kwargs: literature_tools.get_findings(
                    **kwargs, db=self.db
                )
            ),
            Tool(
                name="get_comparison",
                description="Get comparison insights (similarities/differences) for a project.",
                parameters={"project_id": "int"},
                function=lambda project_id: literature_tools.get_comparison(
                    project_id=project_id, db=self.db
                )
            ),
            Tool(
                name="get_synthesis",
                description="Get synthesis data (themes, gaps) for a project.",
                parameters={"project_id": "int"},
                function=lambda project_id: literature_tools.get_synthesis(
                    project_id=project_id, db=self.db
                )
            ),
            Tool(
                name="get_summary",
                description="Get the literature review summary for a project.",
                parameters={"project_id": "int"},
                function=lambda project_id: literature_tools.get_summary(
                    project_id=project_id, db=self.db
                )
            ),
            
            # READ: Lists
            Tool(
                name="list_papers_in_library",
                description="List papers in the current knowledge base scope. Respects user's scope selection (library, project, or specific papers).",
                parameters={},
                function=lambda: literature_tools.list_papers_in_library(
                    user_id=self.agent.context.get('user_id') if self.agent.context else None,
                    db=self.db,
                    scope=self.agent.context.get('scope', 'library') if self.agent.context else 'library',
                    selected_paper_ids=self.agent.context.get('selected_paper_ids') if self.agent.context else None
                )
            ),
            Tool(
                name="list_projects",
                description="List all literature review projects for the user.",
                parameters={},
                function=lambda: literature_tools.list_projects(
                    user_id=self.agent.context.get('user_id') if self.agent.context else None,
                    db=self.db
                )
            ),
            
            # WRITE: Summary
            Tool(
                name="update_summary",
                description="Save or update the literature review summary for a project. Use after generating a summary.",
                parameters={
                    "project_id": "int",
                    "summary_text": "str (optional)",
                    "key_insights": "list of str (optional)",
                    "methodology_overview": "str (optional)",
                    "main_findings": "str (optional)",
                    "research_gaps": "list of str (optional)",
                    "future_directions": "str (optional)"
                },
                function=lambda **kwargs: literature_tools.update_summary(
                    **kwargs,
                    user_id=self.agent.context.get('user_id') if self.agent.context else None,
                    db=self.db
                )
            ),
        ]
        
        # Add RAG tools only if RAG engine is available
        if self.rag:
            tools.extend([
                Tool(
                    name="semantic_search",
                    description="Search papers semantically for specific topics, concepts, or keywords.",
                    parameters={
                        "query": "str",
                        "project_id": "int (optional)",
                        "top_k": "int (default 10)"
                    },
                    function=lambda **kwargs: rag_tools.semantic_search(
                        query=kwargs.get('query'),
                        project_id=kwargs.get('project_id'),
                        top_k=kwargs.get('top_k', 10),
                        scope=self.agent.context.get('scope', 'project') if self.agent.context else 'project',
                        selected_paper_ids=self.agent.context.get('selected_paper_ids') if self.agent.context else None,
                        rag_engine=self.rag
                    )
                ),
                Tool(
                    name="compare_papers",
                    description="Compare a list of papers on a specific aspect (e.g., methodology, findings, datasets). Returns similarities and differences.",
                    parameters={
                        "paper_ids": "list of int",
                        "aspect": "str (methodology, findings, etc.)"
                    },
                    function=lambda **kwargs: rag_tools.compare_papers(
                        **kwargs,
                        rag_engine=self.rag,
                        llm_client=self.llm,
                        project_id=self.agent.context.get('project_id') if self.agent.context else None
                    )
                ),
                Tool(
                    name="extract_methodology",
                    description="Extract structured methodology details from a specific paper. Returns validated JSON with methodology_summary, data_collection, analysis_methods, sample_size.",
                    parameters={"paper_id": "int"},
                    function=lambda **kwargs: rag_tools.extract_methodology(
                        **kwargs,
                        rag_engine=self.rag,
                        llm_client=self.llm
                    )
                ),
                Tool(
                    name="extract_findings",
                    description="Extract structured findings from a specific paper. Returns validated JSON with key_finding, limitations, evidence_level.",
                    parameters={"paper_id": "int"},
                    function=lambda **kwargs: rag_tools.extract_findings(
                        **kwargs,
                        rag_engine=self.rag,
                        llm_client=self.llm
                    )
                ),
                Tool(
                    name="search_paper_sections",
                    description="Semantic search within specific sections (e.g., 'Methodology', 'Results') across papers. Returns relevant chunks by meaning. For exact section text, use get_paper_sections instead.",
                    parameters={
                        "section_types": "list of str",
                        "paper_ids": "list of int (optional)"
                    },
                    function=lambda **kwargs: rag_tools.search_paper_sections(
                        section_types=kwargs.get('section_types'),
                        paper_ids=kwargs.get('paper_ids'),
                        project_id=self.agent.context.get('project_id') if self.agent.context else None,
                        scope=self.agent.context.get('scope', 'project') if self.agent.context else 'project',
                        selected_paper_ids=self.agent.context.get('selected_paper_ids') if self.agent.context else None,
                        rag_engine=self.rag
                    )
                ),
                Tool(
                    name="find_research_gaps",
                    description="Identify research gaps and future directions across papers in a project. Useful for synthesis and summary tabs.",
                    parameters={"project_id": "int"},
                    function=lambda **kwargs: rag_tools.find_research_gaps(
                        project_id=kwargs.get('project_id'),
                        rag_engine=self.rag,
                        llm_client=self.llm
                    )
                ),
            ])
        
        # Master tool for batch operations
        tools.append(
            Tool(
                name="fill_all_tabs",
                description="Fill ALL literature review tabs (methodology, findings, comparison, synthesis, summary) for all papers in a project. Use this when user asks to 'fill all tabs', 'complete the review', or 'extract everything'.",
                parameters={"project_id": "int"},
                function=lambda **kwargs: master_tools.fill_all_tabs(
                    project_id=kwargs.get('project_id'),
                    user_id=self.agent.context.get('user_id') if self.agent.context else None,
                    db=self.db,
                    rag_engine=self.rag,
                    llm_client=self.llm
                )
            )
        )
        
        return tools
    
    async def process_user_message(
        self,
        user_id: str,
        message: str,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        Main entry point for request processing
        
        Args:
            user_id: User ID
            message: User message
            project_id: Optional project ID for context
        
        Returns:
            Response dict
        """
        # Add context to agent for tools to access
        self.agent.context = {
            'user_id': user_id,
            'project_id': project_id
        }
        
        # Run agent
        # The agent will cycle through Think -> Act -> Observe
        result = await self.agent.run(message)
        
        return result
    
    async def process_user_message_streaming(
        self,
        user_id: str,
        message: str,
        project_id: Optional[int] = None,
        scope: str = 'project',
        selected_paper_ids: Optional[list] = None,
        chat_history: Optional[list] = None,
        model_id: Optional[str] = None  # NEW: Model selection from frontend
    ):
        """
        Streaming version that yields agent thinking steps
        """
        # Add context to agent for tools to access
        self.agent.context = {
            'user_id': user_id,
            'project_id': project_id,
            'scope': scope,
            'selected_paper_ids': selected_paper_ids or [],
            'model_id': model_id,
            'active_context': self.active_context  # Inject active context for prompt
        }
        
        # Stream agent execution
        async for event in self.agent.run_streaming(message, chat_history=chat_history):
            yield event
