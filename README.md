# 🔍 AI-Powered Research Paper Search
          
**Intelligent semantic search across 9 academic databases with AI query enhancement** 
               
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-FF6B35?style=flat)](https://github.com/pgvector/pgvector)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Groq](https://img.shields.io/badge/Groq-FF6B35?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJDMTMuMSAyIDE0IDIuOSAxNCA0VjIwQzE0IDIxLjEgMTMuMSAyMiAxMiAyMkg0QzIuOSAyMiAyIDIxLjEgMiAyMFY0QzIgMi45IDIuOSAyIDQgMkgxMkMxMy4xIDIgMTQgMi45IDE0IDRWNFoiIGZpbGw9IiNGRjZCMzUiLz4KPHBhdGggZD0iTTE4IDhIMTZWMTAuNUMxNiAxMS42IDE2LjkgMTIuNSAxOCA5QzE5LjEgMTIuNSAyMCAxMS42IDIwIDEwLjVWMTAuNUMyMCA5LjQgMTkuMSAxOCA5IDE4SDE4VjE2SDE2VjE4SDE4VjE2WiIgZmlsbD0id2hpdGUiLz4KPC9zdmc+)](https://groq.com)
    
A comprehensive research paper search platform that combines traditional keyword search with cutting-edge AI semantic search, powered by PostgreSQL + pgvector for enterprise-grade vector similarity search across **9 academic databases** and **6 research categories**.
    
## ✨ Features

### 🔍 **Intelligent Search System**
- **Category-Based Search**: 6 specialized research domains with optimized sources
- **Dual Search Modes**: Auto-detect between quick keyword and AI-enhanced search
- **AI Query Expansion**: Groq-powered intelligent query understanding
- **Enhanced Embeddings**: Title + authors + abstract for richer semantic search

### 🧠 **AI-Powered Intelligence**
- **Query Analysis**: AI understands research intent and context
- **Smart Term Generation**: Creates multiple academic search strategies
- **Domain Recognition**: Automatically detects research categories
- **Fallback Handling**: Graceful degradation when AI services fail

### 🗄️ **Enterprise Database**
- **PostgreSQL + pgvector**: Native vector operations for high performance
- **ACID Compliance**: Full transactional support and data integrity
- **Scalable Architecture**: Handles millions of papers efficiently
- **Enhanced Indexing**: Optimized for both keyword and vector search

### 🌐 **Comprehensive Multi-Source Integration (9 Databases)**
- **arXiv**: Computer science and physics preprints
- **Semantic Scholar**: AI-powered academic literature search
- **OpenAlex**: Open catalog of scholarly works (100M+ papers)
- **PubMed**: Biomedical and life sciences literature
- **Europe PMC**: European life sciences and biomedical research
- **Crossref**: DOI registration and metadata (50M+ works)
- **ERIC**: Education resources and research
- **CORE**: Open access research papers
- **bioRxiv**: Biology preprints and manuscripts

### 📊 **Research Categories (6 Domains)**
- **AI & Computer Science**: arXiv, Semantic Scholar, OpenAlex
- **Medicine & Biology**: PubMed, Europe PMC, Crossref
- **Engineering & Physics**: arXiv, OpenAlex, Crossref
- **Agriculture & Animal Science**: OpenAlex, CORE, Crossref
- **Humanities & Social Sciences**: ERIC, OpenAlex, CORE
- **Economics & Business**: OpenAlex, CORE, Crossref

### 🎨 **Modern UI/UX**
- **React 19 + TypeScript**: Latest frontend technologies
- **TailwindCSS 4**: Modern utility-first styling
- **Responsive Design**: Optimized for all devices
- **Real-time Search**: Instant results with intelligent caching
- **Category Selection**: User-friendly research domain picker
- **Loading States**: Comprehensive progress indicators

### 🔧 **Developer Experience**
- **Comprehensive Debug System**: Real-time logging and API monitoring
- **Health Checks**: System status and performance metrics
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Docker Deployment**: One-command setup and scaling
- **Testing Suite**: Automated verification and health reports

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (recommended)
- **Python 3.9+** (for local development)
- **Node.js 16+** (for frontend development)
- **Git**

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/Mohamed-Noufal/paper-search.git
cd paper-search

# Start everything with Docker
docker-compose up -d

# Wait for PostgreSQL to initialize (30-60 seconds)
# Then start the backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the frontend
cd frontend
npm install
npm run dev
```

**🎉 Your AI-powered paper search is now running at:**
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 Detailed Setup

### Option 1: Docker (Recommended)

```bash
# 1. Start PostgreSQL + pgvector
docker-compose up -d

# 2. Install backend dependencies
cd backend
pip install -r requirements.txt

# 3. Start backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Install frontend dependencies
cd ../frontend
npm install

# 5. Start frontend development server
npm run dev
```

### Option 2: Local Development

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Database Setup
```bash
# PostgreSQL with Docker
docker run --name postgres-paper-search \
  -e POSTGRES_DB=research_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:15

# Install pgvector extension
docker exec -it postgres-paper-search psql -U postgres -d research_db -c "CREATE EXTENSION vector;"
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/research_db

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# External APIs (optional)
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
OPENALEX_EMAIL=your-email@example.com

# Debug Settings
DEBUG_MODE=true
DEBUG_LOG_LEVEL=DEBUG
```

### Docker Configuration

The `docker-compose.yml` includes:
- **PostgreSQL 15** with pgvector extension
- **Persistent storage** for database data
- **Automatic initialization** scripts
- **Health checks** for service monitoring

## 🎯 Usage Examples

### Category-Based Search
```bash
# AI & Computer Science search
curl "http://localhost:8000/api/v1/papers/search?query=machine%20learning&category=ai_cs&limit=10"

# Medicine & Biology search
curl "http://localhost:8000/api/v1/papers/search?query=cancer%20research&category=medicine_biology&limit=10"

# Engineering & Physics search
curl "http://localhost:8000/api/v1/papers/search?query=quantum%20computing&category=engineering_physics&limit=10"
```

### AI-Enhanced Search
```bash
# AI analyzes and expands your query across category sources
curl "http://localhost:8000/api/v1/papers/search?query=detection%20unhealthy%20goat%20using%20deep%20learning&category=agriculture_animal&mode=ai"
```

### Debug Mode with Categories
```bash
# See detailed search process with category-specific sources
curl "http://localhost:8000/api/v1/papers/search/debug?query=neural%20networks&category=ai_cs&limit=3"
```

### Get Available Categories
```bash
# List all research categories and their sources
curl "http://localhost:8000/api/v1/papers/categories"
```

## 📚 API Documentation

### Endpoints

#### Unified Search
```http
GET /api/v1/papers/search
```

**Parameters:**
- `query` (string, required): Search query or natural language question
- `category` (string, required): Research category (ai_cs, medicine_biology, etc.)
- `mode` (string): Search mode - "auto" (default), "quick", or "ai"
- `limit` (int): Maximum results (1-100, default: 100)

**Smart Features:**
- **Auto Mode**: Automatically detects if query needs AI or quick search
- **Quick Mode**: Fast keyword search with cascading fallback
- **AI Mode**: Intelligent query expansion for research discovery

#### Get Categories
```http
GET /api/v1/papers/categories
```

Returns all available research categories with their associated sources and descriptions.

#### System Health
```http
GET /api/v1/papers/health
```

Returns operational status of all integrated academic sources.

#### Database Stats
```http
GET /api/v1/papers/stats
```

Returns paper counts by source and processing statistics.

#### Clear Cache
```http
DELETE /api/v1/papers/cache
```

Clears the search cache (admin endpoint).

#### Generate Embeddings
```http
POST /api/v1/papers/embeddings/generate
```

**Parameters:**
- `max_papers` (int): Maximum papers to process (1-10000)
- `batch_size` (int): Processing batch size (10-200)
- `force_regenerate` (boolean): Regenerate existing embeddings

Generates enhanced embeddings combining title, authors, and abstract.

#### Embedding Statistics
```http
GET /api/v1/papers/embeddings/stats
```

Returns embedding coverage, version distribution, and processing status.

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest
```

### API Testing
```bash
# Health check
curl http://localhost:8000/api/v1/papers/health

# Search test
curl "http://localhost:8000/api/v1/papers/search?query=test&limit=1"

# Database stats
curl http://localhost:8000/api/v1/papers/stats
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (React 19)    │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│                 │    │                 │    │   + pgvector    │
│ • Category UI   │    │ • AI Analyzer   │    │ • Papers Table  │
│ • Smart Search  │    │ • Multi-Source  │    │ • Embeddings    │
│ • Results View  │    │ • Vector Search │    │ • Categories    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                   ┌─────────────────┐
                   │ Academic APIs   │
                   │ (9 Databases)   │
                   │ • arXiv         │
                   │ • Semantic      │
                   │   Scholar       │
                   │ • OpenAlex      │
                   │ • PubMed        │
                   │ • Europe PMC    │
                   │ • Crossref      │
                   │ • ERIC          │
                   │ • CORE          │
                   │ • bioRxiv       │
                   └─────────────────┘
```

### Key Components

#### AI Query Analyzer
- Uses Groq LLM for intelligent query understanding
- Generates multiple academic search terms
- Handles fallback for API failures

#### Vector Service
- Manages embeddings generation and storage
- Performs vector similarity search
- Optimized for PostgreSQL + pgvector

#### Search Service
- Orchestrates multi-source search
- Handles deduplication and ranking
- Manages caching and performance

## 🔧 Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/app/api/v1/papers.py`
2. **Frontend**: Update components in `frontend/src/`
3. **Database**: Modify models in `backend/app/models/`
4. **Services**: Add logic in `backend/app/services/`

### Code Style

- **Backend**: Black formatting, type hints required
- **Frontend**: ESLint, Prettier, TypeScript strict mode
- **Commits**: Conventional commits format

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **pgvector** for enterprise-grade vector database capabilities
- **Sentence Transformers** for high-quality embedding generation
- **Academic Databases**: arXiv, Semantic Scholar, OpenAlex, PubMed, Europe PMC, Crossref, ERIC, CORE, bioRxiv
- **Groq** for fast, reliable AI query analysis
- **FastAPI** for modern, high-performance API development
- **React** for excellent frontend development experience
- **PostgreSQL** for robust, scalable data management

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Mohamed-Noufal/paper-search/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Mohamed-Noufal/paper-search/discussions)

---

**Built with ❤️ for the research community**





































