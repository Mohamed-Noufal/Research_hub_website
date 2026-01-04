"""
Orchestrator Agent - Main entry point for user requests
Classifies intent, plans execution, delegates to tools
"""
from typing import Dict, List, Optional, Any
from app.agents.base import FlexibleAgent, Tool
from app.core.llm_client import LLMClient
from app.core.rag_engine import RAGEngine
from app.tools import database_tools, rag_tools, pdf_tools
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
                    description="Extract structured methodology details from a specific paper.",
                    parameters={"paper_id": "int"},
                    function=lambda **kwargs: rag_tools.extract_methodology(
                        **kwargs,
                        rag_engine=self.rag,
                        llm_client=self.llm
                    )
                ),
                Tool(
                    name="get_paper_sections",
                    description="Retrieve full text of specific sections (e.g., 'Methodology', 'Results', 'Discussion') from papers. Use this for precise summaries and comparisons without noise.",
                    parameters={
                        "section_types": "list of str",
                        "paper_ids": "list of int (optional)"
                    },
                    function=lambda **kwargs: rag_tools.get_paper_sections(
                        section_types=kwargs.get('section_types'),
                        paper_ids=kwargs.get('paper_ids'),
                        project_id=self.agent.context.get('project_id') if self.agent.context else None,
                        scope=self.agent.context.get('scope', 'project') if self.agent.context else 'project',
                        selected_paper_ids=self.agent.context.get('selected_paper_ids') if self.agent.context else None,
                        rag_engine=self.rag
                    )
                ),
            ])
        
        # Background job tools (always available)
        tools.extend([
             Tool(
                name="parse_pdf",
                description="Parse a PDF file in the background. Handles extraction of text, tables, etc.",
                parameters={
                    "pdf_path": "str",
                    "paper_id": "int"
                },
                function=lambda **kwargs: pdf_tools.parse_pdf_background(
                    pdf_path=kwargs.get('pdf_path'),
                    paper_id=kwargs.get('paper_id'),
                    project_id=self.agent.context.get('project_id') if self.agent.context else None
                )
            ),
             Tool(
                name="check_job_status",
                description="Check the status of a background job (e.g., PDF parsing).",
                parameters={"job_id": "str"},
                function=lambda **kwargs: pdf_tools.check_job_status(
                    job_id=kwargs.get('job_id')
                )
            )
        ])
        
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
        selected_paper_ids: Optional[list] = None
    ):
        """
        Streaming version that yields agent thinking steps
        """
        # Add context to agent for tools to access
        self.agent.context = {
            'user_id': user_id,
            'project_id': project_id,
            'scope': scope,
            'selected_paper_ids': selected_paper_ids or []
        }
        
        # Stream agent execution
        async for event in self.agent.run_streaming(message):
            yield event
