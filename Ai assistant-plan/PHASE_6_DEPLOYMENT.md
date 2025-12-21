# Phase 6: Deployment & Production

**Duration**: Week 8  
**Goal**: Deploy to production with monitoring and security

---

## 🔍 Current Situation Check

**Before starting this phase, verify Phase 5 is complete**:

```bash
# 1. Verify all tests pass
pytest backend/tests/ -v
# Expected: All tests passing

# 2. Verify test coverage
pytest backend/tests/ --cov=app --cov-report=term
# Expected: 80%+ coverage

# 3. Verify quality metrics
python backend/tests/quality/test_rag_quality.py
# Expected: RAG precision > 0.7

# 4. Verify performance
python backend/tests/performance/test_response_time.py
# Expected: Response time < 3s
```

**✅ You should have**:
- All tests passing
- 80%+ code coverage
- Quality metrics met
- Performance benchmarks met

**❌ If missing, complete Phase 5 first**

---

## ✅ Checklist

### Production Setup
- [ ] Configure environment variables
- [ ] Setup production database
- [ ] Configure Redis
- [ ] Setup monitoring
- [ ] Configure logging

### Security
- [ ] Add rate limiting
- [ ] Add cost budgets
- [ ] Input validation
- [ ] Error handling

### Deployment
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Setup health checks
- [ ] Create rollback plan

---

## 📋 Deployment Steps

### 1. Environment Configuration

Create `backend/.env.production`:

```env
# Database
DATABASE_URL=postgresql://user:pass@prod-db:5432/research_hub

# Groq API
GROQ_API_KEY=your_production_key

# Redis
REDIS_URL=redis://prod-redis:6379/0

# Security
SECRET_KEY=your_secret_key
ALLOWED_ORIGINS=https://yourdomain.com

# Limits
MAX_REQUESTS_PER_MINUTE=10
MAX_COST_PER_USER_MONTHLY=50.00
```

### 2. Production Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations
RUN python manage.py migrate

# Start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - GROQ_API_KEY=${GROQ_API_KEY}
    depends_on:
      - db
      - redis
  
  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 4. Deploy

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f backend
```

---

## 📊 Monitoring Setup

### 1. Add Logging

```python
# backend/app/core/logging_config.py

import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()
```

### 2. Health Check Endpoint

```python
# backend/app/api/v1/health.py

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "database": await check_db(db),
        "redis": await check_redis(),
        "llm": await check_groq_api()
    }
```

---

## 🔒 Security

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/agent/chat")
@limiter.limit("10/minute")
async def chat(...):
    ...
```

### Cost Budget

```python
async def check_budget(user_id: str, db):
    total = await db.execute(
        text("""
            SELECT SUM(cost_usd) FROM llm_usage_logs
            WHERE user_id = :user_id
            AND created_at >= NOW() - INTERVAL '1 month'
        """),
        {'user_id': user_id}
    )
    
    if total > 50:
        raise HTTPException(429, "Monthly budget exceeded")
```

---

## 📝 Deliverables

- ✅ Production deployment
- ✅ Monitoring enabled
- ✅ Security configured
- ✅ Health checks working

---

## 🎉 Project Complete!

Your AI assistant is now live in production!
