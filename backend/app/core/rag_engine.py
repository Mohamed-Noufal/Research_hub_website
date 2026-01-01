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
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import TextNode
import os
import logging
from sqlalchemy import text

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
        user_id: str = None,
        title: str = None,
        project_id: int = None,
        metadata: dict = None
    ) -> dict:
        """
        Parse PDF with Docling and ingest into LlamaIndex
        
        Args:
            paper_id: ID from YOUR papers table
            pdf_path: Path to PDF file
            user_id: User who owns this paper (for scoped retrieval)
            title: Paper title (for context in search results)
            project_id: Project ID if paper belongs to a project
            metadata: Optional additional metadata
        
        Returns:
            dict with ingestion stats
        """
        logger.info(f"📄 Processing paper {paper_id} with Docling...")
        
        if not os.path.exists(pdf_path):
             raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Parse PDF with Docling (extracts equations, images, tables)
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        
        stats = {
            'total_elements': 0,
            'equations': 0,
            'tables': 0,
            'images': 0,
            'text_chunks': 0,
            'markdown_length': 0
        }
        
        # Use export_to_markdown() which works correctly in Docling
        # Note: iterate_items() returns tuples without .text attribute
        markdown_content = result.document.export_to_markdown()
        stats['markdown_length'] = len(markdown_content)
        
        if not markdown_content or len(markdown_content) < 100:
            logger.warning(f"  ⚠️ Very little content extracted from PDF: {len(markdown_content)} chars")
            return stats
            
        logger.info(f"  📊 Extracted {len(markdown_content)} chars of markdown")
        
        # Create a single Document from the full markdown content
        # LlamaIndex will chunk it appropriately
        chunk_metadata = {
            "paper_id": paper_id,
            "user_id": user_id,              # For user-scoped search
            "title": title or "Untitled",    # For context in results
            "project_id": project_id,        # For project-scoped search
            "section_type": "full_document", # Will be refined by chunking
            "source": "docling_markdown",
        }
        
        # Merge any additional metadata
        if metadata:
            chunk_metadata.update(metadata)
        
        doc = Document(
            text=markdown_content,
            metadata=chunk_metadata
        )
        
        logger.info(f"  📊 Created document from markdown")
        
        # Parse into nodes (chunks) with LlamaIndex
        parser = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )
        nodes = parser.get_nodes_from_documents([doc])
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
        user_id: str = None,
        top_k: int = 10,
        return_sources: bool = True
    ) -> dict:
        """
        Query using Hybrid Search (Vector + BM25)
        Filters by user_id, project_id, or paper_ids for accurate scoping
        """
        logger.info(f"Query (Hybrid): '{query_text}' user={user_id} project={project_id}")
        
        # Build vector filters
        filters = []
        if user_id:
            filters.append(MetadataFilter(key="user_id", value=str(user_id)))
        if project_id:
            filters.append(MetadataFilter(key="project_id", value=project_id))
        if paper_ids:
            filters.append(MetadataFilter(key="paper_id", value=paper_ids, operator=FilterOperator.IN))
        if section_filter:
            filters.append(MetadataFilter(key="section_type", value=section_filter, operator=FilterOperator.IN))
        
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        # Get Hybrid Retriever
        retriever = await self._get_hybrid_retriever(
            similarity_top_k=top_k,
            filters=metadata_filters,
            project_id=project_id,
            paper_ids=paper_ids,
            user_id=user_id
        )
        
        # Determine strict top_k for synthesis (since fusion returns more candidates usually)
        # But Fusion retriever controls output count via similarity_top_k.
        
        from llama_index.core.query_engine import RetrieverQueryEngine
        
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=self.llm
        )
        
        response = await query_engine.aquery(query_text)
        
        result = {
            'answer': str(response),
            'source_nodes': []
        }
        
        if return_sources and hasattr(response, 'source_nodes'):
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

    def _fetch_nodes_for_scope(
        self,
        project_id: int = None,
        paper_ids: list = None,
        user_id: str = None
    ) -> list:
        """
        Fetch text nodes from DB for BM25 index construction.
        Filters by user_id, project_id, or specific paper_ids for accurate scoping.
        Limit to 2000 chunks to prevent memory explosion.
        """
        from sqlalchemy import text
        from app.core.database import SessionLocal
        import json
        
        db = SessionLocal()
        try:
            # Table name is typically 'data_paper_chunks' for table_name='paper_chunks'
            query_str = "SELECT text, node_id, metadata_ FROM data_paper_chunks"
            params = {}
            conditions = []
            
            # Filter by user_id for user-scoped search
            if user_id:
                conditions.append("metadata_->>'user_id' = :uid")
                params['uid'] = str(user_id)
            
            if project_id:
                # Metadata is JSONB. Accessing top-level field.
                # Note: PGVectorStore metadata_ column structure depends on version.
                # Often it's `metadata_` -> key.
                # We'll use the ->> operator for Postgres JSONB.
                conditions.append("metadata_->>'project_id' = :pid")
                params['pid'] = str(project_id) # JSON values often stringified
            
            if paper_ids:
                # 'paper_id' in metadata
                # Use ANY with cast if needed, or simple IN
                # For safety with SQLAlchemy headers:
                # "metadata_->>'paper_id' IN :pids"
                # But :pids parameter needs to be tuple.
                if len(paper_ids) == 1:
                     conditions.append("metadata_->>'paper_id' = :pid_single")
                     params['pid_single'] = str(paper_ids[0])
                else:
                     # manual string construction for IN clause to avoid binding issues with JSON operators sometimes, 
                     # but binding is safer. 
                     # Let's try explicit IN with list
                     # Or check if paper_id is integer in metadata?
                     # Let's assume string matching logic for safety in JSON query
                     ids_str = ",".join([f"'{pid}'" for pid in paper_ids])
                     conditions.append(f"metadata_->>'paper_id' IN ({ids_str})")
            
            if conditions:
                query_str += " WHERE " + " AND ".join(conditions)
                
            query_str += " LIMIT 2000"
            
            try:
                result = db.execute(text(query_str), params)
            except Exception as e:
                logger.warning(f"⚠️ BM25 Fetch Failed (DB Error): {e}. Falling back to Vector only.")
                return []
            
            nodes = []
            for row in result:
                # Row is likely (text, node_id, metadata_)
                text_content = row[0]
                node_id = row[1]
                metadata_val = row[2]
                
                # metadata_val might be dict or string
                if isinstance(metadata_val, str):
                    metadata = json.loads(metadata_val)
                else:
                    metadata = metadata_val or {}
                    
                node = TextNode(
                    text=text_content,
                    id_=node_id,
                    metadata=metadata
                )
                nodes.append(node)
                
            logger.info(f"  📚 Fetched {len(nodes)} nodes for BM25 index")
            return nodes
        except Exception as e:
            logger.error(f"Error fetching nodes for BM25: {e}")
            return []
        finally:
            db.close()

    async def _get_hybrid_retriever(
        self,
        similarity_top_k: int,
        filters: MetadataFilters,
        project_id: int = None,
        paper_ids: list = None,
        user_id: str = None
    ):
        """
        Construct a hybrid retriever (Vector + BM25)
        Filters by user_id, project_id, or paper_ids for accurate scoping
        """
        # 1. Vector Retriever
        vector_retriever = self.index.as_retriever(
            similarity_top_k=similarity_top_k,
            filters=filters
        )
        
        # 2. BM25 Retriever
        bm25_retriever = None
        
        # Build in-memory BM25 if we have specific scope (user, project, or papers)
        if user_id or project_id or paper_ids:
             nodes = self._fetch_nodes_for_scope(project_id, paper_ids, user_id)
             if nodes:
                 try:
                     logger.info("  🧮 Building in-memory BM25 index...")
                     bm25_retriever = BM25Retriever.from_defaults(
                         nodes=nodes,
                         similarity_top_k=similarity_top_k
                     )
                 except Exception as e:
                     logger.error(f"Failed to build BM25 retriever: {e}")
        
        if not bm25_retriever:
            logger.info("  ⚠️ Passing only Vector Retriever (No BM25 built)")
            return vector_retriever
            
        logger.info("  ⚡ Using Hybrid Retriever (Vector + BM25)")
        return QueryFusionRetriever(
            [vector_retriever, bm25_retriever],
            similarity_top_k=similarity_top_k,
            num_queries=1,
            use_async=True,
            fusion_mode="reciprocal_rank"
        )

    
    async def retrieve_only(
        self,
        query_text: str,
        project_id: int = None,
        paper_ids: list = None,
        section_filter: list = None,
        user_id: str = None,
        top_k: int = 10
    ) -> list:
        """
        Retrieve chunks without LLM generation (faster, cheaper)
        Filters by user_id, project_id, or paper_ids for accurate scoping
        """
        # Build vector retriever
        filters = []
        if user_id:
            filters.append(MetadataFilter(key="user_id", value=str(user_id)))
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
