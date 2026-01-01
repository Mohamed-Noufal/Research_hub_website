"""
RAG Engine using LlamaIndex with YOUR existing Nomic embeddings
Integrates with Docling for academic PDF parsing
"""
from llama_index.core import VectorStoreIndex, Settings, StorageContext, Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, MetadataFilter, FilterOperator
from sqlalchemy import make_url
from docling.document_converter import DocumentConverter
import os
import logging

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class RAGEngine:
    """
    LlamaIndex-powered RAG engine using YOUR Nomic embeddings (768 dims)
    Parses PDFs with Docling to extract equations, tables, images
    """
    
    def __init__(self, db_url: str = None):
        # Database connection
        db_url = db_url or settings.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is not set")
            
        url = make_url(db_url)
        
        # Use YOUR existing Nomic model (same as EnhancedVectorService)
        logger.info("🔧 Initializing Nomic embeddings (nomic-ai/nomic-embed-text-v1.5)...")
        # Initialize embedding model - ensure trust_remote_code is True for Nomic
        self.embed_model = HuggingFaceEmbedding(
            model_name="nomic-ai/nomic-embed-text-v1.5",
            trust_remote_code=True
        )
        
        # Initialize Groq LLM
        api_key = settings.GROQ_API_KEY
        if not api_key:
             logger.warning("⚠️ GROQ_API_KEY not found. LLM functionality will fail if initialized.")

        logger.info("🔧 Initializing Groq LLM (llama-3.3-70b-versatile)...")
        self.llm = Groq(
            model="llama-3.3-70b-versatile",
            api_key=api_key
        )
        
        # Configure LlamaIndex global settings
        Settings.embed_model = self.embed_model
        Settings.llm = self.llm
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        # Initialize pgvector store (connects to YOUR paper_chunks table)
        logger.info("🔧 Connecting to pgvector (paper_chunks table)...")
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
        
        logger.info("✅ RAG Engine initialized successfully!")
    
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
        logger.info(f"📄 Processing paper {paper_id} with Docling...")
        
        if not os.path.exists(pdf_path):
             raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Parse PDF with Docling (extracts equations, images, tables)
        # Note: DocumentConverter can be slow, best run in background (Phase 3 addresses this)
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
        # Iterate over items to capture hierarchy
        current_section = "Introduction" # Default start
        
        for element in result.document.iterate_items():
            stats['total_elements'] += 1
            
            # 1. Handle Section Headers (Update Context)
            if hasattr(element, 'label') and element.label == 'section_header':
                current_section = element.text.strip()
                continue # Don't chunk headers themselves as separate nodes usually, or keep them?
                # Actually, keeping them helps context. Let's keep them but update state first.

            # 2. Handle Tables (Export to Markdown)
            if hasattr(element, 'has_table') and element.has_table:
                stats['tables'] += 1
                # structured_text = element.export_to_markdown() 
                # Note: Check if export_to_markdown exists on this element version
                # If not available, fallback to text.
                if hasattr(element, 'export_to_markdown'):
                    text_content = element.export_to_markdown()
                else:
                    text_content = element.text
            
            # 3. Handle Equations
            elif hasattr(element, 'has_math') and element.has_math:
                stats['equations'] += 1
                text_content = element.text # Often LaTeX-like
                
            # 4. Handle Images
            elif hasattr(element, 'has_figure') and element.has_figure:
                stats['images'] += 1
                text_content = f"[Image: {element.text}]" # Placeholder for now
                
            # 5. Regular Text
            else:
                text_content = element.text

            # Skip empty
            if not text_content or not text_content.strip():
                continue
                
            # Create Document with Section Metadata
            doc = Document(
                text=text_content,
                metadata={
                    "paper_id": paper_id,
                    "section_type": current_section, # CRITICAL: Tag with current header
                    "element_type": element.label if hasattr(element, 'label') else "unknown",
                    "has_equation": getattr(element, 'has_math', False),
                    "has_table": getattr(element, 'has_table', False),
                    "has_image": getattr(element, 'has_figure', False),
                    **(metadata or {})
                }
            )
            documents.append(doc)
        
        logger.info(f"  📊 Extracted {stats['total_elements']} elements:")
        logger.info(f"     - {stats['equations']} equations")
        logger.info(f"     - {stats['tables']} tables")
        logger.info(f"     - {stats['images']} images")
        
        # Parse into nodes (chunks) with LlamaIndex
        parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        nodes = parser.get_nodes_from_documents(documents)
        stats['text_chunks'] = len(nodes)
        
        logger.info(f"  ✂️  Created {len(nodes)} text chunks")
        
        # Insert into vector store (uses YOUR Nomic embeddings automatically!)
        logger.info(f"  🧠 Generating embeddings with YOUR Nomic model...")
        self.index.insert_nodes(nodes)
        
        logger.info(f"  ✅ Successfully ingested paper {paper_id}")
        
        return stats
    
    async def query(
        self,
        query_text: str,
        project_id: int = None,
        section_filter: list = None,
        paper_ids: list = None,
        top_k: int = 10,
        return_sources: bool = True
    ) -> dict:
        """
        Query using LlamaIndex with filters
        
        Args:
            query_text: Natural language query
            project_id: Filter by YOUR project_id
            section_filter: Filter by section types (e.g., ['methodology', 'results'])
            paper_ids: Filter by specific paper IDs
            top_k: Number of results
            return_sources: Include source chunks
        
        Returns:
            dict with answer and source nodes
        """
        logger.info(f"🔍 Querying: '{query_text}'")
        
        # Build metadata filters
        filters = []
        if project_id:
            filters.append(MetadataFilter(key="project_id", value=project_id))
            logger.info(f"  📁 Filtering by project_id={project_id}")
            
        if paper_ids:
            filters.append(MetadataFilter(key="paper_id", value=paper_ids, operator=FilterOperator.IN))
            logger.info(f"  📄 Filtering by paper_ids={paper_ids}")
        
        if section_filter:
            # Use IN operator for multiple sections (OR logic)
            filters.append(MetadataFilter(key="section_type", value=section_filter, operator=FilterOperator.IN))
            logger.info(f"  📑 Filtering by sections: {section_filter}")
        
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        # Create query engine
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            filters=metadata_filters
        )
        
        # Execute query (uses YOUR Nomic embeddings!)
        response = query_engine.query(query_text)
        
        result = {
            'answer': str(response),
            'source_nodes': []
        }
        
        if return_sources:
            if hasattr(response, 'source_nodes'):
                result['source_nodes'] = [
                    {
                        'text': node.node.text,
                        'score': node.score,
                        'metadata': node.node.metadata,
                        'paper_id': node.node.metadata.get('paper_id'),
                        'section_type': node.node.metadata.get('section_type'),
                    }
                    for node in response.source_nodes
                ]
        
        return result
    
    async def retrieve_only(
        self,
        query_text: str,
        project_id: int = None,
        paper_ids: list = None,
        section_filter: list = None,
        top_k: int = 10
    ) -> list:
        """
        Retrieve chunks without LLM generation (faster, cheaper)
        """
        # Build vector retriever
        filters = []
        if project_id:
            filters.append(MetadataFilter(key="project_id", value=project_id))
            
        if paper_ids:
            filters.append(MetadataFilter(key="paper_id", value=paper_ids, operator=FilterOperator.IN))

        if section_filter:
            filters.append(MetadataFilter(key="section_type", value=section_filter, operator=FilterOperator.IN))
            
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        retriever = self.index.as_retriever(
            similarity_top_k=top_k, 
            filters=metadata_filters
        )
        nodes = await retriever.aretrieve(query_text)
        
        return [
            {
                'text': node.node.text,
                'score': node.score,
                'metadata': node.node.metadata
            }
            for node in nodes
        ]
