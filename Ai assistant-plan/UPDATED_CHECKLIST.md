# AI Assistant Implementation Checklist - Customized for Your Project

## 🎯 Project-Specific Customizations

### What We're Leveraging (Already Built):
- ✅ **Nomic Embeddings**: `nomic-ai/nomic-embed-text-v1.5` (768 dims) in `EnhancedVectorService`
- ✅ **Vector Search**: Hybrid semantic + keyword search already working
- ✅ **Database Tables**: `comparison_configs`, `findings`, `methodology_data`, `synthesis_data`
- ✅ **API Endpoints**: `/comparison`, `/findings`, `/methodology`, `/synthesis`
- ✅ **Frontend Components**: ComparisonView, FindingsView, MethodologyView, SummaryView

### What We're Adding:
- 🆕 **Docling PDF Parser**: Extract equations, images, tables from academic PDFs
- 🆕 **RAG Engine**: Query paper chunks with semantic search
- 🆕 **AI Agents**: Autonomous task execution with tools
- 🆕 **Chat Interface**: Natural language interaction
- 🆕 **Real-time Updates**: WebSocket for UI synchronization

---

## ✅ Phase 1: Foundation & Database Setup (COMPLETED)

### Database Setup ✅
- [x] Create migration file `020_agent_system.sql`
- [x] Add `paper_chunks` table (with 768-dim vectors for Nomic)
- [x] Add `agent_conversations` table
- [x] Add `agent_messages` table
- [x] Add `agent_tool_calls` table
- [x] Add `llm_usage_logs` table
- [x] Add `rag_usage_logs` table
- [x] Add indexes for performance
- [x] Test migration on dev database
- [x] Verify no conflicts with existing tables

### Core Infrastructure ✅
- [x] Create `backend/app/agents/` directory
- [x] Create `backend/app/tools/` directory
- [x] Update `config.py` with AI agent settings
- [x] Update `requirements.txt` with dependencies

### Dependencies (Installing)
- [/] Install Groq for LLM
- [/] Install tiktoken for token counting
- [/] Install Docling for PDF parsing
- [/] Install tenacity for retry logic
- [/] Install websockets for real-time updates

---

## 📋 Phase 2: Core Components with Existing Infrastructure

### RAG Engine (Use YOUR Nomic Embeddings)
- [ ] Create `backend/app/core/rag_engine.py`
- [ ] Integrate with `EnhancedVectorService` (reuse Nomic model)
- [ ] Implement `ingest_paper()` with Docling parsing
  - [ ] Extract text chunks
  - [ ] Extract equations (LaTeX)
  - [ ] Extract tables (structured data)
  - [ ] Extract images/figures metadata
  - [ ] Generate embeddings using YOUR Nomic model
  - [ ] Store in `paper_chunks` table
- [ ] Implement `query()` for semantic search
  - [ ] Use YOUR existing vector similarity logic
  - [ ] Filter by project_id
  - [ ] Filter by section_type (methodology, results, etc.)
  - [ ] Return chunks with similarity scores
- [ ] Add caching layer (optional)
- [ ] Test with sample academic PDFs

### LLM Client with Groq
- [ ] Create `backend/app/core/llm_client.py`
- [ ] Implement Groq API wrapper
- [ ] Add retry logic with exponential backoff (tenacity)
- [ ] Implement token counting (tiktoken)
- [ ] Add cost tracking to `llm_usage_logs` table
- [ ] Test LLM connectivity
- [ ] Test different models (llama-3.1-70b, llama-3.1-8b)

### Flexible Agent Base Class
- [ ] Create `backend/app/agents/base.py`
- [ ] Implement `Tool` class with:
  - [ ] Parameter validation
  - [ ] Execution tracking
  - [ ] Result formatting
- [ ] Implement `FlexibleAgent` class with:
  - [ ] Tool initialization
  - [ ] Context management
  - [ ] ReAct loop (Think → Act → Observe)
  - [ ] Memory management
  - [ ] Error handling
  - [ ] Logging
- [ ] Test with simple tools

### Memory Management
- [ ] Create `backend/app/core/memory.py`
- [ ] Implement conversation memory
  - [ ] Store in `agent_messages` table
  - [ ] Retrieve recent messages
  - [ ] Summarize long conversations
- [ ] Implement context management
  - [ ] Track current project_id
  - [ ] Track current user_id
  - [ ] Track tool execution history
- [ ] Add persistent storage
- [ ] Test memory retrieval

---

## 📋 Phase 3: Tools & Agents (Integration with YOUR Tables)

### Database Tools (Use YOUR Existing Tables)
- [ ] Create `backend/app/tools/database_tools.py`
- [ ] Implement tools:
  - [ ] `get_project_by_name` - Find project by fuzzy name match
  - [ ] `get_project_papers` - Fetch from YOUR `project_papers` table
  - [ ] `update_comparison` - Update YOUR `comparison_configs` table
    - [ ] Update `insights_similarities`
    - [ ] Update `insights_differences`
    - [ ] Update `selected_paper_ids`
  - [ ] `update_methodology` - Update YOUR `methodology_data` table
    - [ ] Update methodology summary
    - [ ] Update data collection methods
    - [ ] Update analysis methods
  - [ ] `update_findings` - Update YOUR `findings` table
    - [ ] Update key findings
    - [ ] Update limitations
    - [ ] Update custom notes
  - [ ] `update_synthesis` - Update YOUR `synthesis_data` table
  - [ ] `link_paper_to_project` - Add to `project_papers`
- [ ] Add transaction safety (FOR UPDATE locks)
- [ ] Test concurrent operations
- [ ] Verify no conflicts with existing UI

### RAG Tools (Use YOUR Nomic Embeddings)
- [ ] Create `backend/app/tools/rag_tools.py`
- [ ] Implement tools:
  - [ ] `semantic_search` - Query paper chunks
    - [ ] Use YOUR `EnhancedVectorService`
    - [ ] Filter by project_id
    - [ ] Filter by section_type
    - [ ] Return top-k results
  - [ ] `compare_papers` - Generate comparison insights
    - [ ] Query relevant chunks from multiple papers
    - [ ] Use LLM to synthesize comparison
    - [ ] Format for `comparison_configs` table
  - [ ] `extract_methodology` - Extract methodology details
    - [ ] Query methodology sections
    - [ ] Extract structured data
    - [ ] Format for `methodology_data` table
  - [ ] `find_research_gaps` - Identify gaps
    - [ ] Analyze findings across papers
    - [ ] Generate gap descriptions
    - [ ] Format for `research_gaps` table
- [ ] Add reranking logic (optional)
- [ ] Test query accuracy

### PDF Processing Tools (Docling Integration)
- [ ] Create `backend/app/tools/pdf_tools.py`
- [ ] Implement tools:
  - [ ] `parse_pdf` - Extract with Docling
    - [ ] Handle equations (LaTeX)
    - [ ] Handle tables (structured)
    - [ ] Handle images/figures
    - [ ] Preserve academic structure
  - [ ] `check_paper_exists` - Check by DOI/hash
  - [ ] `store_paper` - Save to `papers` table
  - [ ] `generate_embeddings` - Use YOUR Nomic model
- [ ] Add file upload handling
- [ ] Test with various PDF formats (IEEE, ACM, Nature, etc.)

### Orchestrator Agent
- [ ] Create `backend/app/agents/orchestrator.py`
- [ ] Implement intent classification
  - [ ] Detect "upload PDF" intent
  - [ ] Detect "query papers" intent
  - [ ] Detect "generate section" intent
  - [ ] Detect "compare papers" intent
- [ ] Implement execution planning
  - [ ] Break down complex tasks
  - [ ] Determine tool sequence
  - [ ] Handle dependencies
- [ ] Implement task delegation
  - [ ] Delegate to database tools
  - [ ] Delegate to RAG tools
  - [ ] Delegate to PDF tools
- [ ] Implement response synthesis
- [ ] Add conversation memory
- [ ] Test with sample conversations

---

## 📋 Phase 4: API & Frontend Integration

### Backend API
- [ ] Create `backend/app/api/v1/agent.py`
- [ ] Implement endpoints:
  - [ ] `POST /api/v1/agent/chat` - Main chat endpoint
    - [ ] Accept message + project_id
    - [ ] Process with orchestrator
    - [ ] Return response + metadata
  - [ ] `GET /api/v1/agent/conversations` - List conversations
  - [ ] `GET /api/v1/agent/conversation/{id}` - Get history
  - [ ] `DELETE /api/v1/agent/conversation/{id}` - Delete conversation
  - [ ] `WS /api/v1/agent/ws/{conversation_id}` - WebSocket for real-time
- [ ] Add authentication (use existing `get_current_user_id`)
- [ ] Add rate limiting
- [ ] Test all endpoints

### Agent Service
- [ ] Create `backend/app/services/agent_service.py`
- [ ] Implement:
  - [ ] `process_message()` - Main entry point
    - [ ] Create/retrieve conversation
    - [ ] Process with orchestrator
    - [ ] Save messages to database
    - [ ] Emit WebSocket events
  - [ ] `create_conversation()` - Initialize new conversation
  - [ ] `get_conversation_history()` - Retrieve messages
  - [ ] `subscribe_to_progress()` - WebSocket event stream
- [ ] Add error handling
- [ ] Add logging (structured)

### Frontend Integration
- [ ] Create `frontend/src/components/ai/ChatPanel.tsx`
  - [ ] Message list with user/assistant bubbles
  - [ ] Input field with send button
  - [ ] Loading indicator
  - [ ] Error handling
- [ ] Create `frontend/src/components/ai/MessageBubble.tsx`
  - [ ] User message styling
  - [ ] Assistant message styling
  - [ ] Markdown rendering
  - [ ] Code syntax highlighting
- [ ] Create `frontend/src/components/ai/ProgressTracker.tsx`
  - [ ] Show current tool execution
  - [ ] Show progress percentage
  - [ ] Show estimated time
- [ ] Create `frontend/src/hooks/useAgent.ts`
  - [ ] `sendMessage()` function
  - [ ] `messages` state
  - [ ] `isProcessing` state
  - [ ] WebSocket connection management
- [ ] Implement WebSocket connection
- [ ] Add real-time progress updates
- [ ] Style chat interface (match existing UI)
- [ ] Test UI/UX flow

### Integration with Literature Review
- [ ] Add chat toggle button to LiteratureReview component
- [ ] Add split view (tabs on left, chat on right)
- [ ] Auto-refresh tabs when AI updates data
  - [ ] Listen for WebSocket events
  - [ ] Invalidate React Query cache
  - [ ] Show success notifications
- [ ] Test full workflow:
  - [ ] User asks "Generate methodology section"
  - [ ] AI queries papers
  - [ ] AI generates content
  - [ ] AI updates `methodology_data` table
  - [ ] UI auto-refreshes MethodologyView

### Real-time Updates
- [ ] Implement WebSocket server (FastAPI WebSocket)
- [ ] Create event emitters in agents
  - [ ] Emit "tool_started" event
  - [ ] Emit "tool_completed" event
  - [ ] Emit "section_updated" event
  - [ ] Emit "progress" event
- [ ] Add progress tracking
- [ ] Test real-time updates
- [ ] Handle disconnections gracefully

---

## 📋 Phase 5: Testing & Quality

### Unit Tests
- [ ] Test `RAGEngine` class
  - [ ] Test `ingest_paper()` with sample PDF
  - [ ] Test `query()` with various filters
  - [ ] Test embedding generation
- [ ] Test `LLMClient` class
  - [ ] Test `complete()` with mock responses
  - [ ] Test retry logic
  - [ ] Test cost tracking
- [ ] Test `FlexibleAgent` class
  - [ ] Test tool execution
  - [ ] Test memory management
  - [ ] Test error handling
- [ ] Test database tools
  - [ ] Test `get_project_papers()`
  - [ ] Test `update_comparison()`
  - [ ] Test `update_findings()`
- [ ] Test RAG tools
  - [ ] Test `semantic_search()`
  - [ ] Test `compare_papers()`
- [ ] Achieve 80%+ coverage

### Integration Tests
- [ ] Test full upload workflow
  - [ ] Upload PDF via chat
  - [ ] Verify parsing with Docling
  - [ ] Verify embeddings generated
  - [ ] Verify chunks stored
- [ ] Test query workflow
  - [ ] Ask question about papers
  - [ ] Verify semantic search
  - [ ] Verify relevant results
- [ ] Test section generation workflow
  - [ ] Request methodology section
  - [ ] Verify RAG query
  - [ ] Verify LLM generation
  - [ ] Verify database update
  - [ ] Verify UI refresh
- [ ] Test concurrent operations
  - [ ] Multiple users chatting
  - [ ] Concurrent database updates
  - [ ] No race conditions
- [ ] Test error scenarios
  - [ ] Invalid PDF
  - [ ] LLM timeout
  - [ ] Database error
- [ ] Test WebSocket events
  - [ ] Connect/disconnect
  - [ ] Receive progress updates
  - [ ] Handle reconnection

### Performance Tests
- [ ] Load test chat endpoint
  - [ ] 10 concurrent users
  - [ ] Response time < 3s
- [ ] Test RAG query performance
  - [ ] Query time < 2s
  - [ ] Optimize if needed
- [ ] Test concurrent users
  - [ ] 50 concurrent conversations
  - [ ] No degradation
- [ ] Optimize slow queries
  - [ ] Add indexes if needed
  - [ ] Use query caching
- [ ] Add caching where needed
  - [ ] Cache LLM responses (optional)
  - [ ] Cache RAG results (optional)

### Manual Testing
- [ ] Upload PDF via chat
  - [ ] Test with IEEE paper
  - [ ] Test with Nature paper
  - [ ] Test with arXiv paper
- [ ] Ask questions about papers
  - [ ] "What methodology did they use?"
  - [ ] "Compare the findings"
  - [ ] "What are the limitations?"
- [ ] Generate methodology section
  - [ ] Verify content quality
  - [ ] Verify citations included
  - [ ] Verify table updated
- [ ] Compare papers
  - [ ] Verify similarities identified
  - [ ] Verify differences identified
  - [ ] Verify comparison_configs updated
- [ ] Verify UI updates correctly
  - [ ] Auto-refresh works
  - [ ] No manual reload needed
- [ ] Test on mobile (optional)

---

## 📋 Phase 6: Production Readiness

### Error Handling
- [ ] Add retry logic to all LLM calls (already in LLMClient)
- [ ] Implement graceful degradation
  - [ ] Fallback to simpler models if 70b fails
  - [ ] Fallback to keyword search if RAG fails
- [ ] Add user-friendly error messages
  - [ ] "Sorry, I couldn't process that PDF"
  - [ ] "The AI service is temporarily unavailable"
- [ ] Log all errors to `llm_usage_logs` and `rag_usage_logs`
- [ ] Test failure scenarios

### Monitoring & Logging
- [ ] Set up structured logging
  - [ ] Use Python logging module
  - [ ] Log to file + console
  - [ ] Include timestamps, user_id, conversation_id
- [ ] Add performance metrics
  - [ ] Track RAG query time
  - [ ] Track LLM response time
  - [ ] Track database query time
- [ ] Track LLM token usage
  - [ ] Monitor costs in `llm_usage_logs`
  - [ ] Set up alerts for high usage
- [ ] Monitor database queries
  - [ ] Slow query log
  - [ ] Connection pool monitoring
- [ ] Set up alerts (optional)
  - [ ] Email on errors
  - [ ] Slack on high costs

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
  - [ ] Document all agent endpoints
  - [ ] Include request/response examples
- [ ] Agent architecture diagram
  - [ ] Show agent flow
  - [ ] Show tool interactions
  - [ ] Show database integration
- [ ] Tool reference guide
  - [ ] List all tools
  - [ ] Document parameters
  - [ ] Show usage examples
- [ ] Deployment guide
  - [ ] Environment setup
  - [ ] Database migration steps
  - [ ] Dependency installation
- [ ] User guide
  - [ ] How to use chat interface
  - [ ] Example queries
  - [ ] Tips for best results

### Security
- [ ] Input sanitization
  - [ ] Validate all user inputs
  - [ ] Prevent prompt injection
- [ ] SQL injection prevention (already using parameterized queries)
- [ ] Rate limiting (already in API)
- [ ] API key rotation
  - [ ] Rotate Groq API key periodically
  - [ ] Use environment variables
- [ ] Audit logging
  - [ ] Log all agent actions
  - [ ] Log all database updates

### Deployment
- [ ] Environment configuration
  - [ ] Production .env file
  - [ ] Set GROQ_API_KEY
  - [ ] Set DATABASE_URL
- [ ] Database migrations
  - [ ] Run 020_agent_system.sql on production
  - [ ] Verify tables created
- [ ] Dependency installation
  - [ ] Install in production .venv
  - [ ] Verify all packages installed
- [ ] Service startup scripts
  - [ ] Systemd service file
  - [ ] Auto-restart on failure
- [ ] Health checks
  - [ ] `/health` endpoint
  - [ ] Check database connection
  - [ ] Check LLM connectivity
- [ ] Rollback plan
  - [ ] Database backup before migration
  - [ ] Code rollback procedure

---

## 🎯 Success Criteria

### Functionality
- ✅ User can upload PDF via chat
- ✅ User can query papers naturally ("What methodology did they use?")
- ✅ User can generate lit review sections ("Generate methodology section")
- ✅ All tabs update without conflicts (comparison, findings, methodology)
- ✅ Real-time progress visible in chat

### Performance
- ✅ Chat response < 3s (non-generation queries)
- ✅ Section generation < 30s
- ✅ RAG query < 2s
- ✅ Concurrent users supported (10+ simultaneous)

### Quality
- ✅ 80%+ test coverage
- ✅ Zero data corruption (transaction safety)
- ✅ Graceful error handling (user-friendly messages)
- ✅ Production-ready logging (structured, searchable)

### User Experience
- ✅ Intuitive chat interface (matches existing UI)
- ✅ Clear progress indicators (tool execution visible)
- ✅ Helpful error messages (actionable)
- ✅ Responsive UI (no lag, smooth animations)

---

## 📊 Progress Tracking

**Current Phase**: Phase 1 ✅ COMPLETED  
**Next Phase**: Phase 2 - Core Components  
**Overall Completion**: ~15%

**Completed**:
- ✅ Database migration (6 tables created)
- ✅ Project structure (agents/, tools/)
- ✅ Configuration (config.py updated)
- ✅ Dependencies (requirements.txt updated)

**In Progress**:
- ⏳ Dependency installation (Docling, Groq, etc.)

**Next Steps**:
1. Complete dependency installation
2. Implement RAG engine with Nomic + Docling
3. Implement LLM client with Groq
4. Create flexible agent base class
5. Build database tools for YOUR tables

---

## 💡 Key Differences from Generic Plan

### What We're NOT Doing:
- ❌ LlamaIndex (too complex, we'll build simpler RAG)
- ❌ Changing embedding model (using YOUR Nomic)
- ❌ New database tables for papers (using YOUR existing tables)
- ❌ Replacing vector search (using YOUR EnhancedVectorService)

### What We're ADDING:
- ✅ Docling for academic PDF parsing (equations, tables, images)
- ✅ Direct integration with YOUR comparison_configs, findings, methodology_data tables
- ✅ Reuse of YOUR Nomic embeddings (768 dims)
- ✅ Lightweight RAG (no heavy framework)
- ✅ Simple, maintainable code

**Ready to proceed to Phase 2?** 🚀
