# Phase 4: Document Generation & Citation Management
## AI-Powered Literature Review Generation with Multiple Citation Styles

**Timeline:** Week 6-7 (~30 hours)  
**Priority:** HIGH - Core research feature  
**Impact:** Save users hours of manual writing

---

## 🎯 **Phase 4 Objectives**

1. Generate formatted literature reviews from saved papers
2. Support multiple citation styles (APA, IEEE, Chicago, Vancouver, Harvard)
3. LLM-powered content generation
4. Export to Word, PDF, LaTeX, BibTeX
5. Integration with citation management

---

## 📄 **Task 4.1: Document Formatter Service** (8 hours)

```python
# backend/app/services/document_formatter_service.py
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import List, Dict

class AcademicDocumentFormatter:
    """Format academic documents with proper styling"""
    
    STYLES = {
        "apa": {
            "font": "Times New Roman",
            "font_size": 12,
            "line_spacing": 2.0,
            "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
        },
        "ieee": {
            "font": "Times New Roman",
            "font_size": 10,
            "line_spacing": 1.0,
            "margins": {"top": 0.75, "bottom": 1.0, "left": 0.625, "right": 0.625}
        },
        "chicago": {
            "font": "Times New Roman",
            "font_size": 12,
            "line_spacing": 2.0,
            "margins": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
        }
    }
    
    def create_literature_review(
        self,
        papers: List[Dict],
        style: str = "apa",
        llm_service = None
    ) -> Document:
        """Create formatted literature review document"""
        doc = Document()
        
        # Apply style settings
        self._apply_document_style(doc, style)
        
        # Generate content with LLM
        if llm_service:
            content = await llm_service.generate_literature_review(papers)
        else:
            content = self._generate_basic_review(papers)
        
        # Add title
        title = doc.add_heading('Literature Review', level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add introduction
        doc.add_heading('Introduction', level=1)
        doc.add_paragraph(content['introduction'])
        
        # Add main sections
        for section in content['sections']:
            doc.add_heading(section['title'], level=1)
            doc.add_paragraph(section['content'])
        
        # Add references
        doc.add_page_break()
        doc.add_heading('References', level=1)
        for paper in papers:
            self._add_reference(doc, paper, style)
        
        return doc
```

See `LONG_TERM_SUSTAINABILITY_PLAN.md` Part 6 for complete implementation.

**Dependencies:**
```bash
pip install python-docx openai
```

---

## 🤖 **Task 4.2: LLM Integration** (8 hours)

```python
# backend/app/services/llm_document_service.py
class LLMDocumentService:
    """Use LLM to generate academic document content"""
    
    async def generate_literature_review(
        self,
        papers: List[Dict],
        focus_area: str = None
    ) -> Dict:
        """Generate literature review content using LLM"""
        # Generate introduction
        # Identify themes
        # Generate sections
        # Generate conclusion
        return content
```

**Cost:** ~$0.0013 per review (GPT-5 nano)

---

## 🌐 **Task 4.3: API Endpoints** (4 hours)

```python
# backend/app/api/v1/documents.py
@router.post("/documents/generate-literature-review")
async def generate_literature_review(
    paper_ids: List[int],
    style: str = "apa",
    focus_area: Optional[str] = None,
    use_llm: bool = True,
    db: Session = Depends(get_db)
):
    """Generate formatted literature review document"""
    # Implementation
    return FileResponse(filepath, filename="literature_review.docx")
```

---

## 🎨 **Task 4.4: Frontend Component** (6 hours)

```typescript
// frontend/src/components/DocumentGenerator.tsx
export function DocumentGenerator({ selectedPapers }: { selectedPapers: Paper[] }) {
  const [style, setStyle] = useState<'apa' | 'ieee' | 'chicago'>('apa');
  const [focusArea, setFocusArea] = useState('');
  const [useLLM, setUseLLM] = useState(true);
  
  return (
    <div className="document-generator">
      <h3>Generate Literature Review</h3>
      <select value={style} onChange={(e) => setStyle(e.target.value as any)}>
        <option value="apa">APA 7th Edition</option>
        <option value="ieee">IEEE</option>
        <option value="chicago">Chicago</option>
      </select>
      <button onClick={handleGenerate}>
        Generate Review ({selectedPapers.length} papers)
      </button>
    </div>
  );
}
```

---

## 🧪 **Task 4.5: Testing** (4 hours)

```python
@pytest.mark.asyncio
async def test_generate_review():
    """Test literature review generation"""
    formatter = AcademicDocumentFormatter()
    doc = await formatter.create_literature_review(
        papers=test_papers,
        style="apa"
    )
    assert doc is not None
```

---

## ✅ **Success Criteria**

- [ ] Generates properly formatted Word documents
- [ ] All 3 citation styles work correctly
- [ ] LLM content is coherent and academic
- [ ] Export to multiple formats works
- [ ] Cost < $0.01 per review
- [ ] All tests pass

**Total Time:** ~30 hours  
**Total Cost:** ~$0.0013 per document
