# AI Assistant: Monitoring, Cost Tracking & RAG Process

## 📊 Comprehensive Monitoring System

### 1. LLM Token & Cost Tracking

```python
# backend/app/core/llm_client.py

class LLMClient:
    """Groq LLM client with comprehensive tracking"""
    
    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.metrics = MetricsCollector()
        
        # Pricing (Groq - as of 2024)
        self.pricing = {
            "llama-3.1-70b-versatile": {
                "input": 0.00059 / 1000,   # $0.59 per 1M tokens
                "output": 0.00079 / 1000    # $0.79 per 1M tokens
            },
            "llama-3.1-8b-instant": {
                "input": 0.00005 / 1000,
                "output": 0.00008 / 1000
            }
        }
    
    async def complete(self, prompt: str, model: str = "llama-3.1-70b-versatile"):
        """Complete with full tracking"""
        start_time = time.time()
        
        try:
            # Count input tokens
            input_tokens = self._count_tokens(prompt)
            
            # Call LLM
            response = await self.groq.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract response
            output_text = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
            # Calculate cost
            cost = self._calculate_cost(
                model, input_tokens, output_tokens
            )
            
            # Log metrics
            duration_ms = (time.time() - start_time) * 1000
            
            await self._log_llm_call(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
                duration_ms=duration_ms,
                success=True
            )
            
            return output_text
            
        except Exception as e:
            await self._log_llm_call(
                model=model,
                error=str(e),
                success=False
            )
            raise
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int):
        """Calculate exact cost"""
        pricing = self.pricing[model]
        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        return input_cost + output_cost
    
    async def _log_llm_call(self, **kwargs):
        """Log to database for tracking"""
        await self.db.execute(
            text("""
                INSERT INTO llm_usage_logs (
                    model, input_tokens, output_tokens, total_tokens,
                    cost_usd, duration_ms, success, error, created_at
                ) VALUES (
                    :model, :input_tokens, :output_tokens, :total_tokens,
                    :cost_usd, :duration_ms, :success, :error, NOW()
                )
            """),
            kwargs
        )
```

### 2. RAG Operation Tracking

```python
# backend/app/core/vector_store.py

class VectorStore:
    """pgvector operations with tracking"""
    
    async def similarity_search(
        self,
        query: str,
        user_id: str,
        filters: Dict = None,
        top_k: int = 10
    ):
        """Search with comprehensive tracking"""
        start_time = time.time()
        
        try:
            # Generate query embedding
            embed_start = time.time()
            query_embedding = await self.embed_text(query)
            embed_duration = (time.time() - embed_start) * 1000
            
            # Build SQL query
            sql, params = self._build_search_query(
                query_embedding, user_id, filters, top_k
            )
            
            # Execute search
            search_start = time.time()
            results = await self.db.execute(text(sql), params)
            chunks = results.fetchall()
            search_duration = (time.time() - search_start) * 1000
            
            # Calculate metrics
            total_duration = (time.time() - start_time) * 1000
            avg_similarity = sum(c.similarity for c in chunks) / len(chunks) if chunks else 0
            
            # Log RAG operation
            await self._log_rag_operation(
                query=query,
                user_id=user_id,
                filters=filters,
                results_count=len(chunks),
                avg_similarity=avg_similarity,
                embed_duration_ms=embed_duration,
                search_duration_ms=search_duration,
                total_duration_ms=total_duration
            )
            
            return chunks
            
        except Exception as e:
            await self._log_rag_operation(
                query=query,
                error=str(e),
                success=False
            )
            raise
    
    async def _log_rag_operation(self, **kwargs):
        """Log RAG metrics"""
        await self.db.execute(
            text("""
                INSERT INTO rag_usage_logs (
                    query, user_id, filters, results_count, avg_similarity,
                    embed_duration_ms, search_duration_ms, total_duration_ms,
                    success, error, created_at
                ) VALUES (
                    :query, :user_id, :filters, :results_count, :avg_similarity,
                    :embed_duration_ms, :search_duration_ms, :total_duration_ms,
                    :success, :error, NOW()
                )
            """),
            kwargs
        )
```

### 3. Database Schema for Monitoring

```sql
-- LLM usage tracking
CREATE TABLE llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES local_users(id),
    conversation_id UUID REFERENCES agent_conversations(id),
    model VARCHAR(100) NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost_usd DECIMAL(10, 6),
    duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- RAG usage tracking
CREATE TABLE rag_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES local_users(id),
    query TEXT NOT NULL,
    filters JSONB,
    results_count INTEGER,
    avg_similarity DECIMAL(5, 4),
    embed_duration_ms INTEGER,
    search_duration_ms INTEGER,
    total_duration_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent performance tracking
CREATE TABLE agent_performance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(50) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    duration_ms INTEGER,
    llm_calls INTEGER DEFAULT 0,
    rag_calls INTEGER DEFAULT 0,
    total_cost_usd DECIMAL(10, 6),
    success BOOLEAN DEFAULT true,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_logs_user_date ON llm_usage_logs(user_id, created_at);
CREATE INDEX idx_llm_logs_cost ON llm_usage_logs(cost_usd, created_at);
CREATE INDEX idx_rag_logs_user_date ON rag_usage_logs(user_id, created_at);
```

---

## 🔍 RAG Process: When & How It Works

### When RAG is Triggered

```python
# RAG is used in these scenarios:

1. **User asks questions about papers**
   User: "What methodologies did these papers use?"
   → RAG: Query methodology sections
   
2. **Generating literature review sections**
   User: "Generate introduction section"
   → RAG: Retrieve relevant content from all papers
   
3. **Comparing papers**
   User: "Compare results across my papers"
   → RAG: Query results/findings sections
   
4. **Finding research gaps**
   User: "What are the research gaps?"
   → RAG: Analyze limitations and future work sections
```

### RAG Pipeline (Step-by-Step)

```python
# backend/app/agents/analysis_agent.py

class AnalysisAgent(BaseAgent):
    
    async def query_papers(self, query: str, context: AgentContext):
        """
        Complete RAG pipeline with optimization
        """
        
        # STEP 1: Query Understanding & Expansion
        expanded_query = await self._expand_query(query)
        # Original: "What methods were used?"
        # Expanded: "methodology approach techniques experimental design"
        
        # STEP 2: Generate Query Embedding
        query_embedding = await self.vector_store.embed_text(expanded_query)
        # 768-dimensional vector from nomic-embed-text-v1.5
        
        # STEP 3: Build Filters (Smart Retrieval)
        filters = self._build_filters(context)
        # {
        #   "user_id": "123",
        #   "project_id": 5,
        #   "section_types": ["methodology", "experiments"],
        #   "paper_ids": [42, 58, 91, 103]  # Only papers in project
        # }
        
        # STEP 4: Similarity Search (pgvector)
        chunks = await self.vector_store.similarity_search(
            query_embedding=query_embedding,
            filters=filters,
            top_k=20  # Retrieve top 20 chunks
        )
        
        # SQL executed:
        # SELECT pc.text, pc.section_type, gp.title,
        #        1 - (pc.embedding <=> $query_vec) AS similarity
        # FROM paper_chunks pc
        # JOIN global_papers gp ON pc.global_paper_id = gp.id
        # JOIN user_papers up ON up.global_paper_id = gp.id
        # WHERE up.user_id = '123'
        #   AND up.project_id = 5
        #   AND pc.section_type IN ('methodology', 'experiments')
        #   AND gp.id IN (42, 58, 91, 103)
        # ORDER BY pc.embedding <=> $query_vec
        # LIMIT 20
        
        # STEP 5: Reranking (Optional but Recommended)
        reranked_chunks = await self._rerank_chunks(query, chunks)
        # Use cross-encoder to rerank top 20 → select best 8
        # More accurate than just cosine similarity
        
        # STEP 6: Context Compression
        compressed_context = await self._compress_context(reranked_chunks)
        # Techniques:
        # - Remove redundant information
        # - Use hierarchical summaries for long chunks
        # - Extract only relevant sentences
        # Result: 80% token reduction (6000 → 1200 tokens)
        
        # STEP 7: Augment with Metadata
        enriched_context = self._add_metadata(compressed_context)
        # Add: paper titles, authors, publication year, section types
        
        # STEP 8: Generate Response
        response = await self.llm.complete(
            prompt=f"""
            Based on these research papers:
            
            {enriched_context}
            
            Answer this question: {query}
            
            Provide specific citations in format [Paper Title, Year].
            """
        )
        
        return {
            "answer": response,
            "sources": [chunk.paper_title for chunk in reranked_chunks],
            "metrics": {
                "chunks_retrieved": len(chunks),
                "chunks_used": len(reranked_chunks),
                "token_reduction": "80%",
                "avg_similarity": sum(c.similarity for c in chunks) / len(chunks)
            }
        }
```

### RAG Optimization Strategies

```python
# 1. Hierarchical Retrieval (for long papers)
class HierarchicalRAG:
    """
    First retrieve at section level, then drill down to chunks
    """
    async def retrieve(self, query):
        # Step 1: Find relevant sections
        sections = await self.search_sections(query, top_k=5)
        
        # Step 2: Within those sections, find best chunks
        chunks = []
        for section in sections:
            section_chunks = await self.search_chunks(
                query, section_id=section.id, top_k=3
            )
            chunks.extend(section_chunks)
        
        return chunks

# 2. Hybrid Search (combine semantic + keyword)
class HybridRAG:
    """
    Combine pgvector similarity with PostgreSQL full-text search
    """
    async def retrieve(self, query):
        # Semantic search
        semantic_results = await self.vector_search(query, top_k=15)
        
        # Keyword search
        keyword_results = await self.db.execute(
            text("""
                SELECT * FROM paper_chunks
                WHERE to_tsvector('english', text) @@ plainto_tsquery(:query)
                LIMIT 15
            """),
            {"query": query}
        )
        
        # Merge and rerank
        combined = self._merge_results(semantic_results, keyword_results)
        return combined[:10]

# 3. Context Caching (save money)
class CachedRAG:
    """
    Cache frequent queries to avoid re-embedding
    """
    async def retrieve(self, query):
        # Check cache
        cache_key = hashlib.md5(query.encode()).hexdigest()
        cached = await self.redis.get(f"rag:{cache_key}")
        
        if cached:
            return json.loads(cached)
        
        # Not cached, do full RAG
        results = await self.full_rag_pipeline(query)
        
        # Cache for 1 hour
        await self.redis.setex(
            f"rag:{cache_key}",
            3600,
            json.dumps(results)
        )
        
        return results
```

---

## 📁 Easy PDF Selection & Upload

### Current Problem
Users have to manually browse files, which is tedious for multiple PDFs.

### Solution: Drag-and-Drop + Batch Upload

```tsx
// frontend/src/components/ai/PDFUploader.tsx

function PDFUploader({ onUpload }: { onUpload: (files: File[]) => void }) {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf'
    );
    
    setFiles(prev => [...prev, ...droppedFiles]);
  };
  
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
    }
  };
  
  const uploadAll = async () => {
    for (const file of files) {
      await onUpload(file);
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Drag & Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          dragActive 
            ? 'border-indigo-500 bg-indigo-50' 
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
      >
        <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-lg font-medium text-gray-700">
          Drag & drop PDF files here
        </p>
        <p className="text-sm text-gray-500 mt-2">
          or click to browse
        </p>
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileInput}
          className="hidden"
          id="pdf-input"
        />
        <label
          htmlFor="pdf-input"
          className="mt-4 inline-block px-4 py-2 bg-indigo-600 text-white rounded-lg cursor-pointer hover:bg-indigo-700"
        >
          Browse Files
        </label>
      </div>
      
      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h3 className="font-medium text-gray-900">
            Selected Files ({files.length})
          </h3>
          {files.map((file, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-red-500" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={() => setFiles(files.filter((_, i) => i !== idx))}
                className="p-1 hover:bg-gray-200 rounded"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
          ))}
          
          <Button
            onClick={uploadAll}
            className="w-full bg-indigo-600 hover:bg-indigo-700"
          >
            Upload {files.length} PDF{files.length > 1 ? 's' : ''}
          </Button>
        </div>
      )}
    </div>
  );
}
```

### Alternative: Chat-Based Upload

```tsx
// User can also upload via chat
function ChatInterface() {
  const handleMessage = async (message: string, attachments: File[]) => {
    if (attachments.length > 0) {
      // User sent PDFs via chat
      await sendMessage({
        text: message || "I'm uploading these papers",
        files: attachments
      });
    }
  };
  
  return (
    <ChatInput
      onSend={handleMessage}
      allowAttachments={true}
      acceptedTypes={['.pdf']}
    />
  );
}
```

---

## 📈 Evaluation & Quality Metrics

### 1. RAG Quality Metrics

```python
# backend/app/core/evaluation.py

class RAGEvaluator:
    """Evaluate RAG quality"""
    
    async def evaluate_retrieval(self, query: str, retrieved_chunks: List):
        """
        Metrics:
        - Precision@K: How many retrieved chunks are relevant?
        - Recall: Did we retrieve all relevant chunks?
        - MRR (Mean Reciprocal Rank): Position of first relevant result
        - NDCG: Normalized Discounted Cumulative Gain
        """
        
        # Calculate relevance scores
        relevance_scores = []
        for chunk in retrieved_chunks:
            score = await self._calculate_relevance(query, chunk)
            relevance_scores.append(score)
        
        # Precision@10
        precision_at_10 = sum(1 for s in relevance_scores[:10] if s > 0.7) / 10
        
        # Log metrics
        await self.db.execute(
            text("""
                INSERT INTO rag_quality_metrics (
                    query, precision_at_10, avg_relevance, created_at
                ) VALUES (:query, :precision, :avg_relevance, NOW())
            """),
            {
                "query": query,
                "precision": precision_at_10,
                "avg_relevance": sum(relevance_scores) / len(relevance_scores)
            }
        )
        
        return {
            "precision@10": precision_at_10,
            "avg_relevance": sum(relevance_scores) / len(relevance_scores)
        }
```

### 2. Generation Quality Metrics

```python
class GenerationEvaluator:
    """Evaluate generated content quality"""
    
    async def evaluate_section(self, generated_text: str, sources: List):
        """
        Metrics:
        - Citation accuracy: Are citations correct?
        - Factual consistency: Does content match sources?
        - Coherence: Is the text well-structured?
        - Completeness: Does it cover required schema fields?
        """
        
        # Check citation accuracy
        citations = self._extract_citations(generated_text)
        citation_accuracy = self._verify_citations(citations, sources)
        
        # Check factual consistency (using LLM)
        consistency_score = await self._check_consistency(
            generated_text, sources
        )
        
        # Check completeness
        schema = await self._get_section_schema()
        completeness = self._check_schema_coverage(generated_text, schema)
        
        return {
            "citation_accuracy": citation_accuracy,
            "factual_consistency": consistency_score,
            "completeness": completeness
        }
```

### 3. Cost Monitoring Dashboard

```python
# backend/app/api/v1/monitoring.py

@router.get("/monitoring/costs")
async def get_cost_metrics(
    user_id: str = Depends(get_current_user_id),
    timeframe: str = "7d"
):
    """Get cost breakdown"""
    
    # LLM costs
    llm_costs = await db.execute(
        text("""
            SELECT 
                DATE(created_at) as date,
                model,
                SUM(cost_usd) as total_cost,
                SUM(total_tokens) as total_tokens,
                COUNT(*) as call_count
            FROM llm_usage_logs
            WHERE user_id = :user_id
              AND created_at >= NOW() - INTERVAL :timeframe
            GROUP BY DATE(created_at), model
            ORDER BY date DESC
        """),
        {"user_id": user_id, "timeframe": timeframe}
    )
    
    # RAG costs (embedding costs)
    rag_costs = await db.execute(
        text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as search_count,
                AVG(total_duration_ms) as avg_duration
            FROM rag_usage_logs
            WHERE user_id = :user_id
              AND created_at >= NOW() - INTERVAL :timeframe
            GROUP BY DATE(created_at)
        """),
        {"user_id": user_id, "timeframe": timeframe}
    )
    
    return {
        "llm_costs": [dict(row) for row in llm_costs],
        "rag_costs": [dict(row) for row in rag_costs],
        "total_cost": sum(row.total_cost for row in llm_costs)
    }
```

---

## 🎯 Best Practices Summary

### For Your Project

1. **Use Groq for LLM** - Fast and cost-effective
2. **Use nomic-embed for embeddings** - Best quality/price ratio
3. **Implement caching** - Save 60-80% on costs
4. **Use hierarchical RAG** - Better accuracy for long papers
5. **Track everything** - Monitor costs, performance, quality
6. **Batch operations** - Process multiple PDFs efficiently
7. **Provide drag-and-drop** - Better UX than file browser

### Cost Optimization

- **Context compression**: 80% token reduction
- **Smart retrieval**: Filter by section type
- **Caching**: Reuse embeddings and queries
- **Deduplication**: Process each paper once
- **Batch processing**: Upload multiple PDFs together

Would you like me to implement any of these components first?
