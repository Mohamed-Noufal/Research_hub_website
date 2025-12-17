# Phase 7: Production Deployment & Security
## Authentication, Monitoring, and Go-Live

**Timeline:** Week 12 (~36 hours)  
**Priority:** CRITICAL - Must have before launch  
**Impact:** Security, reliability, scalability

---

## 🎯 **Phase 7 Objectives**

1. JWT authentication system
2. Rate limiting and cost control
3. Monitoring and error tracking
4. Production deployment
5. Backup and disaster recovery

---

## 🔐 **Task 7.1: Authentication System** (16 hours)

### **Backend Implementation:**

```python
# backend/app/core/security.py
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash password"""
    return pwd_context.hash(password)
```

```python
# backend/app/api/v1/auth.py
@router.post("/auth/register")
async def register(
    email: str,
    password: str,
    name: str,
    db: Session = Depends(get_db)
):
    """Register new user"""
    # Check if user exists
    existing = db.query(LocalUser).filter(LocalUser.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = LocalUser(
        email=email,
        hashed_password=get_password_hash(password),
        name=name
    )
    db.add(user)
    db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login")
async def login(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Login user"""
    user = db.query(LocalUser).filter(LocalUser.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
```

### **Frontend Implementation:**

```typescript
// frontend/src/contexts/AuthContext.tsx
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('token')
  );
  
  const login = async (email: string, password: string) => {
    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    const data = await response.json();
    setToken(data.access_token);
    localStorage.setItem('token', data.access_token);
  };
  
  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

**Dependencies:**
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

---

## ⏱️ **Task 7.2: Rate Limiting** (4 hours)

```python
# backend/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to expensive endpoints
@router.post("/ai-tools/detect")
@limiter.limit("10/hour")
async def detect_ai_content(request: Request, text: str):
    """Rate limited AI detection"""
```

**Dependencies:**
```bash
pip install slowapi
```

---

## 📊 **Task 7.3: Monitoring & Logging** (8 hours)

### **Sentry for Error Tracking:**

```python
# backend/app/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=1.0
)
```

### **Structured Logging:**

```python
# backend/app/core/logging.py
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)
```

**Dependencies:**
```bash
pip install sentry-sdk python-json-logger
```

---

## 🚀 **Task 7.4: Deployment** (8 hours)

### **Railway Deployment:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### **Environment Variables:**

```bash
# .env.production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET_KEY=...
SENTRY_DSN=...
GROQ_API_KEY=...
OPENAI_API_KEY=...
```

### **Docker Configuration:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 💾 **Task 7.5: Backup & Recovery** (Optional)

### **Automated Database Backups:**

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://your-bucket/backups/
```

### **Backup Schedule:**
- Daily backups (keep 7 days)
- Weekly backups (keep 4 weeks)
- Monthly backups (keep 12 months)

---

## ✅ **Success Criteria**

- [ ] Authentication works (register, login, logout)
- [ ] Protected endpoints require auth
- [ ] Rate limiting prevents abuse
- [ ] Sentry captures errors
- [ ] Logs are structured and searchable
- [ ] App deployed to Railway
- [ ] Environment variables configured
- [ ] Database backups automated
- [ ] Uptime > 99.9%

---

## 🎉 **Go-Live Checklist**

### **Before Launch:**
- [ ] All tests pass
- [ ] Security audit complete
- [ ] Performance tested
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Documentation updated
- [ ] Domain configured
- [ ] SSL certificate active

### **After Launch:**
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Review user feedback
- [ ] Plan next features

---

**Total Time:** ~36 hours  
**Total Cost:** $20-50/month (infrastructure)  
**Impact:** Production-ready, secure, scalable app! 🚀
