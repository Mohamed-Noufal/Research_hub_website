# Search History Feature Implementation Plan

## Overview
Save search sessions to workspace history so users can:
- View their search history
- Click to return to previous search results
- Track search patterns

---

## Backend Implementation

### 1. Database Schema (Already Exists!)
```sql
-- user_search_history table
CREATE TABLE user_search_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES local_users(id),
    query TEXT,
    category VARCHAR(50),
    results_count INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. API Endpoints Needed

**Save Search to History:**
```python
POST /api/v1/users/search-history
{
  "query": "machine learning",
  "category": "ai_cs",
  "results_count": 20
}
```

**Get Search History:**
```python
GET /api/v1/users/search-history
Response: [
  {
    "id": 1,
    "query": "machine learning",
    "category": "ai_cs",
    "results_count": 20,
    "created_at": "2025-11-22T15:30:00"
  },
  ...
]
```

**Restore Search Session:**
```python
GET /api/v1/users/search-history/{id}
Response: {
  "query": "machine learning",
  "category": "ai_cs",
  "papers": [...] // Re-run the search
}
```

---

## Frontend Implementation

### 1. Save Search When Results Load
```tsx
// In SearchResults.tsx
useEffect(() => {
  if (searchData && searchData.papers.length > 0) {
    // Save to history
    usersApi.saveSearchHistory({
      query: searchQuery,
      category: searchCategory,
      results_count: searchData.total
    });
  }
}, [searchData]);
```

### 2. Display History in Workspace
```tsx
// In Workspace.tsx - Add new tab
<Tabs>
  <Tab>Saved Papers</Tab>
  <Tab>Notes</Tab>
  <Tab>Search History</Tab> {/* NEW */}
</Tabs>

// Search History Tab
<SearchHistoryList>
  {history.map(item => (
    <HistoryItem
      query={item.query}
      category={item.category}
      resultsCount={item.results_count}
      date={item.created_at}
      onClick={() => restoreSearch(item.id)}
    />
  ))}
</SearchHistoryList>
```

### 3. Restore Search Session
```tsx
const restoreSearch = async (historyId) => {
  // Navigate back to results with saved query
  const history = await usersApi.getSearchHistory(historyId);
  onSearch(history.query, history.category);
  onNavigate('results');
};
```

---

## Implementation Steps

### Phase 1: Backend (30 min)
1. Add search history endpoints to `users.py`
2. Add methods to `UserService`
3. Test with curl/Postman

### Phase 2: Frontend (45 min)
1. Add search history API calls to `users.ts`
2. Auto-save search when results load
3. Add "Search History" tab to Workspace
4. Implement restore functionality

### Phase 3: Polish (15 min)
1. Add loading states
2. Add "Clear History" button
3. Show search date/time
4. Add search result preview

---

## Benefits

✅ **User Experience:**
- Easy to revisit previous searches
- Track research progress
- Quick access to past results

✅ **Analytics:**
- See what users search for
- Identify popular topics
- Improve search suggestions

✅ **Productivity:**
- No need to remember search terms
- Quick iteration on searches
- Research session continuity

---

## Example UI

```
┌─────────────────────────────────────────┐
│  Workspace > Search History             │
├─────────────────────────────────────────┤
│                                          │
│  🔍 machine learning                     │
│     AI & CS • 20 results • 2 hours ago   │
│     [View Results]                       │
│                                          │
│  🔍 detection unhealthy goat             │
│     AI & CS • 15 results • 5 hours ago   │
│     [View Results]                       │
│                                          │
│  🔍 climate change agriculture           │
│     Agriculture • 30 results • 1 day ago │
│     [View Results]                       │
│                                          │
│  [Clear All History]                     │
└─────────────────────────────────────────┘
```

---

## Next Steps

Would you like me to:
1. ✅ Implement the backend endpoints
2. ✅ Add frontend integration
3. ✅ Create the workspace history tab

This will give users a complete search history feature integrated into their workspace!
