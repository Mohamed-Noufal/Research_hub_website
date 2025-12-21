# Phase 3: DOI-Based Paper Fetching
## Fetch Papers Directly by DOI from Multiple Sources

**Timeline:** Week 5 (~9 hours)  
**Priority:** MEDIUM - User-requested feature  
**Impact:** Easier paper discovery, better data quality

---

## 🎯 **Phase 3 Objectives**

1. Allow users to fetch papers by DOI
2. Integrate multiple data sources (Crossref, Unpaywall, Semantic Scholar)
3. Automatic deduplication
4. Generate embeddings automatically
5. Seamless integration with existing workflow

**Why This Feature:**
- Users often have DOIs from citations
- Faster than manual search
- Better metadata quality
- Free APIs (no cost!)

---

## 📊 **What is DOI?**

**DOI (Digital Object Identifier):** Unique identifier for academic papers

**Examples:**
- `10.1038/nature12373` (Nature paper)
- `10.1109/CVPR.2016.90` (IEEE paper)
- `10.1371/journal.pone.0123456` (PLOS ONE paper)

**Format:** `10.{publisher}/{unique-id}`

---

## 🔧 **Task 3.1: API Endpoint** (3 hours)

### **Backend Implementation:**

```python
# backend/app/api/v1/papers.py
from app.services.doi_fetcher_service import DOIFetcherService
from app.services.vector_service import EnhancedVectorService

@router.post("/papers/fetch-by-doi")
async def fetch_by_doi(
    doi: str,
    user_id: Optional[str] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch paper by DOI and save to database
    
    Example DOI: "10.1038/nature12373"
    
    Returns:
        - paper: Paper object
        - status: "created" | "already_exists"
        - source: Which API provided the data
    """
    # Clean DOI (remove URL prefix if present)
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    
    # Check if already in database
    existing = db.query(Paper).filter(Paper.doi == doi).first()
    if existing:
        return {
            "paper": existing,
            "status": "already_exists",
            "message": "Paper already in database"
        }
    
    # Fetch from external sources
    fetcher = DOIFetcherService()
    paper_data = await fetcher.fetch_paper_by_doi(doi)
    
    if not paper_data:
        raise HTTPException(
            status_code=404,
            detail=f"Paper with DOI '{doi}' not found in any source"
        )
    
    # Save to database
    paper = Paper(**paper_data)
    db.add(paper)
    db.commit()
    db.refresh(paper)
    
    # Generate embeddings (async)
    vector_service = EnhancedVectorService()
    await vector_service.generate_embeddings_for_papers(db, paper_ids=[paper.id])
    
    # If user is logged in, auto-save to their library
    if user_id:
        saved_paper = UserSavedPaper(
            user_id=user_id,
            paper_id=paper.id,
            saved_at=datetime.utcnow()
        )
        db.add(saved_paper)
        db.commit()
    
    return {
        "paper": paper,
        "status": "created",
        "source": paper_data.get("source", "unknown"),
        "message": "Paper fetched and saved successfully"
    }


@router.post("/papers/fetch-by-doi-batch")
async def fetch_by_doi_batch(
    dois: List[str],
    user_id: Optional[str] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fetch multiple papers by DOI"""
    results = []
    
    for doi in dois:
        try:
            result = await fetch_by_doi(doi, user_id, db)
            results.append(result)
        except Exception as e:
            results.append({
                "doi": doi,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "results": results,
        "total": len(dois),
        "successful": len([r for r in results if r["status"] in ["created", "already_exists"]]),
        "failed": len([r for r in results if r["status"] == "error"])
    }
```

---

## 🎨 **Task 3.2: Frontend Component** (4 hours)

### **DOI Search Component:**

```typescript
// frontend/src/components/DOISearch.tsx
import { useState } from 'react';

export function DOISearch() {
  const [doi, setDoi] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  
  const handleFetch = async () => {
    if (!doi.trim()) {
      setError('Please enter a DOI');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await fetch('/api/v1/papers/fetch-by-doi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doi: doi.trim() })
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Paper not found');
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleFetch();
    }
  };
  
  return (
    <div className="doi-search">
      <div className="doi-search-header">
        <h2>🔍 Fetch Paper by DOI</h2>
        <p>Enter a DOI to fetch paper metadata and PDF link</p>
      </div>
      
      <div className="doi-search-input">
        <input
          type="text"
          value={doi}
          onChange={(e) => setDoi(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="e.g., 10.1038/nature12373"
          className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-blue-500"
          disabled={loading}
        />
        <button
          onClick={handleFetch}
          disabled={loading || !doi.trim()}
          className="mt-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Fetching...
            </>
          ) : (
            'Fetch Paper'
          )}
        </button>
      </div>
      
      {error && (
        <div className="doi-search-error">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
        </div>
      )}
      
      {result && (
        <div className="doi-search-result">
          {result.status === 'already_exists' && (
            <div className="status-badge status-exists">
              ✓ Already in your library
            </div>
          )}
          {result.status === 'created' && (
            <div className="status-badge status-new">
              ✨ New paper added!
            </div>
          )}
          
          <PaperCard paper={result.paper} />
          
          <div className="result-actions">
            <button onClick={() => viewPaper(result.paper)}>
              View Full Details
            </button>
            {result.paper.pdf_url && (
              <a href={result.paper.pdf_url} target="_blank" rel="noopener">
                📄 Download PDF
              </a>
            )}
          </div>
        </div>
      )}
      
      <div className="doi-search-examples">
        <p>Try these examples:</p>
        <button onClick={() => setDoi('10.1038/nature12373')}>
          Nature paper
        </button>
        <button onClick={() => setDoi('10.1109/CVPR.2016.90')}>
          IEEE paper
        </button>
        <button onClick={() => setDoi('10.1371/journal.pone.0123456')}>
          PLOS ONE paper
        </button>
      </div>
    </div>
  );
}
```

### **Batch DOI Import:**

```typescript
// frontend/src/components/DOIBatchImport.tsx
export function DOIBatchImport() {
  const [dois, setDois] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  
  const handleImport = async () => {
    const doiList = dois.split('\n').map(d => d.trim()).filter(d => d);
    
    setLoading(true);
    try {
      const response = await fetch('/api/v1/papers/fetch-by-doi-batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dois: doiList })
      });
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Batch import failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="doi-batch-import">
      <h2>📚 Batch Import by DOI</h2>
      <p>Paste multiple DOIs (one per line)</p>
      
      <textarea
        value={dois}
        onChange={(e) => setDois(e.target.value)}
        placeholder="10.1038/nature12373\n10.1109/CVPR.2016.90\n10.1371/journal.pone.0123456"
        rows={10}
        className="w-full p-4 border rounded-lg"
      />
      
      <button onClick={handleImport} disabled={loading}>
        {loading ? 'Importing...' : `Import ${dois.split('\n').filter(d => d.trim()).length} Papers`}
      </button>
      
      {results && (
        <div className="import-results">
          <h3>Import Results</h3>
          <p>✅ Successful: {results.successful}</p>
          <p>❌ Failed: {results.failed}</p>
          
          <div className="results-list">
            {results.results.map((r, i) => (
              <div key={i} className={`result-item result-${r.status}`}>
                {r.status === 'created' && `✅ ${r.paper.title}`}
                {r.status === 'already_exists' && `ℹ️ ${r.paper.title} (already exists)`}
                {r.status === 'error' && `❌ ${r.doi}: ${r.error}`}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 🧪 **Task 3.3: Testing** (2 hours)

### **Backend Tests:**

```python
# backend/tests/test_doi_fetcher.py
import pytest
from app.services.doi_fetcher_service import DOIFetcherService

@pytest.mark.asyncio
async def test_fetch_valid_doi():
    """Test fetching a valid DOI"""
    fetcher = DOIFetcherService()
    paper = await fetcher.fetch_paper_by_doi("10.1038/nature12373")
    
    assert paper is not None
    assert paper['title']
    assert paper['authors']
    assert paper['doi'] == "10.1038/nature12373"

@pytest.mark.asyncio
async def test_fetch_invalid_doi():
    """Test fetching an invalid DOI"""
    fetcher = DOIFetcherService()
    paper = await fetcher.fetch_paper_by_doi("invalid_doi_12345")
    
    assert paper is None

@pytest.mark.asyncio
async def test_fetch_with_pdf():
    """Test fetching DOI with PDF link"""
    fetcher = DOIFetcherService()
    paper = await fetcher.fetch_paper_by_doi("10.1371/journal.pone.0123456")
    
    assert paper is not None
    # PLOS ONE papers usually have open access PDFs
    assert 'pdf_url' in paper or 'open_access_pdf' in paper

@pytest.mark.asyncio
async def test_api_endpoint(client):
    """Test DOI fetch API endpoint"""
    response = await client.post("/api/v1/papers/fetch-by-doi", json={
        "doi": "10.1038/nature12373"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data['status'] in ['created', 'already_exists']
    assert data['paper']['doi'] == "10.1038/nature12373"
```

---

## 📊 **Phase 3 Results**

### **What Users Can Do:**
1. ✅ Paste DOI → Get paper instantly
2. ✅ Batch import from reference list
3. ✅ Auto-save to library
4. ✅ Get PDF links (if available)
5. ✅ Automatic deduplication

### **Data Sources:**
- **Crossref:** Metadata for most papers
- **Unpaywall:** Open access PDF links
- **Semantic Scholar:** Enhanced metadata

### **Cost:** $0 (all APIs are free!)

---

## ✅ **Success Criteria**

- [ ] API endpoint works for valid DOIs
- [ ] Handles invalid DOIs gracefully
- [ ] Deduplication works (no duplicates)
- [ ] Embeddings generated automatically
- [ ] Frontend component renders correctly
- [ ] Batch import works
- [ ] All tests pass
- [ ] Error messages are user-friendly

---

## 🚀 **Integration Points**

### **Add to SearchPage:**
```typescript
// frontend/src/pages/SearchPage.tsx
<Tabs>
  <Tab label="Search">
    <SearchBar />
  </Tab>
  <Tab label="Fetch by DOI">
    <DOISearch />  {/* NEW */}
  </Tab>
</Tabs>
```

### **Add to Workspace:**
```typescript
// Add "Import by DOI" button
<button onClick={() => openDOIImport()}>
  📥 Import by DOI
</button>
```

---

**Total Time:** ~9 hours  
**Total Cost:** $0  
**Impact:** Better user experience, easier paper discovery
