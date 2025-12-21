# Implementation Plan
## Paper Search Platform - Development Roadmap

**Created:** 2025-11-22  
**Status:** In Progress  
**Timeline:** 8 weeks to MVP, 12 months to enterprise-ready

---

## 🎯 **Immediate Priorities (Week 1-2)**

### **Phase 1: Critical Performance Fixes** ⚡ HIGH PRIORITY

#### Task 1.1: Database Indexing (Day 1)
**Estimated Time:** 30 minutes  
**Impact:** 40x faster searches  
**Status:** ⏳ Ready to implement

**Steps:**
1. Run database migration
   ```bash
   cd backend
   python migrations/run_migration.py
   ```
2. Verify indexes created
   ```sql
   SELECT indexname FROM pg_indexes WHERE schemaname = 'public';
   ```
3. Test query performance
   ```sql
   EXPLAIN ANALYZE SELECT * FROM papers WHERE category = 'ai_cs' LIMIT 20;
   ```

**Success Criteria:**
- ✅ All 25+ indexes created
- ✅ Search queries use index scans (not seq scans)
- ✅ Query time < 50ms for category searches

**Files to modify:**
- None (just run migration)

---

#### Task 1.2: Connection Pooling (Day 1)
**Estimated Time:** 15 minutes  
**Impact:** 10x more concurrent users  
**Status:** ⏳ Ready to implement

**Steps:**
1. Edit `backend/app/core/database.py`
2. Add connection pooling configuration
3. Restart backend server
4. Test with concurrent requests

**Code changes:**
```python
# backend/app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

**Success Criteria:**
- ✅ Connection pool active
- ✅ No connection errors under load
- ✅ Handles 100+ concurrent requests

**Files to modify:**
- `backend/app/core/database.py`

---

#### Task 1.3: Add Pagination (Day 2)
**Estimated Time:** 2 hours  
**Impact:** Prevents memory issues at scale  
**Status:** ⏳ Ready to implement

**Steps:**
1. Update search endpoint with pagination params
2. Add pagination to user library endpoints
3. Update frontend to handle paginated responses
4. Test with large result sets

**Code changes:**
```python
# backend/app/api/v1/papers.py
@router.post("/search")
async def search_papers(
    query: str,
    category: str,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    # ... search logic with LIMIT and OFFSET
    
    return {
        "papers": results,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }
```

**Success Criteria:**
- ✅ All list endpoints support pagination
- ✅ Frontend handles pagination
- ✅ No memory issues with 10,000+ papers

**Files to modify:**
- `backend/app/api/v1/papers.py`
- `backend/app/api/v1/users.py`
- `frontend/src/components/SearchResults.tsx`

---

## 🚀 **Feature Development (Week 3-4)**

### **Phase 2: DOI-Based Paper Fetching**

#### Task 2.1: Create API Endpoint (Day 1)
**Estimated Time:** 3 hours  
**Impact:** New feature for users  
**Status:** ⏳ Service already created

**Steps:**
1. Add endpoint to `backend/app/api/v1/papers.py`
2. Integrate `DOIFetcherService`
3. Add error handling
4. Test with various DOIs

**Code changes:**
```python
# backend/app/api/v1/papers.py
from app.services.doi_fetcher_service import DOIFetcherService

@router.post("/papers/fetch-by-doi")
async def fetch_by_doi(
    doi: str,
    db: Session = Depends(get_db)
):
    fetcher = DOIFetcherService()
    paper_data = await fetcher.fetch_paper_by_doi(doi)
    
    if not paper_data:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if already exists
    existing = db.query(Paper).filter(Paper.doi == doi).first()
    if existing:
        return {"paper": existing, "status": "already_exists"}
    
    # Save to database
    paper = Paper(**paper_data)
    db.add(paper)
    db.commit()
    
    # Generate embeddings
    vector_service = EnhancedVectorService()
    await vector_service.generate_embeddings_for_papers(db, paper_ids=[paper.id])
    
    return {"paper": paper, "status": "created"}
```

**Success Criteria:**
- ✅ Endpoint returns paper metadata
- ✅ Handles duplicate DOIs gracefully
- ✅ Generates embeddings automatically
- ✅ Returns PDF link if available

**Files to create/modify:**
- `backend/app/api/v1/papers.py` (modify)

---

#### Task 2.2: Create Frontend Component (Day 2)
**Estimated Time:** 4 hours  
**Impact:** User-facing feature  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `DOISearch.tsx` component
2. Add to SearchPage
3. Style with TailwindCSS
4. Add loading and error states
5. Test user flow

**Code changes:**
```typescript
// frontend/src/components/DOISearch.tsx
import { useState } from 'react';

export function DOISearch() {
  const [doi, setDoi] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  
  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/papers/fetch-by-doi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doi })
      });
      
      if (!response.ok) throw new Error('Paper not found');
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="doi-search">
      <input
        type="text"
        placeholder="Enter DOI (e.g., 10.1038/nature12373)"
        value={doi}
        onChange={(e) => setDoi(e.target.value)}
        className="w-full px-4 py-2 border rounded-lg"
      />
      <button
        onClick={handleFetch}
        disabled={loading || !doi}
        className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg"
      >
        {loading ? 'Fetching...' : 'Fetch Paper'}
      </button>
      
      {error && <p className="text-red-600 mt-2">{error}</p>}
      {result && <PaperCard paper={result.paper} />}
    </div>
  );
}
```

**Success Criteria:**
- ✅ Component renders correctly
- ✅ Validates DOI format
- ✅ Shows loading state
- ✅ Displays paper or error message

**Files to create/modify:**
- `frontend/src/components/DOISearch.tsx` (create)
- `frontend/src/pages/SearchPage.tsx` (modify)

---

#### Task 2.3: Testing & Integration (Day 3)
**Estimated Time:** 2 hours  
**Impact:** Quality assurance  
**Status:** ⏳ Ready to implement

**Steps:**
1. Test with valid DOIs
2. Test with invalid DOIs
3. Test with duplicate DOIs
4. Test error handling
5. Test PDF link retrieval

**Test cases:**
```python
# backend/tests/test_doi_fetcher.py
import pytest
from app.services.doi_fetcher_service import DOIFetcherService

@pytest.mark.asyncio
async def test_fetch_valid_doi():
    fetcher = DOIFetcherService()
    paper = await fetcher.fetch_paper_by_doi("10.1038/nature12373")
    assert paper is not None
    assert paper['title']
    assert paper['authors']

@pytest.mark.asyncio
async def test_fetch_invalid_doi():
    fetcher = DOIFetcherService()
    paper = await fetcher.fetch_paper_by_doi("invalid_doi")
    assert paper is None
```

**Success Criteria:**
- ✅ All test cases pass
- ✅ Error handling works
- ✅ Integration with existing workflow

**Files to create:**
- `backend/tests/test_doi_fetcher.py`

---

## 📄 **Document Generation (Week 5-6)**

### **Phase 3: LLM Document Formatting**

#### Task 3.1: Document Formatter Service (Day 1-2)
**Estimated Time:** 8 hours  
**Impact:** Core feature functionality  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `document_formatter_service.py`
2. Implement APA citation style
3. Implement IEEE citation style
4. Implement Chicago citation style
5. Add document styling (fonts, margins, spacing)
6. Test with sample papers

**Code structure:**
```python
# backend/app/services/document_formatter_service.py
from docx import Document
from docx.shared import Pt, Inches

class AcademicDocumentFormatter:
    STYLES = {
        "apa": {...},
        "ieee": {...},
        "chicago": {...}
    }
    
    def create_literature_review(self, papers, style="apa"):
        # Create Word document
        # Apply formatting
        # Add citations
        # Add references
        return doc
```

**Success Criteria:**
- ✅ Generates properly formatted Word documents
- ✅ All 3 citation styles work correctly
- ✅ Proper margins, fonts, line spacing
- ✅ Hanging indents for references

**Files to create:**
- `backend/app/services/document_formatter_service.py`

**Dependencies:**
```bash
pip install python-docx
```

---

#### Task 3.2: LLM Integration (Day 3-4)
**Estimated Time:** 8 hours  
**Impact:** AI-powered content generation  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `llm_document_service.py`
2. Integrate GPT-5 nano API
3. Implement content generation prompts
4. Add thematic section generation
5. Test with different paper sets

**Code structure:**
```python
# backend/app/services/llm_document_service.py
class LLMDocumentService:
    def __init__(self, llm_provider="gpt5-nano"):
        self.llm_provider = llm_provider
    
    async def generate_literature_review(self, papers, focus_area=None):
        # Generate introduction
        # Identify themes
        # Generate sections
        # Generate conclusion
        return content
```

**Success Criteria:**
- ✅ Generates coherent academic content
- ✅ Properly cites papers
- ✅ Identifies relevant themes
- ✅ Cost < $0.01 per review

**Files to create:**
- `backend/app/services/llm_document_service.py`

**Dependencies:**
```bash
pip install openai
```

---

#### Task 3.3: API Endpoint (Day 5)
**Estimated Time:** 4 hours  
**Impact:** Backend integration  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `/documents/generate-literature-review` endpoint
2. Integrate formatter and LLM services
3. Add file download response
4. Test with Postman/curl

**Code changes:**
```python
# backend/app/api/v1/documents.py (create new file)
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

router = APIRouter()

@router.post("/documents/generate-literature-review")
async def generate_literature_review(
    paper_ids: List[int],
    style: str = "apa",
    focus_area: Optional[str] = None,
    use_llm: bool = True,
    db: Session = Depends(get_db)
):
    # Fetch papers
    # Generate content
    # Format document
    # Return file
    return FileResponse(filepath, filename="literature_review.docx")
```

**Success Criteria:**
- ✅ Endpoint returns Word document
- ✅ Document is properly formatted
- ✅ Download works in browser

**Files to create:**
- `backend/app/api/v1/documents.py`
- Update `backend/app/main.py` to include router

---

#### Task 3.4: Frontend Component (Day 6-7)
**Estimated Time:** 6 hours  
**Impact:** User-facing feature  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `DocumentGenerator.tsx` component
2. Add to Workspace page
3. Style with TailwindCSS
4. Add file download handling
5. Test user flow

**Success Criteria:**
- ✅ Component renders in Workspace
- ✅ User can select papers
- ✅ User can choose citation style
- ✅ Document downloads correctly

**Files to create:**
- `frontend/src/components/DocumentGenerator.tsx`
- Update `frontend/src/pages/Workspace.tsx`

---

## 🤖 **AI Writing Tools (Week 7-8)**

### **Phase 4: AI Writing Detection & Paraphrasing**

#### Task 4.1: AI Writing Detection Service (Day 1-2)
**Estimated Time:** 8 hours  
**Impact:** Academic integrity feature  
**Status:** ⏳ Ready to implement

**Purpose:** Detect AI-generated content in papers and literature reviews to ensure academic integrity.

**Steps:**
1. Create `ai_detection_service.py`
2. Integrate AI detection APIs
3. Implement scoring algorithm
4. Add batch processing
5. Test with various texts

**Code structure:**
```python
# backend/app/services/ai_detection_service.py
from typing import Dict, List
import httpx

class AIDetectionService:
    """Detect AI-generated content in academic text"""
    
    def __init__(self):
        self.detectors = {
            "gptzero": self._detect_with_gptzero,
            "copyleaks": self._detect_with_copyleaks,
            "originality": self._detect_with_originality,
        }
    
    async def detect_ai_content(
        self,
        text: str,
        detector: str = "gptzero"
    ) -> Dict:
        """
        Detect AI-generated content
        
        Returns:
            {
                "is_ai_generated": bool,
                "ai_probability": float (0-1),
                "human_probability": float (0-1),
                "sentences": List[Dict],  # Per-sentence analysis
                "overall_score": float,
                "confidence": str  # "high", "medium", "low"
            }
        """
        if detector not in self.detectors:
            raise ValueError(f"Unknown detector: {detector}")
        
        return await self.detectors[detector](text)
    
    async def _detect_with_gptzero(self, text: str) -> Dict:
        """Use GPTZero API for detection"""
        # GPTZero API: https://gptzero.me/
        url = "https://api.gptzero.me/v2/predict/text"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"document": text},
                headers={"x-api-key": settings.GPTZERO_API_KEY}
            )
            response.raise_for_status()
            data = response.json()
        
        return {
            "is_ai_generated": data["documents"][0]["completely_generated_prob"] > 0.5,
            "ai_probability": data["documents"][0]["completely_generated_prob"],
            "human_probability": 1 - data["documents"][0]["completely_generated_prob"],
            "sentences": data["documents"][0]["sentences"],
            "overall_score": data["documents"][0]["average_generated_prob"],
            "confidence": self._get_confidence_level(
                data["documents"][0]["completely_generated_prob"]
            )
        }
    
    async def _detect_with_copyleaks(self, text: str) -> Dict:
        """Use Copyleaks AI Content Detector"""
        # Copyleaks API: https://api.copyleaks.com/
        # Similar implementation
        pass
    
    def _get_confidence_level(self, probability: float) -> str:
        """Determine confidence level"""
        if probability > 0.8 or probability < 0.2:
            return "high"
        elif probability > 0.6 or probability < 0.4:
            return "medium"
        else:
            return "low"
    
    async def analyze_paper(self, paper_id: int, db: Session) -> Dict:
        """Analyze entire paper for AI content"""
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        
        if not paper:
            raise ValueError("Paper not found")
        
        # Analyze abstract
        abstract_result = await self.detect_ai_content(paper.abstract)
        
        # Store results
        paper.ai_detection_score = abstract_result["ai_probability"]
        paper.ai_detection_confidence = abstract_result["confidence"]
        db.commit()
        
        return {
            "paper_id": paper_id,
            "title": paper.title,
            "abstract_analysis": abstract_result,
            "recommendation": self._get_recommendation(abstract_result)
        }
    
    def _get_recommendation(self, result: Dict) -> str:
        """Get recommendation based on detection results"""
        if result["ai_probability"] > 0.8:
            return "High likelihood of AI-generated content. Review carefully."
        elif result["ai_probability"] > 0.5:
            return "Moderate likelihood of AI content. Manual review recommended."
        else:
            return "Low likelihood of AI content. Appears human-written."
```

**API Options & Costs:**

1. **GPTZero** (Recommended)
   - Free tier: 5,000 words/month
   - Paid: $10/month for 150,000 words
   - Best accuracy for academic text
   - **Cost: $0.00007 per word**

2. **Copyleaks AI Detector**
   - Free tier: 10 pages/month
   - Paid: $9.99/month for 100 pages
   - Good for plagiarism + AI detection
   - **Cost: $0.10 per page**

3. **Originality.AI**
   - Pay-as-you-go: $0.01 per 100 words
   - Best for bulk checking
   - **Cost: $0.0001 per word**

**Success Criteria:**
- ✅ Detects AI-generated text with >85% accuracy
- ✅ Provides sentence-level analysis
- ✅ Returns confidence scores
- ✅ Cost < $0.01 per paper

**Files to create:**
- `backend/app/services/ai_detection_service.py`

**Dependencies:**
```bash
pip install httpx
```

---

#### Task 4.2: Paraphrasing Service (Day 3-4)
**Estimated Time:** 10 hours  
**Impact:** Content improvement tool  
**Status:** ⏳ Ready to implement

**Purpose:** Help users paraphrase and improve academic writing while maintaining meaning.

**Steps:**
1. Create `paraphrasing_service.py`
2. Integrate LLM for paraphrasing
3. Add academic tone preservation
4. Implement citation preservation
5. Test with various texts

**Code structure:**
```python
# backend/app/services/paraphrasing_service.py
from typing import Dict, List, Optional
import openai

class ParaphrasingService:
    """Paraphrase academic text while preserving meaning"""
    
    def __init__(self, llm_provider="gpt5-nano"):
        self.llm_provider = llm_provider
        self.client = openai.AsyncOpenAI()
    
    async def paraphrase_text(
        self,
        text: str,
        style: str = "academic",
        preserve_citations: bool = True,
        formality_level: str = "formal"
    ) -> Dict:
        """
        Paraphrase text while maintaining academic integrity
        
        Args:
            text: Text to paraphrase
            style: "academic", "simple", "technical"
            preserve_citations: Keep citations intact
            formality_level: "formal", "semi-formal", "casual"
        
        Returns:
            {
                "original": str,
                "paraphrased": str,
                "changes": List[Dict],
                "similarity_score": float,
                "word_count_change": int
            }
        """
        # Extract citations if needed
        citations = []
        if preserve_citations:
            citations = self._extract_citations(text)
            text_without_citations = self._remove_citations(text, citations)
        else:
            text_without_citations = text
        
        # Generate paraphrase
        prompt = self._create_paraphrase_prompt(
            text_without_citations,
            style,
            formality_level
        )
        
        paraphrased = await self._call_llm(prompt)
        
        # Reinsert citations
        if preserve_citations:
            paraphrased = self._reinsert_citations(paraphrased, citations)
        
        # Calculate similarity
        similarity = await self._calculate_similarity(text, paraphrased)
        
        return {
            "original": text,
            "paraphrased": paraphrased,
            "changes": self._highlight_changes(text, paraphrased),
            "similarity_score": similarity,
            "word_count_change": len(paraphrased.split()) - len(text.split()),
            "preserved_citations": citations if preserve_citations else []
        }
    
    def _create_paraphrase_prompt(
        self,
        text: str,
        style: str,
        formality_level: str
    ) -> str:
        """Create prompt for LLM paraphrasing"""
        style_instructions = {
            "academic": "Use formal academic language with precise terminology",
            "simple": "Use clear, simple language accessible to general readers",
            "technical": "Use technical terminology appropriate for experts"
        }
        
        formality_instructions = {
            "formal": "Maintain high formality, avoid contractions",
            "semi-formal": "Balance formality with readability",
            "casual": "Use conversational tone while remaining professional"
        }
        
        return f"""
        Paraphrase the following academic text while:
        1. Preserving the original meaning completely
        2. {style_instructions[style]}
        3. {formality_instructions[formality_level]}
        4. Maintaining academic integrity (no plagiarism)
        5. Keeping approximately the same length
        
        Original text:
        {text}
        
        Paraphrased text:
        """
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM for paraphrasing"""
        response = await self.client.chat.completions.create(
            model="gpt-5-nano",  # Cheap and fast
            messages=[
                {
                    "role": "system",
                    "content": "You are an academic writing assistant specializing in paraphrasing."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Some creativity, but not too much
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    
    def _extract_citations(self, text: str) -> List[Dict]:
        """Extract citations from text"""
        import re
        
        citations = []
        
        # APA style: (Author, Year)
        apa_pattern = r'\([A-Z][a-z]+(?:\s+et\s+al\.)?,\s+\d{4}\)'
        citations.extend([
            {"type": "apa", "text": m.group(), "position": m.start()}
            for m in re.finditer(apa_pattern, text)
        ])
        
        # IEEE style: [1]
        ieee_pattern = r'\[\d+\]'
        citations.extend([
            {"type": "ieee", "text": m.group(), "position": m.start()}
            for m in re.finditer(ieee_pattern, text)
        ])
        
        return citations
    
    def _remove_citations(self, text: str, citations: List[Dict]) -> str:
        """Temporarily remove citations"""
        for i, citation in enumerate(citations):
            text = text.replace(citation["text"], f"__CITATION_{i}__")
        return text
    
    def _reinsert_citations(self, text: str, citations: List[Dict]) -> str:
        """Reinsert citations in paraphrased text"""
        for i, citation in enumerate(citations):
            text = text.replace(f"__CITATION_{i}__", citation["text"])
        return text
    
    async def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts"""
        from sentence_transformers import SentenceTransformer, util
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode([text1, text2])
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        
        return similarity
    
    def _highlight_changes(self, original: str, paraphrased: str) -> List[Dict]:
        """Highlight what changed"""
        import difflib
        
        diff = difflib.ndiff(original.split(), paraphrased.split())
        
        changes = []
        for i, word in enumerate(diff):
            if word.startswith('- '):
                changes.append({"type": "removed", "word": word[2:], "position": i})
            elif word.startswith('+ '):
                changes.append({"type": "added", "word": word[2:], "position": i})
        
        return changes
    
    async def paraphrase_paragraph_by_paragraph(
        self,
        text: str,
        **kwargs
    ) -> Dict:
        """Paraphrase text paragraph by paragraph for better quality"""
        paragraphs = text.split('\n\n')
        paraphrased_paragraphs = []
        
        for para in paragraphs:
            if para.strip():
                result = await self.paraphrase_text(para, **kwargs)
                paraphrased_paragraphs.append(result["paraphrased"])
        
        return {
            "original": text,
            "paraphrased": '\n\n'.join(paraphrased_paragraphs),
            "paragraph_count": len(paragraphs)
        }
```

**Cost Analysis:**
- GPT-5 nano: $0.05/1M input tokens, $0.40/1M output tokens
- Average paragraph: ~200 words = ~300 tokens
- Cost per paragraph: ~$0.0003 (less than 1 cent!)
- **Very affordable** ✅

**Success Criteria:**
- ✅ Maintains original meaning (similarity > 0.85)
- ✅ Preserves citations correctly
- ✅ Improves readability
- ✅ Cost < $0.01 per 1,000 words

**Files to create:**
- `backend/app/services/paraphrasing_service.py`

**Dependencies:**
```bash
pip install openai sentence-transformers
```

---

#### Task 4.3: API Endpoints (Day 5)
**Estimated Time:** 4 hours  
**Impact:** Backend integration  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `/ai-tools/detect` endpoint
2. Create `/ai-tools/paraphrase` endpoint
3. Add rate limiting (expensive operations)
4. Test with Postman

**Code changes:**
```python
# backend/app/api/v1/ai_tools.py (create new file)
from fastapi import APIRouter, Depends, HTTPException
from app.services.ai_detection_service import AIDetectionService
from app.services.paraphrasing_service import ParaphrasingService

router = APIRouter()

@router.post("/ai-tools/detect")
@limiter.limit("10/hour")  # Rate limit expensive operation
async def detect_ai_content(
    text: str,
    detector: str = "gptzero"
):
    """Detect AI-generated content in text"""
    service = AIDetectionService()
    result = await service.detect_ai_content(text, detector)
    return result

@router.post("/ai-tools/paraphrase")
@limiter.limit("20/hour")  # Rate limit
async def paraphrase_text(
    text: str,
    style: str = "academic",
    preserve_citations: bool = True,
    formality_level: str = "formal"
):
    """Paraphrase text while preserving meaning"""
    service = ParaphrasingService()
    result = await service.paraphrase_text(
        text,
        style=style,
        preserve_citations=preserve_citations,
        formality_level=formality_level
    )
    return result

@router.post("/ai-tools/analyze-paper/{paper_id}")
async def analyze_paper_ai_content(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Analyze entire paper for AI content"""
    service = AIDetectionService()
    result = await service.analyze_paper(paper_id, db)
    return result
```

**Success Criteria:**
- ✅ Endpoints return correct data
- ✅ Rate limiting works
- ✅ Error handling robust

**Files to create:**
- `backend/app/api/v1/ai_tools.py`
- Update `backend/app/main.py` to include router

---

#### Task 4.4: Frontend Components (Day 6-7)
**Estimated Time:** 8 hours  
**Impact:** User-facing features  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create `AIDetector.tsx` component
2. Create `Paraphraser.tsx` component
3. Add to Workspace page
4. Style with TailwindCSS
5. Test user flows

**Code changes:**
```typescript
// frontend/src/components/AIDetector.tsx
import { useState } from 'react';

export function AIDetector() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  
  const handleDetect = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai-tools/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Detection failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="ai-detector">
      <h3>AI Content Detector</h3>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste text to analyze..."
        className="w-full h-40 p-4 border rounded-lg"
      />
      <button
        onClick={handleDetect}
        disabled={loading || !text}
        className="mt-2 px-6 py-2 bg-purple-600 text-white rounded-lg"
      >
        {loading ? 'Analyzing...' : 'Detect AI Content'}
      </button>
      
      {result && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="font-semibold">AI Probability:</span>
            <span className={`text-lg font-bold ${
              result.ai_probability > 0.7 ? 'text-red-600' :
              result.ai_probability > 0.4 ? 'text-yellow-600' :
              'text-green-600'
            }`}>
              {(result.ai_probability * 100).toFixed(1)}%
            </span>
          </div>
          <div className="mt-2">
            <span className="text-sm text-gray-600">
              Confidence: {result.confidence}
            </span>
          </div>
          <div className="mt-4 p-3 bg-white rounded border">
            <p className="text-sm">{result.recommendation || 'No recommendation'}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// frontend/src/components/Paraphraser.tsx
export function Paraphraser() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [style, setStyle] = useState('academic');
  
  const handleParaphrase = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai-tools/paraphrase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, style, preserve_citations: true })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Paraphrasing failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="paraphraser">
      <h3>Academic Paraphraser</h3>
      
      <select
        value={style}
        onChange={(e) => setStyle(e.target.value)}
        className="mb-2 px-4 py-2 border rounded-lg"
      >
        <option value="academic">Academic</option>
        <option value="simple">Simple</option>
        <option value="technical">Technical</option>
      </select>
      
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste text to paraphrase..."
        className="w-full h-40 p-4 border rounded-lg"
      />
      <button
        onClick={handleParaphrase}
        disabled={loading || !text}
        className="mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg"
      >
        {loading ? 'Paraphrasing...' : 'Paraphrase'}
      </button>
      
      {result && (
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div>
            <h4 className="font-semibold mb-2">Original</h4>
            <div className="p-4 bg-gray-50 rounded-lg">
              {result.original}
            </div>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Paraphrased</h4>
            <div className="p-4 bg-green-50 rounded-lg">
              {result.paraphrased}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

**Success Criteria:**
- ✅ Components render correctly
- ✅ Real-time analysis works
- ✅ Results display clearly
- ✅ Copy/paste functionality

**Files to create:**
- `frontend/src/components/AIDetector.tsx`
- `frontend/src/components/Paraphraser.tsx`
- Update `frontend/src/pages/Workspace.tsx`

---

## 🔒 **Security & Production (Week 9-10)**

### **Phase 5: Production Readiness**

#### Task 5.1: Authentication System (Week 9)
**Estimated Time:** 16 hours  
**Impact:** Security requirement  
**Status:** ⏳ Ready to implement

**Steps:**
1. Create JWT authentication
2. Add user registration/login endpoints
3. Protect user-specific endpoints
4. Add frontend auth flow
5. Test security

**Files to create:**
- `backend/app/core/security.py`
- `backend/app/api/v1/auth.py`
- `frontend/src/contexts/AuthContext.tsx`

---

#### Task 5.2: Rate Limiting (Week 9)
**Estimated Time:** 4 hours  
**Impact:** Cost control  
**Status:** ⏳ Ready to implement

**Steps:**
1. Install slowapi
2. Add rate limiting to endpoints
3. Configure limits per tier
4. Test rate limiting

**Dependencies:**
```bash
pip install slowapi
```

---

#### Task 5.3: Monitoring & Logging (Week 10)
**Estimated Time:** 8 hours  
**Impact:** Observability  
**Status:** ⏳ Ready to implement

**Steps:**
1. Set up Sentry for error tracking
2. Add structured logging
3. Create analytics dashboard
4. Set up uptime monitoring

**Dependencies:**
```bash
pip install sentry-sdk python-json-logger
```

---

#### Task 5.4: Deployment (Week 10)
**Estimated Time:** 8 hours  
**Impact:** Go live  
**Status:** ⏳ Ready to implement

**Steps:**
1. Deploy backend to Railway
2. Deploy frontend to Vercel/Cloudflare
3. Configure environment variables
4. Set up database backups
5. Test production environment

---

## 📊 **Progress Tracking**

### **Week 1-2: Performance** ⚡
- [ ] Database indexing (30 min)
- [ ] Connection pooling (15 min)
- [ ] Pagination (2 hours)
- [ ] Testing (2 hours)

**Total: ~5 hours**

### **Week 3-4: DOI Fetching** 🔍
- [ ] API endpoint (3 hours)
- [ ] Frontend component (4 hours)
- [ ] Testing (2 hours)

**Total: ~9 hours**

### **Week 5-6: Document Generation** 📄
- [ ] Formatter service (8 hours)
- [ ] LLM integration (8 hours)
- [ ] API endpoint (4 hours)
- Email: $0-20
- Monitoring: $0-26
- **Total: $21-117/month**

### **API Costs (per 1,000 users):**
- GPT-5 nano (document generation): $30-80
- Gemini 2.0 Flash (optional): $50-80
- **Total: $30-160/month**

---

## 🎯 **Success Metrics**

### **Performance:**
- ✅ Search queries < 50ms
- ✅ Page load < 2 seconds
- ✅ Uptime > 99.9%

### **Features:**
- ✅ DOI fetching works
- ✅ Document generation works
- ✅ All citation styles supported

### **Quality:**
- ✅ Test coverage > 80%
- ✅ No critical bugs
- ✅ Error rate < 0.1%

### **Business:**
- ✅ 100+ active users
- ✅ 1,000+ searches/month
- ✅ 50+ documents generated

---

## 📝 **Next Steps**

1. **Start with Week 1-2** (Performance fixes)
   - Run database migration
   - Add connection pooling
   - Implement pagination

2. **Then Week 3-4** (DOI fetching)
   - Create API endpoint
   - Build frontend component
   - Test integration

3. **Then Week 5-6** (Document generation)
   - Build formatter service
   - Integrate LLM
   - Create frontend UI

4. **Finally Week 7-8** (Production)
   - Add authentication
   - Set up monitoring
   - Deploy to production

---

## 📚 **Resources**

- **Database Analysis:** `DATABASE_ARCHITECTURE_ANALYSIS.md`
- **Sustainability Plan:** `LONG_TERM_SUSTAINABILITY_PLAN.md`
- **Cost Analysis:** `COST_ANALYSIS.md`
- **Integration Status:** `INTEGRATION_STATUS.md`
- **Quick Start:** `QUICK_START.md`

---

**Last Updated:** 2025-11-22  
**Status:** Ready to start implementation  
**Next Milestone:** Week 1-2 Performance Fixes
