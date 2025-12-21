
## 📄 **Part C: AI Document Formatting & Journal Compliance**

### **Task 2.10: Journal Requirements Database** (2 hours)

**Create database of journal formatting requirements:**

```python
# backend/app/models/journal_requirements.py
from sqlalchemy import Column, Integer, String, JSON, Text

class JournalRequirement(Base):
    """Store formatting requirements for academic journals"""
    __tablename__ = "journal_requirements"
    
    id = Column(Integer, primary_key=True)
    journal_name = Column(String(200), unique=True, index=True)
    publisher = Column(String(100))
    field = Column(String(50))  # "Computer Science", "Medicine", etc.
    
    # Citation style
    citation_style = Column(String(20))  # "APA", "IEEE", "Chicago", "Vancouver", "Harvard"
    
    # Document structure
    required_sections = Column(JSON)  # ["Abstract", "Introduction", "Methods", ...]
    section_order = Column(JSON)  # Order of sections
    
    # Formatting rules
    word_count_limits = Column(JSON)  # {"abstract": 250, "total": 8000}
    font_requirements = Column(JSON)  # {"family": "Times New Roman", "size": 12}
    line_spacing = Column(Float)  # 1.5, 2.0, etc.
    margins = Column(JSON)  # {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0}
    
    # Reference formatting
    reference_style = Column(Text)  # Detailed reference format
    max_references = Column(Integer)  # Maximum number of references
    
    # Special requirements
    special_requirements = Column(JSON)  # Any special rules
    
    # Examples
    example_paper_url = Column(String(500))  # Link to example paper
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Seed data for popular journals
JOURNAL_REQUIREMENTS = [
    {
        "journal_name": "Nature",
        "publisher": "Springer Nature",
        "field": "Multidisciplinary",
        "citation_style": "Nature",
        "required_sections": ["Abstract", "Introduction", "Results", "Discussion", "Methods", "References"],
        "word_count_limits": {"abstract": 200, "total": 5000},
        "font_requirements": {"family": "Arial", "size": 12},
        "line_spacing": 2.0,
        "reference_style": "Numbered in order of appearance"
    },
    {
        "journal_name": "IEEE Transactions",
        "publisher": "IEEE",
        "field": "Computer Science",
        "citation_style": "IEEE",
        "required_sections": ["Abstract", "Introduction", "Related Work", "Methodology", "Results", "Conclusion", "References"],
        "word_count_limits": {"abstract": 250, "total": 8000},
        "font_requirements": {"family": "Times New Roman", "size": 10},
        "line_spacing": 1.0
    },
    {
        "journal_name": "PLOS ONE",
        "publisher": "PLOS",
        "field": "Multidisciplinary",
        "citation_style": "Vancouver",
        "required_sections": ["Abstract", "Introduction", "Materials and Methods", "Results", "Discussion", "Conclusions", "References"],
        "word_count_limits": {"abstract": 300, "total": 15000},
        "font_requirements": {"family": "Times New Roman", "size": 12},
        "line_spacing": 2.0
    }
]
```

---

### **Task 2.11: AI Document Formatter Service** (4 hours)

```python
# backend/app/services/ai_document_formatter_service.py
from typing import Dict, List
import openai
from docx import Document
from docx.shared import Pt, Inches

class AIDocumentFormatterService:
    """AI-powered document formatting for journal compliance"""
    
    def __init__(self):
        self.llm_client = openai.AsyncOpenAI()
    
    async def format_for_journal(
        self,
        document_content: str,
        journal_name: str,
        user_id: str,
        db: Session
    ) -> Dict:
        """
        Format user's document to match journal requirements
        
        Example:
        User writes: "I studied machine learning models..."
        AI formats to: Proper sections, citations, references, word count
        """
        # Get journal requirements
        journal = db.query(JournalRequirement).filter(
            JournalRequirement.journal_name == journal_name
        ).first()
        
        if not journal:
            raise ValueError(f"Journal '{journal_name}' not found in database")
        
        # Get user's saved papers for citations
        user_papers = await self._get_user_papers(user_id, db)
        
        # Step 1: Analyze document structure
        analysis = await self._analyze_document(document_content, journal)
        
        # Step 2: Reformat document
        formatted_content = await self._reformat_document(
            document_content,
            journal,
            user_papers,
            analysis
        )
        
        # Step 3: Fix citations and references
        formatted_content = await self._fix_citations(
            formatted_content,
            journal.citation_style,
            user_papers
        )
        
        # Step 4: Generate Word document
        doc = self._create_word_document(formatted_content, journal)
        
        return {
            "formatted_content": formatted_content,
            "document": doc,
            "compliance_report": analysis,
            "journal": journal.journal_name
        }
    
    async def _analyze_document(
        self,
        content: str,
        journal: JournalRequirement
    ) -> Dict:
        """Analyze if document meets journal requirements"""
        
        prompt = f"""
        Analyze this academic document for compliance with {journal.journal_name} requirements.
        
        Requirements:
        - Required sections: {journal.required_sections}
        - Word count limits: {journal.word_count_limits}
        - Citation style: {journal.citation_style}
        
        Document:
        {content}
        
        Provide analysis in JSON format:
        {{
            "missing_sections": [],
            "word_count_issues": {{}},
            "citation_issues": [],
            "structure_issues": [],
            "compliance_score": 0-100
        }}
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are an academic publishing expert."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _reformat_document(
        self,
        content: str,
        journal: JournalRequirement,
        user_papers: List[Paper],
        analysis: Dict
    ) -> str:
        """Reformat document to match journal requirements"""
        
        prompt = f"""
        Reformat this academic document to comply with {journal.journal_name} requirements.
        
        Requirements:
        1. Sections: {journal.required_sections} (in this order: {journal.section_order})
        2. Word limits: {journal.word_count_limits}
        3. Citation style: {journal.citation_style}
        
        Current issues found:
        {json.dumps(analysis, indent=2)}
        
        Original document:
        {content}
        
        Available papers to cite:
        {self._format_papers_for_citation(user_papers)}
        
        Instructions:
        - Reorganize into required sections
        - Ensure word count compliance
        - Add proper citations in {journal.citation_style} style
        - Maintain academic tone
        - Keep all original research content
        - Add section headings
        
        Return the reformatted document.
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are an academic writing expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    async def _fix_citations(
        self,
        content: str,
        citation_style: str,
        user_papers: List[Paper]
    ) -> str:
        """Convert all citations to the correct style"""
        
        prompt = f"""
        Fix all citations in this document to use {citation_style} style.
        
        Document:
        {content}
        
        Available papers:
        {self._format_papers_for_citation(user_papers)}
        
        Rules for {citation_style}:
        {self._get_citation_rules(citation_style)}
        
        Return the document with corrected citations.
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a citation expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for accuracy
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    def _create_word_document(
        self,
        content: str,
        journal: JournalRequirement
    ) -> Document:
        """Create properly formatted Word document"""
        
        doc = Document()
        
        # Apply journal formatting
        style = doc.styles['Normal']
        font = style.font
        font.name = journal.font_requirements.get('family', 'Times New Roman')
        font.size = Pt(journal.font_requirements.get('size', 12))
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(journal.margins.get('top', 1.0))
            section.bottom_margin = Inches(journal.margins.get('bottom', 1.0))
            section.left_margin = Inches(journal.margins.get('left', 1.0))
            section.right_margin = Inches(journal.margins.get('right', 1.0))
        
        # Set line spacing
        paragraph_format = style.paragraph_format
        paragraph_format.line_spacing = journal.line_spacing
        
        # Add content (parse markdown/sections)
        sections_content = self._parse_sections(content)
        for section in sections_content:
            doc.add_heading(section['title'], level=1)
            doc.add_paragraph(section['content'])
        
        return doc
    
    def _get_citation_rules(self, style: str) -> str:
        """Get citation formatting rules"""
        rules = {
            "APA": "In-text: (Author, Year). References: Author, A. A. (Year). Title. Journal, Volume(Issue), pages.",
            "IEEE": "In-text: [1]. References: [1] A. Author, \"Title,\" Journal, vol. X, no. Y, pp. Z, Year.",
            "Chicago": "In-text: (Author Year). References: Author. \"Title.\" Journal Volume, no. Issue (Year): pages.",
            "Vancouver": "In-text: (1). References: 1. Author AA. Title. Journal. Year;Volume(Issue):pages.",
            "Harvard": "In-text: (Author Year). References: Author, A. (Year) 'Title', Journal, Volume(Issue), pp. pages."
        }
        return rules.get(style, "Standard academic citation format")
    
    def _format_papers_for_citation(self, papers: List[Paper]) -> str:
        """Format user's papers for citation"""
        formatted = []
        for i, paper in enumerate(papers, 1):
            authors = ', '.join([a['name'] for a in paper.authors[:3]])
            formatted.append(f"{i}. {authors} ({paper.publication_date.year}). {paper.title}. {paper.source}.")
        return '\n'.join(formatted)
```

---

### **Task 2.12: Frontend Document Formatter UI** (2 hours)

```typescript
// frontend/src/components/workspace/DocumentFormatter.tsx
import { useState } from 'react';

export function DocumentFormatter() {
  const [content, setContent] = useState('');
  const [selectedJournal, setSelectedJournal] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  
  const journals = [
    { name: "Nature", field: "Multidisciplinary" },
    { name: "IEEE Transactions", field: "Computer Science" },
    { name: "PLOS ONE", field: "Multidisciplinary" },
    { name: "Science", field: "Multidisciplinary" },
    { name: "Cell", field: "Biology" },
    { name: "The Lancet", field: "Medicine" }
  ];
  
  const handleFormat = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai-formatter/format-for-journal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          journal_name: selectedJournal
        })
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Formatting failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="document-formatter">
      <div className="formatter-header">
        <h2>📄 AI Document Formatter</h2>
        <p>Format your document to match journal requirements</p>
      </div>
      
      <div className="formatter-controls">
        <label>Select Target Journal:</label>
        <select
          value={selectedJournal}
          onChange={(e) => setSelectedJournal(e.target.value)}
          className="journal-select"
        >
          <option value="">Choose a journal...</option>
          {journals.map(j => (
            <option key={j.name} value={j.name}>
              {j.name} ({j.field})
            </option>
          ))}
        </select>
      </div>
      
      <div className="formatter-editor">
        <label>Your Document:</label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Paste your document here..."
          className="document-input"
          rows={20}
        />
      </div>
      
      <button
        onClick={handleFormat}
        disabled={loading || !content || !selectedJournal}
        className="format-button"
      >
        {loading ? 'Formatting...' : '✨ Format for Journal'}
      </button>
      
      {result && (
        <div className="formatter-results">
          <div className="compliance-report">
            <h3>Compliance Report</h3>
            <div className="compliance-score">
              Score: {result.compliance_report.compliance_score}/100
            </div>
            
            {result.compliance_report.missing_sections.length > 0 && (
              <div className="issues">
                <h4>Missing Sections:</h4>
                <ul>
                  {result.compliance_report.missing_sections.map((section, i) => (
                    <li key={i}>{section}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {result.compliance_report.word_count_issues && (
              <div className="issues">
                <h4>Word Count Issues:</h4>
                <pre>{JSON.stringify(result.compliance_report.word_count_issues, null, 2)}</pre>
              </div>
            )}
          </div>
          
          <div className="formatted-document">
            <h3>Formatted Document</h3>
            <div className="document-preview">
              {result.formatted_content}
            </div>
            
            <button onClick={() => downloadDocument(result.document)}>
              📥 Download Word Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 📊 **Phase 2 Complete Summary**

### **Timeline:**
- **Part A:** Workspace UI (20 hours)
- **Part B:** RAG AI Assistant (20 hours)
- **Part C:** AI Document Formatting (8 hours)
- **Total: 48 hours** (Week 3-4)

### **What You Get:**

#### **Workspace Improvements:**
1. ✅ Beautiful redesigned layout
2. ✅ Drag-and-drop organization
3. ✅ Collections and folders
4. ✅ Keyboard shortcuts
5. ✅ Multiple view modes
6. ✅ Enhanced paper cards

#### **Intelligent AI Assistant:**
7. ✅ RAG system with access to your data
8. ✅ Answer questions about your research
9. ✅ Summarize your notes
10. ✅ Edit literature reviews
11. ✅ Context-aware suggestions

#### **AI Document Formatting:** ⭐ **NEW!**
12. ✅ Format documents for any journal
13. ✅ Automatic citation style conversion
14. ✅ Reference list formatting
15. ✅ Compliance checking
16. ✅ Word count management
17. ✅ Section structure compliance

### **Example Use Cases:**

**Scenario 1: Writing for Nature**
```
User: "I wrote this paper, format it for Nature"
AI: 
- Analyzes document
- Finds missing "Methods" section
- Converts citations to Nature style (numbered)
- Reduces abstract to 200 words
- Reformats references
- Generates compliant Word document
```

**Scenario 2: Switching Journals**
```
User: "I wrote this for IEEE, but now I want to submit to PLOS ONE"
AI:
- Converts IEEE citations [1] to Vancouver (1)
- Reorganizes sections
- Adjusts word counts
- Changes font and spacing
- Updates reference format
```

**Scenario 3: Citation Management**
```
User: "Add citations from my saved papers about transformers"
AI:
- Finds relevant papers in user's library
- Adds proper in-text citations
- Generates reference list
- Maintains citation style consistency
```

### **Cost:**
- GPT-5 mini for formatting: $0.15/1M input, $0.60/1M output
- Average document: ~5,000 words = ~7,000 tokens
- Cost per format: ~$0.005 (half a cent!)
- **Very affordable** ✅

### **Dependencies:**
```bash
# Backend
pip install python-docx openai sentence-transformers scikit-learn

# Frontend
npm install @dnd-kit/core @dnd-kit/sortable
```

---

## ✅ **Success Criteria**

- [ ] Workspace loads in < 2 seconds
- [ ] Drag-and-drop works smoothly
- [ ] All keyboard shortcuts functional
- [ ] AI answers questions accurately (>80% relevance)
- [ ] AI can edit reviews coherently
- [ ] **Document formatting matches journal requirements (>90% compliance)**
- [ ] **Citations converted correctly (100% accuracy)**
- [ ] Mobile-responsive design
- [ ] No performance degradation with 1000+ papers

---

**This transforms your app into a complete research workflow platform!** 🚀

Users can:
1. Search and save papers
2. Organize with AI assistance
3. Take notes and highlights
4. Write literature reviews
5. **Format for any journal** ⭐
6. **Auto-fix citations** ⭐
7. Submit with confidence!
