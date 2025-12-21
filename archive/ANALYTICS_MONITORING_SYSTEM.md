# Analytics & Monitoring System
## Admin Dashboard for ResearchHub

**Created:** 2025-11-22  
**Purpose:** Comprehensive analytics and monitoring system to track user behavior, app performance, and system health

---

## 📊 **Overview**

Track everything about your app: users, searches, performance, and system health. This enables data-driven decisions and proactive monitoring.

---

## **1. User Analytics**

### **A. User Engagement Metrics**

**What to Track:**
- Total users (daily/weekly/monthly active users - DAU/WAU/MAU)
- New user registrations
- User retention rate (7-day, 30-day)
- Session duration (average time spent)
- Pages per session
- User journey flow (search → results → workspace)

**Database Schema:**
```sql
CREATE TABLE user_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES local_users(id),
    session_id VARCHAR(255),
    event_type VARCHAR(50), -- 'page_view', 'search', 'save', 'export'
    event_data JSONB,
    page_url VARCHAR(500),
    timestamp TIMESTAMP DEFAULT NOW(),
    session_duration INTEGER, -- seconds
    device_type VARCHAR(50), -- 'desktop', 'mobile', 'tablet'
    browser VARCHAR(100)
);

CREATE INDEX idx_user_analytics_user ON user_analytics(user_id);
CREATE INDEX idx_user_analytics_event ON user_analytics(event_type);
CREATE INDEX idx_user_analytics_timestamp ON user_analytics(timestamp);
```

---

### **B. Search Analytics**

**What to Track:**
- Total searches per day/week/month
- Searches per user (average, top users)
- Popular search queries
- Search categories distribution
- Search modes used (auto/quick/ai)
- Search success rate (results found vs no results)
- Average search time
- Cache hit rate
- AI suggestion usage rate

**Database Schema:**
```sql
CREATE TABLE search_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES local_users(id),
    query TEXT,
    category VARCHAR(50),
    mode VARCHAR(20),
    results_count INTEGER,
    search_time FLOAT, -- seconds
    cached BOOLEAN,
    api_calls_made INTEGER,
    sources_used TEXT[],
    timestamp TIMESTAMP DEFAULT NOW(),
    ai_suggestions_used BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_search_analytics_user ON search_analytics(user_id);
CREATE INDEX idx_search_analytics_timestamp ON search_analytics(timestamp);
```

---

### **C. Paper Interaction Analytics**

**What to Track:**
- Papers saved per user
- Papers viewed (detail clicks)
- Papers exported (PDF, citations)
- Most saved papers
- Most viewed papers
- Save rate (saved / viewed)

**Database Schema:**
```sql
CREATE TABLE paper_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES local_users(id),
    paper_id INTEGER REFERENCES papers(id),
    action_type VARCHAR(50), -- 'view', 'save', 'unsave', 'export'
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_paper_analytics_user ON paper_analytics(user_id);
CREATE INDEX idx_paper_analytics_paper ON paper_analytics(paper_id);
```

---

## **2. System Performance Metrics**

### **A. Database Metrics**

**What to Track:**
- Total papers in database
- Papers with embeddings
- Papers added per day
- Database size (GB)
- Embedding queue length
- Average embedding time

**Monitoring Queries:**
```sql
-- Daily stats
SELECT 
    DATE(created_at) as date,
    COUNT(*) as papers_added,
    COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as embedded
FROM papers
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at);

-- Database size
SELECT 
    pg_size_pretty(pg_database_size('research_db')) as db_size;

-- Pending embeddings
SELECT COUNT(*) FROM papers 
WHERE embedding IS NULL AND is_processed = FALSE;
```

---

### **B. API Performance**

**What to Track:**
- API response times (p50, p95, p99)
- API error rates
- External API success/failure
- Rate limit hits
- Timeout occurrences

**Database Schema:**
```sql
CREATE TABLE api_performance (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    status_code INTEGER,
    response_time FLOAT, -- milliseconds
    external_api VARCHAR(50),
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## **3. Admin Dashboard**

### **Dashboard Layout**

```
┌─────────────────────────────────────────────────────┐
│  📊 ResearchHub Admin Dashboard                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Users    │  │ Active   │  │ Searches │         │
│  │  1,234   │  │   456    │  │  12,345  │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Papers   │  │ Avg Time │  │ Cache    │         │
│  │  10,941  │  │   5.3s   │  │   45%    │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  📈 Searches Over Time (30 Days)             │  │
│  │  [Line Chart showing daily search volume]    │  │
│  └──────────────────────────────────────────────┘  │
│                                                      │
│  ┌──────────────────┐  ┌──────────────────────┐   │
│  │ Top Categories   │  │ Most Active Users    │   │
│  │ 1. AI (45%)     │  │ 1. user@example.com  │   │
│  │ 2. Med (30%)    │  │ 2. researcher@edu    │   │
│  │ 3. Agri (15%)   │  │ 3. student@school    │   │
│  └──────────────────┘  └──────────────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │  🏥 System Health                            │  │
│  │  ✅ Database: Healthy                        │  │
│  │  ✅ APIs: All operational                    │  │
│  │  ⚠️  Queue: 150 pending embeddings           │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

### **Key Metrics**

**Real-Time:**
- Current active users
- Searches in last hour
- API response time (5 min)
- Error rate (5 min)

**Daily:**
- New users today
- Total searches today
- Papers added today
- Avg session duration

**Trends:**
- User growth rate
- Search volume trends
- Database growth
- Popular categories

---

## **4. Admin API Endpoints**

```python
# GET /api/v1/admin/analytics/overview
{
  "total_users": 1234,
  "active_users_today": 456,
  "total_searches": 12345,
  "papers_in_db": 10941,
  "avg_search_time": 5.3,
  "cache_hit_rate": 0.45
}

# GET /api/v1/admin/analytics/searches?period=7d
{
  "total_searches": 2345,
  "searches_per_day": [...],
  "top_queries": [...],
  "category_distribution": {...}
}

# GET /api/v1/admin/analytics/users?period=30d
{
  "new_users": 123,
  "active_users": 456,
  "retention_rate": 0.78,
  "top_users": [...]
}

# GET /api/v1/admin/analytics/performance
{
  "api_response_times": {...},
  "error_rates": {...},
  "database_size": "2.5 GB",
  "pending_embeddings": 150
}
```

---

## **5. Monitoring & Alerts**

### **Alert Conditions**

**Critical (Immediate Action):**
- API error rate > 5%
- Database connection failures
- External API downtime
- Disk space < 10%

**Warning (Monitor):**
- Search time > 30s (p95)
- Embedding queue > 1000
- Cache hit rate < 30%
- Memory usage > 80%

**Alert Channels:**
- Email notifications
- Slack/Discord webhooks
- Admin dashboard badges
- SMS for critical

---

## **6. Implementation Plan**

### **Phase 1: Basic Analytics (Week 1-2)**
- [ ] Create analytics tables
- [ ] Add event tracking to frontend
- [ ] Create admin API endpoints
- [ ] Build basic dashboard UI

### **Phase 2: Advanced Metrics (Week 3-4)**
- [ ] Add performance monitoring
- [ ] Real-time dashboards
- [ ] Automated reports
- [ ] Alerting system

### **Phase 3: Optimization (Week 5-6)**
- [ ] Data visualization (charts)
- [ ] Export functionality
- [ ] Custom reports
- [ ] User behavior heatmaps

---

## **7. Privacy & Compliance**

**Data Retention:**
- User analytics: 90 days
- Search analytics: 180 days
- Performance metrics: 30 days
- Error logs: 7 days

**Privacy:**
- Anonymize IP addresses
- Hash user identifiers
- No PII in analytics
- GDPR compliance
- User opt-out option

---

## **8. Quick Start: Minimal Analytics**

Start with these essential metrics:

1. **User Count:** Total and daily active
2. **Search Count:** Total and per user
3. **Database Size:** Papers count and growth
4. **Performance:** Average search time

**Simple Implementation:**
```sql
-- Add to existing tables
ALTER TABLE user_search_history 
  ADD COLUMN search_time FLOAT,
  ADD COLUMN results_count INTEGER;

-- Create analytics view
CREATE VIEW daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(*) as total_searches,
    AVG(search_time) as avg_search_time
FROM user_search_history
GROUP BY DATE(created_at);
```

---

## **9. Dashboard Technologies**

**Stack:**
- **Backend:** FastAPI (existing)
- **Database:** PostgreSQL (existing)
- **Charts:** Chart.js or Recharts
- **Real-time:** WebSockets
- **Export:** CSV, PDF

**Optional:**
- Google Analytics (frontend)
- Sentry (error tracking)
- Grafana (advanced dashboards)

---

## **10. Sample Admin Page Code**

**Frontend Component:**
```tsx
// AdminDashboard.tsx
const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  
  useEffect(() => {
    fetch('/api/v1/admin/analytics/overview')
      .then(res => res.json())
      .then(setStats);
  }, []);
  
  return (
    <div className="admin-dashboard">
      <h1>Admin Dashboard</h1>
      
      <div className="stats-grid">
        <StatCard 
          title="Total Users" 
          value={stats?.total_users} 
        />
        <StatCard 
          title="Active Today" 
          value={stats?.active_users_today} 
        />
        <StatCard 
          title="Total Searches" 
          value={stats?.total_searches} 
        />
      </div>
      
      <SearchChart period="30d" />
      <TopCategories />
      <SystemHealth />
    </div>
  );
};
```

---

## **Summary**

This analytics system provides:
- ✅ Complete user behavior tracking
- ✅ Search performance monitoring
- ✅ System health dashboards
- ✅ Automated alerts
- ✅ Data-driven insights

**Start simple, expand gradually!**
