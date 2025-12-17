# 🔌 Frontend-Backend Integration Status

**Last Updated:** 2025-11-21  
**Status:** ⚠️ **DISCONNECTED** - Frontend and Backend are NOT integrated

---

## 📊 Executive Summary

The project has a **fully functional backend** with comprehensive API endpoints and a **beautiful frontend UI**, but they are **completely disconnected**. All frontend components are using **mock data** and making **zero API calls** to the backend.

### Current State
- ✅ **Backend**: 100% functional with 9 academic databases integrated
- ✅ **Database**: PostgreSQL + pgvector with complete schema
- ✅ **Services**: Search, user library, notes, literature review all working
- ❌ **Frontend**: Beautiful UI but using only mock/hardcoded data
- ❌ **Integration**: No API client, no HTTP requests, no data fetching

---

## 🎯 What Works (Backend)

### ✅ Fully Implemented Backend APIs

#### 1. **Paper Search API** (`/api/v1/papers/`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/search` | GET | ✅ Working | Unified search across 9 databases with AI enhancement |
| `/categories` | GET | ✅ Working | Get all research categories and their sources |
| `/health` | GET | ✅ Working | Health check for all academic sources |
| `/stats` | GET | ✅ Working | Database statistics and paper counts |
| `/cache` | DELETE | ✅ Working | Clear search cache |
| `/embeddings/generate` | POST | ✅ Working | Generate embeddings for semantic search |
| `/embeddings/stats` | GET | ✅ Working | Embedding coverage and statistics |

**Search Features:**
- **Category-based search**: 6 specialized research domains
- **Dual modes**: Quick keyword search + AI-enhanced search
- **Multi-source**: arXiv, Semantic Scholar, OpenAlex, PubMed, Europe PMC, Crossref, ERIC, CORE, bioRxiv
- **Semantic search**: Vector similarity with pgvector
- **Caching**: Redis-based result caching
- **Deduplication**: Smart paper merging across sources

#### 2. **User Library API** (`/api/v1/users/`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/init` | POST | ✅ Working | Initialize local user (no auth required) |
| `/papers/save` | POST | ✅ Working | Save paper to library with tags/notes |
| `/papers/unsave/{id}` | DELETE | ✅ Working | Remove paper from library |
| `/papers/saved` | GET | ✅ Working | Get all saved papers with metadata |
| `/papers/{id}/saved` | GET | ✅ Working | Check if paper is saved |

**Library Features:**
- Personal paper collections
- Tags and categorization
- Personal notes per paper
- Read status tracking
- Star ratings

#### 3. **Notes API** (`/api/v1/users/notes/`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/` | POST | ✅ Working | Create new note |
| `/{id}` | PUT | ✅ Working | Update existing note |
| `/` | GET | ✅ Working | Get all notes (with hierarchy) |
| `/{id}` | DELETE | ✅ Working | Delete note |
| `/hierarchy` | GET | ✅ Working | Get notes with folder structure |
| `/folders` | POST | ✅ Working | Create folder |
| `/files` | POST | ✅ Working | Create note file in folder |
| `/{id}/rename` | PUT | ✅ Working | Rename note/folder |
| `/{id}/move` | PUT | ✅ Working | Move to different folder |
| `/{id}/delete-recursive` | DELETE | ✅ Working | Delete with all contents |

**Notes Features:**
- Hierarchical folder structure
- Markdown/HTML/plain text support
- Paper-linked notes
- Full CRUD operations
- Recursive operations

#### 4. **Literature Review API** (`/api/v1/users/reviews/`)

| Endpoint | Method | Status | Description |
|----------|--------|--------|-------------|
| `/` | POST | ✅ Working | Create literature review project |
| `/` | GET | ✅ Working | Get all reviews |
| `/{id}` | PUT | ✅ Working | Update review |
| `/{id}` | DELETE | ✅ Working | Delete review |

**Review Features:**
- Multi-paper review projects
- Title and description
- Paper collection management
- Timestamps and versioning

### ✅ Database Schema (Complete)

```sql
-- Papers table with vector embeddings
papers (
  id, arxiv_id, doi, semantic_scholar_id, openalex_id,
  title, abstract, authors (JSON), publication_date,
  pdf_url, pdf_text, source, citation_count, venue,
  embedding (vector 768), is_processed, date_added
)

-- User system (no authentication required)
local_users (
  id (UUID), created_at, last_active, device_info (JSON)
)

-- User's saved papers
user_saved_papers (
  id, user_id, paper_id, saved_at,
  tags (array), personal_notes, read_status, rating
)

-- User's notes with hierarchy
user_notes (
  id, user_id, paper_id, title, content, content_type,
  parent_id, path, is_folder, level,
  created_at, updated_at
)

-- Literature review projects
user_literature_reviews (
  id, user_id, title, description,
  paper_ids (array), created_at, updated_at
)

-- Search history
user_search_history (
  id, user_id, query, category, results_count, searched_at
)

-- User uploads
user_uploads (
  id, user_id, filename, file_path, file_type,
  file_size, uploaded_at, processed_at
)
```

### ✅ Services (Fully Implemented)

1. **UnifiedSearchService**
   - Multi-source academic search
   - AI query analysis with Groq
   - Semantic reranking
   - Cascading fallback
   - Result caching

2. **UserService**
   - Library management
   - Notes CRUD with hierarchy
   - Literature review management
   - Search history tracking

3. **EnhancedVectorService**
   - Embedding generation
   - Vector similarity search
   - Batch processing

4. **Individual Source Services**
   - ArXivService
   - SemanticScholarService
   - OpenAlexService
   - PubMedService
   - EuropePMCService
   - CrossRefService
   - ERICService
   - COREService
   - bioRxivService

---

## ❌ What's Missing (Frontend Integration)

### 1. **No API Client**

**Current State:**
```typescript
// App.tsx - All data is mock/local state
const [savedPapers, setSavedPapers] = useState<Paper[]>([]);
```

**What's Needed:**
```typescript
// src/api/client.ts - MISSING
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

export default apiClient;
```

### 2. **No Environment Configuration**

**Missing File:** `frontend/.env`
```bash
VITE_API_URL=http://localhost:8000
VITE_API_VERSION=v1
```

### 3. **No Data Fetching Hooks**

**Current State:**
```typescript
// SearchResults.tsx - Using mock data
const mockPapers: Paper[] = useMemo(() => {
  return Array.from({ length: 10 }, (_, i) => ({
    id: `paper-${i}`,
    title: `Machine Learning Techniques...`,
    // ... all hardcoded
  }));
}, [searchQuery]);
```

**What's Needed:**
```typescript
// src/hooks/useSearch.ts - MISSING
export const useSearch = (query: string, category: string) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true);
      try {
        const response = await apiClient.get('/api/v1/papers/search', {
          params: { query, category, limit: 20 }
        });
        setData(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [query, category]);

  return { data, loading, error };
};
```

### 4. **No API Integration in Components**

#### SearchPage.tsx
- ❌ Categories are hardcoded
- ❌ No API call to `/api/v1/papers/categories`
- ❌ Search only updates local state

#### SearchResults.tsx
- ❌ All papers are mock data
- ❌ No API call to `/api/v1/papers/search`
- ❌ Save/unsave doesn't call backend

#### Workspace.tsx
- ❌ Saved papers from local state only
- ❌ No API call to `/api/v1/users/papers/saved`
- ❌ Notes are mock data
- ❌ No integration with notes API

### 5. **No User Session Management**

**What's Needed:**
```typescript
// src/hooks/useUser.ts - MISSING
export const useUser = () => {
  const [userId, setUserId] = useState<string | null>(
    localStorage.getItem('userId')
  );

  useEffect(() => {
    const initUser = async () => {
      if (!userId) {
        const response = await apiClient.post('/api/v1/users/init');
        const newUserId = response.data.user_id;
        localStorage.setItem('userId', newUserId);
        setUserId(newUserId);
      }
    };
    initUser();
  }, []);

  return { userId };
};
```

---

## 🔧 Required Changes

### Phase 1: Setup API Client (1-2 hours)

1. **Create API client**
   ```bash
   mkdir -p frontend/src/api
   touch frontend/src/api/client.ts
   touch frontend/src/api/papers.ts
   touch frontend/src/api/users.ts
   ```

2. **Install dependencies**
   ```bash
   cd frontend
   npm install axios react-query
   ```

3. **Configure environment**
   ```bash
   echo "VITE_API_URL=http://localhost:8000" > .env
   ```

### Phase 2: Create Data Fetching Hooks (2-3 hours)

Create these hooks:
- `useSearch` - Search papers
- `useUser` - User session
- `useSavedPapers` - Library management
- `useNotes` - Notes CRUD
- `useLiteratureReviews` - Review management

### Phase 3: Update Components (3-4 hours)

1. **SearchPage.tsx**
   - Fetch categories from `/api/v1/papers/categories`
   - Call search API on submit
   - Handle loading/error states

2. **SearchResults.tsx**
   - Replace mock data with `useSearch` hook
   - Implement save/unsave with API calls
   - Add pagination support

3. **Workspace.tsx**
   - Fetch saved papers from API
   - Integrate notes API
   - Connect literature review endpoints

### Phase 4: State Management (2-3 hours)

1. **Setup React Query**
   ```typescript
   // App.tsx
   import { QueryClient, QueryClientProvider } from 'react-query';
   
   const queryClient = new QueryClient();
   
   function App() {
     return (
       <QueryClientProvider client={queryClient}>
         {/* ... */}
       </QueryClientProvider>
     );
   }
   ```

2. **Add optimistic updates**
3. **Implement cache invalidation**

### Phase 5: Error Handling & UX (2-3 hours)

1. **Add toast notifications**
2. **Implement retry logic**
3. **Add offline support**
4. **Loading skeletons**

---

## 📝 Detailed Implementation Guide

### Step 1: Create API Client

**File:** `frontend/src/api/client.ts`
```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const userId = localStorage.getItem('userId');
    if (userId) {
      config.headers['X-User-ID'] = userId;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
```

### Step 2: Create Papers API Module

**File:** `frontend/src/api/papers.ts`
```typescript
import apiClient from './client';

export const papersApi = {
  search: async (query: string, category: string, mode = 'auto', limit = 20) => {
    const response = await apiClient.get('/api/v1/papers/search', {
      params: { query, category, mode, limit }
    });
    return response.data;
  },

  getCategories: async () => {
    const response = await apiClient.get('/api/v1/papers/categories');
    return response.data;
  },

  getStats: async () => {
    const response = await apiClient.get('/api/v1/papers/stats');
    return response.data;
  },

  healthCheck: async () => {
    const response = await apiClient.get('/api/v1/papers/health');
    return response.data;
  }
};
```

### Step 3: Create Users API Module

**File:** `frontend/src/api/users.ts`
```typescript
import apiClient from './client';

export const usersApi = {
  initUser: async () => {
    const response = await apiClient.post('/api/v1/users/init');
    return response.data;
  },

  savePaper: async (paperId: number, tags?: string[], notes?: string) => {
    const response = await apiClient.post('/api/v1/users/papers/save', {
      paper_id: paperId,
      tags,
      personal_notes: notes
    });
    return response.data;
  },

  unsavePaper: async (paperId: number) => {
    const response = await apiClient.delete(`/api/v1/users/papers/unsave/${paperId}`);
    return response.data;
  },

  getSavedPapers: async () => {
    const response = await apiClient.get('/api/v1/users/papers/saved');
    return response.data;
  },

  // Notes
  createNote: async (data: { paper_id?: number; title?: string; content: string }) => {
    const response = await apiClient.post('/api/v1/users/notes', data);
    return response.data;
  },

  getNotes: async (paperId?: number) => {
    const response = await apiClient.get('/api/v1/users/notes', {
      params: { paper_id: paperId }
    });
    return response.data;
  },

  getNotesHierarchy: async () => {
    const response = await apiClient.get('/api/v1/users/notes/hierarchy');
    return response.data;
  },

  // Literature Reviews
  createReview: async (data: { title: string; description?: string; paper_ids?: number[] }) => {
    const response = await apiClient.post('/api/v1/users/reviews', data);
    return response.data;
  },

  getReviews: async () => {
    const response = await apiClient.get('/api/v1/users/reviews');
    return response.data;
  }
};
```

### Step 4: Create Custom Hooks

**File:** `frontend/src/hooks/useSearch.ts`
```typescript
import { useState, useEffect } from 'react';
import { papersApi } from '../api/papers';

export const useSearch = (query: string, category: string, enabled = true) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!enabled || !query || !category) return;

    const fetchResults = async () => {
      setLoading(true);
      setError(null);
      try {
        const results = await papersApi.search(query, category);
        setData(results);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [query, category, enabled]);

  return { data, loading, error };
};
```

**File:** `frontend/src/hooks/useUser.ts`
```typescript
import { useState, useEffect } from 'react';
import { usersApi } from '../api/users';

export const useUser = () => {
  const [userId, setUserId] = useState<string | null>(
    localStorage.getItem('userId')
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initUser = async () => {
      if (!userId) {
        setLoading(true);
        try {
          const response = await usersApi.initUser();
          const newUserId = response.user_id;
          localStorage.setItem('userId', newUserId);
          setUserId(newUserId);
        } catch (error) {
          console.error('Failed to initialize user:', error);
        } finally {
          setLoading(false);
        }
      }
    };

    initUser();
  }, [userId]);

  return { userId, loading };
};
```

### Step 5: Update SearchPage Component

**Changes needed in:** `frontend/src/components/SearchPage.tsx`

```typescript
// Add at top
import { useState, useEffect } from 'react';
import { papersApi } from '../api/papers';

// Replace hardcoded categories
const [categories, setCategories] = useState<any[]>([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchCategories = async () => {
    try {
      const data = await papersApi.getCategories();
      setCategories(Object.values(data.categories));
    } catch (error) {
      console.error('Failed to fetch categories:', error);
      // Fallback to hardcoded categories
      setCategories([
        { id: 'ai_cs', name: 'AI & CS' },
        { id: 'medicine_biology', name: 'Medicine & Biology' },
        // ... etc
      ]);
    } finally {
      setLoading(false);
    }
  };
  fetchCategories();
}, []);
```

### Step 6: Update SearchResults Component

**Changes needed in:** `frontend/src/components/SearchResults.tsx`

```typescript
// Replace mock data with real API call
import { useSearch } from '../hooks/useSearch';
import { usersApi } from '../api/users';

const SearchResults = ({ searchQuery, searchCategory, ... }) => {
  const { data, loading, error } = useSearch(searchQuery, searchCategory);
  
  const handleSavePaper = async (paper: Paper) => {
    try {
      if (isPaperSaved(paper.id)) {
        await usersApi.unsavePaper(parseInt(paper.id));
      } else {
        await usersApi.savePaper(parseInt(paper.id));
      }
      onSavePaper(paper); // Update local state
    } catch (error) {
      console.error('Failed to save/unsave paper:', error);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  const papers = data?.papers || [];
  
  // Rest of component...
};
```

### Step 7: Update Workspace Component

**Changes needed in:** `frontend/src/components/Workspace.tsx`

```typescript
import { useState, useEffect } from 'react';
import { usersApi } from '../api/users';

const Workspace = ({ onNavigate }) => {
  const [savedPapers, setSavedPapers] = useState([]);
  const [notes, setNotes] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [papersData, notesData, reviewsData] = await Promise.all([
          usersApi.getSavedPapers(),
          usersApi.getNotesHierarchy(),
          usersApi.getReviews()
        ]);
        setSavedPapers(papersData.papers);
        setNotes(notesData.hierarchy);
        setReviews(reviewsData.reviews);
      } catch (error) {
        console.error('Failed to fetch workspace data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Rest of component...
};
```

---

## 🧪 Testing the Integration

### 1. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Verify Backend is Running
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", "service": "api"}

curl http://localhost:8000/api/v1/papers/categories
# Should return list of categories
```

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

### 4. Test Integration
1. Open http://localhost:5173
2. Search for "machine learning"
3. Check browser DevTools Network tab
4. Should see API calls to `http://localhost:8000/api/v1/papers/search`
5. Save a paper - should see POST to `/api/v1/users/papers/save`
6. Go to Workspace - should see GET to `/api/v1/users/papers/saved`

---

## 📈 Estimated Timeline

| Phase | Task | Time | Priority |
|-------|------|------|----------|
| 1 | API Client Setup | 2h | 🔴 Critical |
| 2 | Data Fetching Hooks | 3h | 🔴 Critical |
| 3 | SearchPage Integration | 2h | 🔴 Critical |
| 4 | SearchResults Integration | 2h | 🔴 Critical |
| 5 | Workspace Integration | 3h | 🟡 High |
| 6 | Error Handling & UX | 2h | 🟡 High |
| 7 | Testing & Debugging | 2h | 🟡 High |
| **Total** | | **16h** | |

---

## 🎯 Success Criteria

### Must Have
- ✅ Search returns real papers from backend
- ✅ Save/unsave papers persists to database
- ✅ Workspace shows actual saved papers
- ✅ Notes can be created and retrieved
- ✅ Error messages show for failed requests

### Should Have
- ✅ Loading states during API calls
- ✅ Optimistic UI updates
- ✅ Retry logic for failed requests
- ✅ Toast notifications for actions

### Nice to Have
- ✅ Offline support with service workers
- ✅ Request debouncing for search
- ✅ Infinite scroll for results
- ✅ Real-time updates with WebSockets

---

## 🚨 Common Issues & Solutions

### Issue 1: CORS Errors
**Symptom:** `Access-Control-Allow-Origin` error in browser console

**Solution:**
```python
# backend/app/main.py - Already configured!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 2: 404 Not Found
**Symptom:** API calls return 404

**Solution:** Check API URL in `.env`:
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000  # No trailing slash!
```

### Issue 3: User ID Not Found
**Symptom:** `User not found` errors

**Solution:** Initialize user on app load:
```typescript
// App.tsx
const { userId } = useUser();  // This hook auto-initializes
```

---

## 📚 Additional Resources

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Backend Guides
- [API_REFERENCE.md](./API_REFERENCE.md) - Complete API documentation
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Deployment instructions

### Frontend Libraries
- [React Query](https://tanstack.com/query/latest) - Data fetching
- [Axios](https://axios-http.com/) - HTTP client
- [React Hook Form](https://react-hook-form.com/) - Form handling

---

## 🤝 Need Help?

1. **Check Backend Logs**: `docker-compose logs -f backend`
2. **Check Frontend Console**: Browser DevTools → Console
3. **Test API Directly**: Use Swagger UI at http://localhost:8000/docs
4. **Review Network Tab**: Check request/response in DevTools

---

**Next Steps:** Start with Phase 1 (API Client Setup) and work through each phase sequentially. Test each integration point before moving to the next.
