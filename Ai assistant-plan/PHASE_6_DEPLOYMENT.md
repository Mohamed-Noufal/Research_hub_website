# Phase 6: Production Deployment

**Duration**: Week 8  
**Goal**: Deploy AI assistant to production with monitoring, security, and documentation

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 5 is complete**:

```bash
# 1. Run all tests
.venv\Scripts\python.exe -m pytest tests/ -v
# Expected: All tests passing

# 2. Check test coverage
.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
# Expected: 80%+ coverage

# 3. Verify no critical bugs
# Review: test results, error logs, manual testing notes

# 4. Check frontend builds
cd frontend
npm run build
# Expected: Build successful
```

**✅ You should have**:
- All tests passing (80%+ coverage)
- No critical bugs
- Frontend builds successfully
- Manual testing complete

**❌ If missing, complete Phase 5 first**

---

## ✅ Checklist

### Production Configuration
- [ ] Set up production `.env` file
- [ ] Configure GROQ_API_KEY
- [ ] Configure DATABASE_URL (production)
- [ ] Set secure SECRET_KEY
- [ ] Configure CORS origins
- [ ] Set rate limits

### Database Migration
- [ ] Backup production database
- [ ] Run migration `020_agent_system.sql`
- [ ] Verify tables created
- [ ] Test rollback procedure

### Dependency Management
- [ ] Freeze requirements (`pip freeze > requirements.txt`)
- [ ] Install in production environment
- [ ] Verify all packages installed
- [ ] Test import statements

### Security Hardening
- [ ] Input sanitization
- [ ] SQL injection prevention (already using parameterized queries)
- [ ] Rate limiting configured
- [ ] API key rotation plan
- [ ] Audit logging enabled

### Monitoring & Logging
- [ ] Set up structured logging
- [ ] Configure log rotation
- [ ] Monitor LLM costs (`llm_usage_logs`)
- [ ] Monitor RAG performance (`rag_usage_logs`)
- [ ] Set up error alerts

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide
- [ ] Admin guide
- [ ] Troubleshooting guide

### Deployment
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates
- [ ] Configure health checks
- [ ] Test production deployment

---

## 📋 Step-by-Step Implementation

### 1. Production Environment Configuration

Create `backend/.env.production`:

```bash
# Database
DATABASE_URL=postgresql://user:password@prod-db-host:5432/research_db

# API Keys
GROQ_API_KEY=your_production_groq_api_key_here
SECRET_KEY=your_very_secure_random_secret_key_here

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Agent Configuration
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT_SECONDS=300
EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/research-assistant/app.log
```

### 2. Database Migration Script

Create `backend/deploy_migration.sh`:

```bash
#!/bin/bash

echo "🚀 Deploying Agent System Migration"
echo "===================================="

# Backup database
echo "1️⃣ Backing up database..."
pg_dump -U postgres research_db > backup_$(date +%Y%m%d_%H%M%S).sql
echo "   ✅ Backup created"

# Run migration
echo "2️⃣ Running migration..."
psql -U postgres research_db < migrations/020_agent_system.sql
echo "   ✅ Migration complete"

# Verify tables
echo "3️⃣ Verifying tables..."
psql -U postgres research_db -c "\dt" | grep -E "paper_chunks|agent_conversations"
echo "   ✅ Tables verified"

echo ""
echo "✅ Deployment complete!"
```

### 3. Production Logging Configuration

Create `backend/app/core/logging_config.py`:

```python
"""
Production logging configuration
Structured logging with rotation
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'conversation_id'):
            log_data['conversation_id'] = record.conversation_id
        
        return json.dumps(log_data)

def setup_logging():
    """Configure production logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', '/var/log/research-assistant/app.log')
    
    # Create logger
    logger = logging.getLogger('research_assistant')
    logger.setLevel(log_level)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler for development
    if os.getenv('ENVIRONMENT') != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()
```

### 4. Health Check Endpoint

Update `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import logger
import os

app = FastAPI(title="Research Assistant API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns system status
    """
    from sqlalchemy import text
    from app.core.database import engine
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    # Check Groq API key
    groq_status = "configured" if os.getenv('GROQ_API_KEY') else "missing"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "groq_api": groq_status,
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    return {"message": "Research Assistant API", "version": "1.0.0"}

# Include routers
from app.api.v1 import agent
app.include_router(agent.router, prefix="/api/v1")
```

### 5. Nginx Configuration

Create `nginx.conf`:

```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:3000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # API endpoints
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # WebSocket
    location /api/v1/agent/ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 6. Systemd Service Files

Create `research-assistant-backend.service`:

```ini
[Unit]
Description=Research Assistant Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/research-assistant/backend
Environment="PATH=/opt/research-assistant/backend/.venv/bin"
ExecStart=/opt/research-assistant/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `research-assistant-frontend.service`:

```ini
[Unit]
Description=Research Assistant Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/research-assistant/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7. Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash

echo "🚀 Deploying Research Assistant"
echo "==============================="

# Pull latest code
echo "1️⃣ Pulling latest code..."
git pull origin main

# Backend deployment
echo "2️⃣ Deploying backend..."
cd backend
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -v
sudo systemctl restart research-assistant-backend
echo "   ✅ Backend deployed"

# Frontend deployment
echo "3️⃣ Deploying frontend..."
cd ../frontend
npm install
npm run build
sudo systemctl restart research-assistant-frontend
echo "   ✅ Frontend deployed"

# Restart nginx
echo "4️⃣ Restarting nginx..."
sudo systemctl restart nginx
echo "   ✅ Nginx restarted"

# Health check
echo "5️⃣ Running health check..."
sleep 5
curl -f http://localhost:8000/health || echo "⚠️ Health check failed"

echo ""
echo "✅ Deployment complete!"
echo "🔗 Visit: https://yourdomain.com"
```

### 8. Monitoring Dashboard

Create `backend/app/api/v1/monitoring.py`:

```python
"""
Monitoring endpoints
Track LLM costs, RAG performance, system health
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/llm-costs")
async def get_llm_costs(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get LLM costs for last N days"""
    result = await db.execute(
        text("""
            SELECT 
                DATE(created_at) as date,
                model,
                COUNT(*) as requests,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost
            FROM llm_usage_logs
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at), model
            ORDER BY date DESC
        """),
        {'days': days}
    )
    
    return [dict(row._mapping) for row in result.fetchall()]

@router.get("/rag-performance")
async def get_rag_performance(
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get RAG query performance metrics"""
    result = await db.execute(
        text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as queries,
                AVG(duration_ms) as avg_duration_ms,
                AVG(chunks_retrieved) as avg_chunks
            FROM rag_usage_logs
            WHERE created_at >= NOW() - INTERVAL ':days days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """),
        {'days': days}
    )
    
    return [dict(row._mapping) for row in result.fetchall()]

@router.get("/system-stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    # Total conversations
    conv_result = await db.execute(
        text("SELECT COUNT(*) FROM agent_conversations")
    )
    total_conversations = conv_result.fetchone()[0]
    
    # Total messages
    msg_result = await db.execute(
        text("SELECT COUNT(*) FROM agent_messages")
    )
    total_messages = msg_result.fetchone()[0]
    
    # Total papers with chunks
    papers_result = await db.execute(
        text("SELECT COUNT(DISTINCT paper_id) FROM paper_chunks")
    )
    total_papers_processed = papers_result.fetchone()[0]
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_papers_processed": total_papers_processed
    }
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Backup created
- [ ] Rollback plan ready

### Deployment
- [ ] Environment variables set
- [ ] Database migrated
- [ ] Dependencies installed
- [ ] Services started
- [ ] Health checks passing

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Check LLM costs
- [ ] Verify RAG performance
- [ ] Test critical workflows
- [ ] User acceptance testing

---

## 📊 Success Metrics

- ✅ Zero downtime deployment
- ✅ All health checks passing
- ✅ Response time < 3s (95th percentile)
- ✅ Error rate < 1%
- ✅ LLM costs within budget
- ✅ User satisfaction > 80%

---

## 🎉 Completion

**Congratulations!** Your AI Research Assistant is now in production!

### What You've Built:
- ✅ RAG engine with LlamaIndex + YOUR Nomic embeddings
- ✅ Docling PDF parsing (equations, tables, images)
- ✅ Flexible agent framework with ReAct pattern
- ✅ Database tools for YOUR existing tables
- ✅ Chat API with WebSocket support
- ✅ React chat UI
- ✅ Comprehensive testing (80%+ coverage)
- ✅ Production deployment

### Next Steps:
1. Monitor system performance
2. Gather user feedback
3. Iterate and improve
4. Add new features as needed

**🚀 Happy researching!**
