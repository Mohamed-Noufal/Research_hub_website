# AI-Powered Research Assistant - MVP Development Plan

## 📋 Executive Summary

### Project Vision

Build an AI-powered research platform that helps researchers search, read, and understand academic papers 10x faster by combining multi-source search, PDF management, and RAG-based chat assistance.

### The Problem We're Solving

- Researchers spend 60-70% of time searching and organizing papers
- Tools are fragmented (Google Scholar for search, Mendeley for management, ChatGPT for understanding)
- No single platform combines: Search + Read + AI Chat + Writing

### The Solution

**All-in-one platform** that:

1. **Searches** 3 academic databases (arXiv, Semantic Scholar, OpenAlex)
2. **Displays** papers with PDF viewer and metadata
3. **Chats** intelligently about papers using RAG (Retrieval Augmented Generation)
4. **Saves** papers to personal library
5. **Assists** in writing literature reviews and summaries

### Target Users

- PhD students and researchers
- Literature review writers
- Academic institutions
- Grant proposal authors

---

## 🎯 Core Features (MVP Scope)

### ✅ Must Have (MVP)

1. Multi-source paper search (arXiv + Semantic Scholar + OpenAlex)
2. Search results display with deduplication
3. PDF viewer with paper details
4. RAG-based chat assistant per paper
5. User authentication (JWT)
6. Personal library (save/remove papers)
7. Chat history per paper

### 🔄 Should Have (Phase 2)

- Paper recommendations
- Advanced filters (date, citations, authors)
- Export citations (BibTeX, APA, MLA)
- Collaborative libraries
- Document writer with AI assistance

### 💡 Could Have (Future)

- Browser extension
- Mobile app
- Team workspaces
- Integration with Notion/Obsidian
- Citation graph visualization

---

## 🏗️ Technical Architecture

### System Overview

`┌─────────────┐
│   Frontend  │  React + TypeScript + TailwindCSS
│  (Vercel)   │  
└──────┬──────┘
       │ REST API (JSON)
       ↓
┌─────────────┐
│   Backend   │  FastAPI + Python
│  (Railway)  │  
└──────┬──────┘
       │
       ├──→ PostgreSQL + pgvector (Papers, Users, Embeddings)
       ├──→ Redis (Search cache)
       ├──→ Groq API (LLM for chat)
       └──→ External APIs (arXiv, Semantic Scholar, OpenAlex)`

### Technology Stack

```
LayerTechnologyWhy?FrontendReact 18 + TypeScriptType-safe, modern, large ecosystemStylingTailwindCSSFast development, consistent designState ManagementTanStack Query + ZustandServer state + UI state separationBackendFastAPIAsync, fast, auto API docsDatabasePostgreSQL 15Reliable, supports pgvectorVector DBpgvectorNative Postgres, simple setupCacheRedisFast search result cachingLLMGroq (Llama 3.1 70B)Fastest inference (500+ tok/s), free tierEmbeddingsnomic-embed-text-v1.5Free, 768 dimensions, qualityPDF ProcessingPyMuPDFFast, reliable text extractionDeploymentRailway + VercelEasy, affordable (~$15/month)
```

### Key Design Decisions

**Why pgvector over Chroma/Pinecone?**

- Single database (simpler architecture)
- Transactional consistency
- No extra service to manage
- Easy to migrate later if needed

**Why Groq over OpenAI?**

- 10x faster inference speed
- Generous free tier
- Open-source models (Llama)
- Lower cost at scale

**Why nomic-embed over OpenAI embeddings?**

- Free (no API costs)
- Small size (768 dims = faster search)
- Good quality for academic text
- Can run locally

---

## 📅 8-Week Development Timeline

### Week 1: Project Setup & Infrastructure

**Goal:** Dev environment ready, project structure created

**Tasks:**

- [x]  Install Python 3.11+, Node 18+, PostgreSQL, Redis
- [x]  Create project folder structure (backend + frontend)
- [x]  Setup virtual environment and install dependencies
- [x]  Configure PostgreSQL with pgvector extension
- [x]  Setup environment variables (.env files)
- [x]  Initialize Git repository
- [ ]  Create README with setup instructions

**Deliverable:** ✅ Running empty backend + frontend locally

---

### Week 2: Database & Authentication

**Goal:** Users can register and login

**Backend Tasks:**

- [ ]  Design database schema (5 tables: users, papers, embeddings, user_papers, chat_messages)
- [ ]  Create SQLAlchemy models
- [ ]  Setup Alembic for migrations
- [ ]  Implement JWT authentication
- [ ]  Create user registration endpoint
- [ ]  Create login endpoint
- [ ]  Create "get current user" endpoint
- [ ]  Add password hashing (bcrypt)
- [ ]  Write authentication middleware

**Database Schema:**

`users
├── id (PK)
├── email (unique)
├── hashed_password
├── full_name
└── created_at

papers
├── id (PK)
├── arxiv_id, doi, semantic_scholar_id (unique identifiers)
├── title, abstract, authors (JSON)
├── pdf_url, pdf_text, pdf_path
├── source, citation_count
├── is_processed
└── created_at

embeddings
├── id (PK)
├── paper_id (FK → papers)
├── chunk_text
├── chunk_index
└── vector (pgvector, 768 dimensions)

user_papers
├── id (PK)
├── user_id (FK → users)
├── paper_id (FK → papers)
├── saved_at
└── notes

chat_messages
├── id (PK)
├── user_id (FK → users)
├── paper_id (FK → papers)
├── role (user/assistant)
├── content
└── timestamp`

**Testing:**

- [ ]  Test registration with Postman
- [ ]  Test login returns JWT token
- [ ]  Test protected endpoints require token

**Deliverable:** ✅ Working authentication system

---

### Week 3: Paper Search System

**Goal:** Search 3 APIs and return deduplicated results

**Backend Tasks:**

- [ ]  Create base class for paper sources (abstract interface)
- [ ]  Implement arXiv API service
- [ ]  Implement Semantic Scholar API service
- [ ]  Implement OpenAlex API service
- [ ]  Create unified search service (searches all 3)
- [ ]  Implement deduplication logic (by ID and title)
- [ ]  Create search endpoint (/api/v1/papers/search)
- [ ]  Add Redis caching for search results
- [ ]  Add rate limiting and error handling
- [ ]  Create "get paper by ID" endpoint
- [ ]  Add pagination support

**Search Flow:**

`1. User searches "machine learning"
2. Check Redis cache
3. If miss → Query 3 APIs in parallel (asyncio)
4. Deduplicate results
5. Save new papers to database
6. Cache results (1 hour TTL)
7. Return top 50 papers`

**API Response Format:**

json

`{
  "papers": [...],
  "total": 47,
  "query": "machine learning",
  "sources": ["arxiv", "semantic_scholar", "openalex"]
}`

**Testing:**

- [ ]  Search returns results from all sources
- [ ]  No duplicate papers in results
- [ ]  Cache works (second search is instant)
- [ ]  Handle API failures gracefully

**Deliverable:** ✅ Working multi-source search with caching

---

### Week 4: RAG System (PDF + Embeddings + Chat)

**Goal:** Users can chat with any paper

**Backend Tasks:**

- [ ]  Create PDF download service
- [ ]  Implement text extraction (PyMuPDF)
- [ ]  Create text chunking service (500 tokens, 50 overlap)
- [ ]  Load embedding model (nomic-embed-text-v1.5)
- [ ]  Create embedding service (process paper → chunks → vectors)
- [ ]  Store embeddings in database
- [ ]  Implement vector similarity search (pgvector)
- [ ]  Create RAG service (retrieve + generate)
- [ ]  Integrate Groq API for LLM responses
- [ ]  Create chat endpoint (/api/v1/papers/chat)
- [ ]  Create chat history endpoints
- [ ]  Add background job for embedding (optional)

**RAG Flow:**

`1. User asks: "What is the main contribution?"
2. Embed query with nomic-embed
3. Search top 5 similar chunks (pgvector cosine similarity)
4. Build context: paper metadata + top chunks
5. Send to Groq LLM with prompt
6. Stream response back to user
7. Save chat message to database`

**Prompt Template:**

`You are a research assistant. Answer based on this paper:

Title: {title}
Authors: {authors}
Abstract: {abstract}

Relevant sections:
{chunk_1}
{chunk_2}
...

User question: {user_message}`

**Testing:**

- [ ]  PDF downloads successfully
- [ ]  Text extraction works (test with sample PDF)
- [ ]  Embeddings created (check database)
- [ ]  Chat returns relevant answers
- [ ]  Chat history persists

**Deliverable:** ✅ Working RAG chat system

---

### Week 5: Frontend Core UI

**Goal:** Search page + Paper view page working

**Frontend Tasks:**

- [ ]  Setup React Router (pages: Home, PaperView, Library, Login, Register)
- [ ]  Configure TailwindCSS
- [ ]  Create API client with axios (auth interceptors)
- [ ]  Setup TanStack Query
- [ ]  Create Zustand stores (auth, UI state)
- [ ]  Build authentication pages (Login, Register)
- [ ]  Build Navbar component
- [ ]  Build SearchBar component
- [ ]  Build PaperCard component (shows paper in list)
- [ ]  Create Home page (search + results list)
- [ ]  Add loading states and error handling

**Components:**

`Layout/
├── Navbar (logo, library link, user menu)
├── Footer
└── Sidebar (filters - future)

Search/
├── SearchBar (input + button)
├── PaperCard (title, authors, abstract, actions)
└── SearchFilters (date, source - future)

Common/
├── Button
├── Input
├── Loading
├── Modal
└── ErrorMessage`

**Testing:**

- [ ]  Can register new user
- [ ]  Can login
- [ ]  Can search papers
- [ ]  Results display correctly
- [ ]  Click paper navigates to detail page

**Deliverable:** ✅ Functional search interface

---

### Week 6: Frontend - Paper View & Chat

**Goal:** View PDF and chat with AI

**Frontend Tasks:**

- [ ]  Build PaperView page layout (2 columns: PDF + Chat)
- [ ]  Integrate react-pdf for PDF viewing
- [ ]  Build PaperDetails component (metadata display)
- [ ]  Build ChatPanel component
- [ ]  Build ChatMessage component (user/assistant bubbles)
- [ ]  Build ChatInput component (textarea + send button)
- [ ]  Implement chat API hooks
- [ ]  Add "Save to Library" button
- [ ]  Add loading states for chat
- [ ]  Handle streaming responses (optional)
- [ ]  Add auto-scroll for chat
- [ ]  Style everything with Tailwind

**PaperView Layout:**

`┌─────────────────────────────────────────┐
│          Navbar                          │
├───────────────────┬─────────────────────┤
│                   │  Chat Panel         │
│   PDF Viewer      │  ┌───────────────┐ │
│   (left 60%)      │  │ Messages      │ │
│                   │  │               │ │
│   [Paper Details] │  │ User: ...     │ │
│   Title           │  │ AI: ...       │ │
│   Authors         │  │               │ │
│   Abstract        │  │               │ │
│                   │  └───────────────┘ │
│   [Save] [Export] │  [Input box] [Send]│
└───────────────────┴─────────────────────┘`

**Testing:**

- [ ]  PDF loads and displays
- [ ]  Can send chat messages
- [ ]  AI responds correctly
- [ ]  Chat history persists
- [ ]  Can save paper to library

**Deliverable:** ✅ Complete paper viewing + chat experience

---

### Week 7: Library & Polish

**Goal:** Users can manage saved papers + UI polish

**Frontend Tasks:**

- [ ]  Build Library page
- [ ]  Build LibraryGrid component (card grid)
- [ ]  Add search/filter in library (local)
- [ ]  Add "remove from library" action
- [ ]  Add notes field per paper (optional)
- [ ]  Polish all UI components
- [ ]  Add transitions and animations
- [ ]  Responsive design (mobile-friendly)
- [ ]  Add error boundaries
- [ ]  Add toast notifications (react-hot-toast)
- [ ]  Improve loading states everywhere

**Backend Tasks:**

- [ ]  Create library endpoints (save, get, remove)
- [ ]  Add pagination for library
- [ ]  Optimize database queries (add indexes)
- [ ]  Add API rate limiting
- [ ]  Add request validation everywhere
- [ ]  Write API documentation (Swagger)

**Testing:**

- [ ]  Library loads saved papers
- [ ]  Can remove papers
- [ ]  UI looks good on mobile
- [ ]  All error cases handled
- [ ]  Performance is acceptable

**Deliverable:** ✅ Complete MVP feature set

---

### Week 8: Testing, Deployment & Documentation

**Goal:** Live production app + documentation

**Testing Tasks:**

- [ ]  Write backend unit tests (pytest)
- [ ]  Test all API endpoints
- [ ]  Test authentication flows
- [ ]  Test search with various queries
- [ ]  Test RAG with different papers
- [ ]  Frontend integration testing
- [ ]  Test on multiple browsers
- [ ]  Test on mobile devices
- [ ]  Load testing (handle 100 concurrent users)
- [ ]  Security audit (SQL injection, XSS, etc.)

**Deployment Tasks:**

- [ ]  Setup Railway account
- [ ]  Deploy PostgreSQL on Railway
- [ ]  Deploy Redis on Railway
- [ ]  Deploy backend to Railway
- [ ]  Configure environment variables
- [ ]  Setup Railway volumes for PDF storage
- [ ]  Deploy frontend to Vercel
- [ ]  Configure CORS correctly
- [ ]  Setup custom domain (optional)
- [ ]  Add monitoring (Railway metrics)
- [ ]  Setup error tracking (Sentry - optional)

**Documentation Tasks:**

- [ ]  Write README.md with setup instructions
- [ ]  Document API endpoints
- [ ]  Create user guide (how to use the platform)
- [ ]  Write deployment guide
- [ ]  Document architecture decisions
- [ ]  Add code comments
- [ ]  Create demo video

**Railway Deployment Checklist:**

`1. Create new project
2. Add PostgreSQL plugin
3. Add Redis plugin
4. Add pgvector extension
5. Deploy backend (connect to GitHub)
6. Set environment variables
7. Run migrations
8. Test API endpoints
9. Deploy frontend to Vercel
10. Update CORS origins`

**Deliverable:** ✅ **LIVE MVP** at yourdomain.com

---

## 📊 Success Metrics (MVP Launch)

### Technical Metrics

- Search response time: < 3 seconds
- Chat response time: < 5 seconds
- System uptime: > 99%
- API error rate: < 1%

### User Metrics (First Month)

- 100+ registered users
- 1000+ searches performed
- 500+ papers saved
- 2000+ chat messages sent
- 70%+ user retention (week 2)

### Performance Benchmarks

- Support 100 concurrent users
- Handle 10,000 searches/day
- Store 50,000 papers
- Generate 100,000 embeddings

---

## 💰 Cost Breakdown (Monthly)

```
ServicePlanCostRailway (Backend)Hobby$5Railway (PostgreSQL)2GB$5Railway (Redis)256MB$5Railway (Storage)10GB$2Vercel (Frontend)Free$0Groq APIFree tier$0Total$17/month
```

**Scaling Costs (1000 users):**

- Railway: ~$50/month
- Groq: ~$30/month (after free tier)
- Storage: ~$10/month
- **Total: ~$90/month**

---

## 🚀 Phase 2 Roadmap (Post-MVP)

### Month 2-3: Enhancement

- [ ]  Paper recommendations (similar papers)
- [ ]  Advanced filters (date range, citations, field)
- [ ]  Export citations (BibTeX, APA, MLA)
- [ ]  Document writer (AI-assisted writing)
- [ ]  Better PDF viewer (annotations)
- [ ]  Email notifications
- [ ]  Social features (share papers)

### Month 4-6: Scale

- [ ]  Team workspaces (shared libraries)
- [ ]  Collaborative annotations
- [ ]  Integration with Zotero/Mendeley
- [ ]  Browser extension (save from any site)
- [ ]  Mobile app (React Native)
- [ ]  Payment system (Stripe)
- [ ]  Admin dashboard

### Month 7-12: Advanced Features

- [ ]  Citation graph visualization
- [ ]  Paper summarization
- [ ]  Multi-language support
- [ ]  Voice interaction
- [ ]  Integration with Notion/Obsidian
- [ ]  Research project management
- [ ]  Grant proposal assistant
- [ ]  Thesis writing assistant

---

## 📁 Project Structure

`research-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py              # Auth dependencies
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py      # Login, register
│   │   │       │   ├── search.py    # Paper search
│   │   │       │   ├── chat.py      # RAG chat
│   │   │       │   └── library.py   # Save/remove papers
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py            # Settings
│   │   │   ├── security.py          # JWT, passwords
│   │   │   └── logger.py
│   │   ├── db/
│   │   │   ├── base.py
│   │   │   ├── session.py
│   │   │   └── models/              # SQLAlchemy models
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── services/
│   │   │   ├── paper_sources/
│   │   │   │   ├── base.py
│   │   │   │   ├── arxiv.py
│   │   │   │   ├── semantic_scholar.py
│   │   │   │   └── openalex.py
│   │   │   ├── search_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── pdf_service.py
│   │   │   ├── rag_service.py
│   │   │   └── cache_service.py
│   │   └── utils/
│   ├── main.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── api/                     # API clients
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── search/
│   │   │   ├── paper/
│   │   │   ├── chat/
│   │   │   ├── library/
│   │   │   └── common/
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── pages/                   # Route pages
│   │   ├── store/                   # Zustand stores
│   │   ├── types/                   # TypeScript types
│   │   └── utils/
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md`

## Key Functions & Responsibilities

### Backend Services

**1. SearchService**

- Purpose: Unified paper search across multiple sources
- Functions:
    - `search(query, max_results)` → Search all APIs
    - `_save_papers(results)` → Store in database
    - `_find_existing_paper(result)` → Avoid duplicates

**2. EmbeddingService**

- Purpose: Generate and store vector embeddings
- Functions:
    - `process_paper(paper_id)` → Download PDF, extract text, create embeddings
    - `embed_query(query)` → Generate query vector

**3. RAGService**

- Purpose: Retrieval Augmented Generation for chat
- Functions:
    - `chat(paper_id, message, history)` → Generate AI response
    - `_retrieve_chunks(paper_id, query, top_k)` → Find relevant sections
    - `_build_context(paper, chunks)` → Format prompt
    - `_generate_response(context, message, history)` → Call LLM

**4. PDFService**

- Purpose: Download and extract text from PDFs
- Functions:
    - `download_pdf(url, paper_id)` → Save PDF locally
    - `extract_text(pdf_path)` → Extract all text
    - `_clean_text(text)` → Remove noise

**5. CacheService**

- Purpose: Redis caching for fast results
- Functions:
    - `get_search_results(query)` → Check cache
    - `set_search_results(query, results, ttl)` → Store results

### Frontend Hooks

**1. useAuth**

- Purpose: Handle authentication
- Functions: `login()`, `register()`, `logout()`, `user`, `isLoading`

**2. useSearch**

- Purpose: Search papers
- Functions: `data`, `isLoading`, `error`, `refetch()`

**3. useChat**

- Purpose: Chat with papers
- Functions: `messages`, `sendMessage()`, `clearHistory()`, `isSending`

**4. usePapers**

- Purpose: Manage library
- Functions: `library`, `savePaper()`, `removePaper()`, `isLoading`

---

## 🛠️ Development Tools & Commands

### Backend Commands

bash

`*# Setup*
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

*# Database*
alembic revision --autogenerate -m "message"
alembic upgrade head

*# Run dev server*
uvicorn main:app --reload

*# Tests*
pytest
pytest --cov=app tests/

*# Linting*
black .
flake8`

### Frontend Commands

bash

`*# Setup*
npm install

*# Run dev server*
npm start

*# Build production*
npm run build

*# Tests*
npm test

*# Linting*
npm run lint`

---

## ⚠️ Risk Management

### Technical Risks

**Risk 1: API Rate Limits**

- Impact: Search fails during high traffic
- Mitigation: Aggressive caching, fallback to single source, implement retry logic

**Risk 2: PDF Processing Failures**

- Impact: ~15% of PDFs are scanned/corrupted
- Mitigation: Graceful fallback to abstract-only, show clear error messages

**Risk 3: Embedding Cost/Time**

- Impact: Slow first-time chat experience
- Mitigation: Background processing, show progress indicator, cache embeddings

**Risk 4: LLM Response Quality**

- Impact: Inaccurate or hallucinated answers
- Mitigation: Clear prompts, cite sources, add feedback mechanism

### Operational Risks

**Risk 5: Database Growth**

- Impact: Storage costs increase
- Mitigation: Implement cleanup of old embeddings, compress PDFs

**Risk 6: Deployment Complexity**

- Impact: Hard to deploy for first-time users
- Mitigation: Docker setup, detailed docs, Railway templates

---

## 📝 Best Practices

### Code Quality

- [ ]  Use type hints (Python) and TypeScript
- [ ]  Write docstrings for all functions
- [ ]  Follow PEP 8 (Python) and Airbnb style (JS)
- [ ]  Keep functions under 50 lines
- [ ]  Use meaningful variable names

### Git Workflow

- [ ]  Main branch is production-ready
- [ ]  Feature branches: `feature/search-system`
- [ ]  Commit messages: "feat: add arXiv search"
- [ ]  Pull requests for code review
- [ ]  Tag releases: v1.0.0

### Security

- [ ]  Never commit .env files
- [ ]  Use strong password hashing (bcrypt)
- [ ]  Validate all user inputs
- [ ]  Add SQL injection protection
- [ ]  Implement rate limiting
- [ ]  Use HTTPS in production

### Performance

- [ ]  Index database columns (title, arxiv_id, etc.)
- [ ]  Use pagination for large results
- [ ]  Lazy load images and PDFs
- [ ]  Cache search results
- [ ]  Optimize bundle size

---

## ✅ Launch Checklist

### Pre-Launch (Week 8)

- [ ]  All features working
- [ ]  No critical bugs
- [ ]  Mobile responsive
- [ ]  Performance acceptable (< 3s load)
- [ ]  Security audit passed
- [ ]  Database backed up
- [ ]  Monitoring setup
- [ ]  Error tracking configured

### Launch Day

- [ ]  Deploy to production
- [ ]  Test all features in production
- [ ]  Announce to beta users
- [ ]  Monitor errors closely
- [ ]  Have rollback plan ready


## we need to convert the "" to :

__React Query Conversion:__

- 🚀 Optional future enhancement
- 🚀 Even better performance
- 🚀 More maintainable code
- 🚀 Industry best practice

### __💡 The Perfect Migration Strategy:__

1. __Phase 1 ✅ DONE:__ Fix critical performance issues
2. __Phase 2 🚀 NEXT:__ Convert one component at a time to React Query
3. __Phase 3 🚀 FUTURE:__ Complete migration when beneficial

### __🎯 Bottom Line:__

__You have a fully functional, high-performance research platform right now__ with industry-standard fixes applied. The React Query conversion is a "nice-to-have" enhancement that can happen incrementally over time.
