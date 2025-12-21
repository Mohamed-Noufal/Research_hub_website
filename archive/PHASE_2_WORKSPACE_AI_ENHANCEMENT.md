# Phase 2: Workspace Optimization & Intelligent AI Assistant
## Complete UI/UX Overhaul + RAG-Powered AI Assistant + Smart Document Formatting

**Timeline:** Week 3-4 (48 hours)  
**Priority:** HIGH - Core user experience  
**Impact:** Transform app from basic search to intelligent research assistant

---

## 🎯 **Phase 2 Objectives**

### **Part A: Workspace UI/UX Optimization** (20 hours)
1. Redesign workspace layout and workflow
2. Add new UI components
3. Improve paper management interface
4. Optimize user interactions
5. Add keyboard shortcuts
6. Improve mobile responsiveness

### **Part B: Intelligent AI Assistant with RAG** (20 hours)
1. Build RAG system with access to user's data
2. AI can read saved papers
3. AI can access notes and highlights
4. AI can edit literature reviews
5. AI can answer questions about user's research
6. Context-aware suggestions

### **Part C: AI Document Formatting & Journal Compliance** (8 hours) ⭐ **NEW!**
1. AI formats documents to match journal requirements
2. Automatic citation style conversion
3. Reference list formatting
4. Document structure compliance
5. Word count and section requirements
6. Integration with citation management

---

## 📐 **Part A: Workspace UI/UX Optimization**

### **Task 2.1: Workspace Layout Redesign** (6 hours)

**Current Issues:**
- Basic layout, not optimized for research workflow
- No drag-and-drop
- Limited organization options
- Poor visual hierarchy

**New Design:**

```typescript
// frontend/src/pages/Workspace.tsx - NEW LAYOUT

export function Workspace() {
  return (
    <div className="workspace-container">
      {/* Left Sidebar - Collections & Folders */}
      <aside className="workspace-sidebar">
        <CollectionsList />
        <FolderTree />
        <TagCloud />
      </aside>
      
      {/* Main Content - Papers Grid/List */}
      <main className="workspace-main">
        <WorkspaceToolbar />
        <PapersView mode={viewMode} />
      </main>
      
      {/* Right Panel - AI Assistant + Details */}
      <aside className="workspace-right-panel">
        <AIAssistant />
        <PaperDetails />
      </aside>
    </div>
  );
}
```

**New Components to Create:**

1. **CollectionsList** - Organize papers into collections
```typescript
// frontend/src/components/workspace/CollectionsList.tsx
export function CollectionsList() {
  const [collections, setCollections] = useState([
    { id: 1, name: "To Read", count: 12, color: "blue" },
    { id: 2, name: "Favorites", count: 8, color: "red" },
    { id: 3, name: "Cited in Paper", count: 15, color: "green" }
  ]);
  
  return (
    <div className="collections-list">
      <h3>Collections</h3>
      {collections.map(collection => (
        <CollectionItem key={collection.id} {...collection} />
      ))}
      <button onClick={createCollection}>+ New Collection</button>
    </div>
  );
}
```

2. **FolderTree** - Hierarchical organization
```typescript
// frontend/src/components/workspace/FolderTree.tsx
export function FolderTree() {
  return (
    <div className="folder-tree">
      <h3>Folders</h3>
      <TreeView>
        <Folder name="Machine Learning">
          <Folder name="Deep Learning" />
          <Folder name="NLP" />
        </Folder>
        <Folder name="Computer Vision" />
      </TreeView>
    </div>
  );
}
```

3. **WorkspaceToolbar** - Quick actions
```typescript
// frontend/src/components/workspace/WorkspaceToolbar.tsx
export function WorkspaceToolbar() {
  return (
    <div className="workspace-toolbar">
      <SearchBar />
      <ViewToggle /> {/* Grid / List / Compact */}
      <SortDropdown /> {/* Date, Title, Citations */}
      <FilterButton />
      <BulkActions /> {/* Select all, Delete, Move */}
    </div>
  );
}
```

4. **PapersView** - Multiple view modes
```typescript
// frontend/src/components/workspace/PapersView.tsx
export function PapersView({ mode }: { mode: 'grid' | 'list' | 'compact' }) {
  if (mode === 'grid') return <PapersGrid />;
  if (mode === 'list') return <PapersList />;
  return <PapersCompact />;
}
```

**Success Criteria:**
- ✅ Drag-and-drop papers between folders
- ✅ Multi-select with Shift+Click
- ✅ Keyboard shortcuts (Ctrl+A, Delete, etc.)
- ✅ Smooth animations
- ✅ Responsive on tablet/mobile

---

### **Task 2.2: Enhanced Paper Cards** (4 hours)

**New Features:**

```typescript
// frontend/src/components/workspace/EnhancedPaperCard.tsx
export function EnhancedPaperCard({ paper }: { paper: Paper }) {
  return (
    <div className="paper-card">
      {/* Quick Preview on Hover */}
      <div className="paper-card-preview">
        <img src={paper.thumbnail} alt="Paper preview" />
      </div>
      
      {/* Paper Info */}
      <div className="paper-card-content">
        <h3>{paper.title}</h3>
        <p className="authors">{formatAuthors(paper.authors)}</p>
        <p className="excerpt">{paper.abstract.slice(0, 150)}...</p>
        
        {/* Tags */}
        <div className="paper-tags">
          {paper.tags.map(tag => <Tag key={tag}>{tag}</Tag>)}
        </div>
        
        {/* Metadata */}
        <div className="paper-metadata">
          <span>📅 {formatDate(paper.publication_date)}</span>
          <span>📊 {paper.citation_count} citations</span>
          <span>⭐ {paper.user_rating}/5</span>
        </div>
        
        {/* Quick Actions */}
        <div className="paper-actions">
          <button onClick={() => openPDF(paper)}>📄 PDF</button>
          <button onClick={() => addNote(paper)}>📝 Note</button>
          <button onClick={() => cite(paper)}>📚 Cite</button>
          <button onClick={() => askAI(paper)}>🤖 Ask AI</button>
        </div>
      </div>
      
      {/* Reading Progress */}
      <div className="reading-progress">
        <ProgressBar value={paper.reading_progress} />
      </div>
    </div>
  );
}
```

**New Fields to Add to Database:**
```sql
ALTER TABLE user_saved_papers ADD COLUMN user_rating INTEGER;
ALTER TABLE user_saved_papers ADD COLUMN reading_progress INTEGER DEFAULT 0;
ALTER TABLE user_saved_papers ADD COLUMN last_opened_at TIMESTAMP;
ALTER TABLE user_saved_papers ADD COLUMN thumbnail_url VARCHAR(500);
```

---

### **Task 2.3: Keyboard Shortcuts** (2 hours)

```typescript
// frontend/src/hooks/useKeyboardShortcuts.ts
export function useKeyboardShortcuts() {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Search
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        openSearch();
      }
      
      // Select all
      if (e.ctrlKey && e.key === 'a') {
        e.preventDefault();
        selectAllPapers();
      }
      
      // Delete selected
      if (e.key === 'Delete') {
        deleteSelectedPapers();
      }
      
      // Open AI assistant
      if (e.ctrlKey && e.key === '/') {
        e.preventDefault();
        openAIAssistant();
      }
      
      // Quick add to collection
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        addToCollection();
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);
}
```

**Shortcuts to Implement:**
- `Ctrl+K` - Quick search
- `Ctrl+A` - Select all
- `Delete` - Delete selected
- `Ctrl+/` - Open AI assistant
- `Ctrl+S` - Save to collection
- `Ctrl+N` - New note
- `Ctrl+L` - New literature review
- `Esc` - Close modals

---

### **Task 2.4: Drag & Drop Interface** (4 hours)

```typescript
// frontend/src/components/workspace/DragDropWorkspace.tsx
import { DndContext, DragOverlay } from '@dnd-kit/core';

export function DragDropWorkspace() {
  const handleDragEnd = (event) => {
    const { active, over } = event;
    
    if (over && over.id.startsWith('folder-')) {
      // Move paper to folder
      movePaperToFolder(active.id, over.id);
    } else if (over && over.id.startsWith('collection-')) {
      // Add paper to collection
      addPaperToCollection(active.id, over.id);
    }
  };
  
  return (
    <DndContext onDragEnd={handleDragEnd}>
      <FolderTree />
      <PapersGrid />
      <DragOverlay>
        {activeId ? <PaperCard id={activeId} /> : null}
      </DragOverlay>
    </DndContext>
  );
}
```

**Dependencies:**
```bash
npm install @dnd-kit/core @dnd-kit/sortable
```

---

### **Task 2.5: API Endpoint Improvements** (4 hours)

**New Endpoints:**

```python
# backend/app/api/v1/workspace.py
from fastapi import APIRouter, Depends
from typing import List, Optional

router = APIRouter()

@router.get("/workspace/collections")
async def get_collections(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's collections"""
    collections = db.query(Collection).filter(
        Collection.user_id == user_id
    ).all()
    return {"collections": collections}


@router.post("/workspace/collections")
async def create_collection(
    name: str,
    color: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new collection"""
    collection = Collection(
        user_id=user_id,
        name=name,
        color=color
    )
    db.add(collection)
    db.commit()
    return collection


@router.post("/workspace/papers/{paper_id}/move")
async def move_paper(
    paper_id: int,
    folder_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move paper to folder"""
    saved_paper = db.query(UserSavedPaper).filter(
        UserSavedPaper.paper_id == paper_id,
        UserSavedPaper.user_id == user_id
    ).first()
    
    saved_paper.folder_id = folder_id
    db.commit()
    return {"success": True}


@router.post("/workspace/papers/bulk-action")
async def bulk_action(
    paper_ids: List[int],
    action: str,  # "delete", "move", "tag"
    target: Optional[int] = None,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Perform bulk action on papers"""
    if action == "delete":
        db.query(UserSavedPaper).filter(
            UserSavedPaper.paper_id.in_(paper_ids),
            UserSavedPaper.user_id == user_id
        ).delete()
    elif action == "move":
        db.query(UserSavedPaper).filter(
            UserSavedPaper.paper_id.in_(paper_ids),
            UserSavedPaper.user_id == user_id
        ).update({"folder_id": target})
    
    db.commit()
    return {"success": True, "count": len(paper_ids)}
```

---

## 🤖 **Part B: Intelligent AI Assistant with RAG**

### **Task 2.6: RAG System Architecture** (8 hours)

**What is RAG?**
Retrieval-Augmented Generation - AI that can access and reason about your saved papers, notes, and literature reviews.

**Architecture:**

```python
# backend/app/services/rag_assistant_service.py
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import openai

class RAGAssistantService:
    """Intelligent AI assistant with access to user's research data"""
    
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm_client = openai.AsyncOpenAI()
    
    async def answer_question(
        self,
        user_id: str,
        question: str,
        db: Session
    ) -> Dict:
        """
        Answer user's question using their saved papers and notes
        
        Example questions:
        - "What papers do I have about deep learning?"
        - "Summarize my notes on transformer models"
        - "What are the main findings in my saved papers?"
        - "Help me write a literature review on NLP"
        """
        # Step 1: Retrieve relevant context from user's data
        context = await self._retrieve_context(user_id, question, db)
        
        # Step 2: Generate answer using LLM + context
        answer = await self._generate_answer(question, context)
        
        # Step 3: Return answer with sources
        return {
            "answer": answer,
            "sources": context["sources"],
            "confidence": context["confidence"]
        }
    
    async def _retrieve_context(
        self,
        user_id: str,
        question: str,
        db: Session
    ) -> Dict:
        """Retrieve relevant papers, notes, and reviews"""
        
        # Generate question embedding
        question_embedding = self.embedder.encode(question)
        
        # Search user's saved papers
        saved_papers = db.query(UserSavedPaper).filter(
            UserSavedPaper.user_id == user_id
        ).all()
        
        # Get paper details with embeddings
        papers_with_embeddings = []
        for saved in saved_papers:
            paper = db.query(Paper).filter(Paper.id == saved.paper_id).first()
            if paper and paper.embedding:
                papers_with_embeddings.append({
                    "paper": paper,
                    "embedding": paper.embedding,
                    "saved_at": saved.saved_at,
                    "tags": saved.tags
                })
        
        # Calculate similarity scores
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        similarities = []
        for item in papers_with_embeddings:
            similarity = cosine_similarity(
                [question_embedding],
                [item["embedding"]]
            )[0][0]
            similarities.append({
                "paper": item["paper"],
                "similarity": similarity,
                "tags": item["tags"]
            })
        
        # Sort by relevance
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        top_papers = similarities[:5]  # Top 5 most relevant
        
        # Get user's notes on these papers
        notes = []
        for item in top_papers:
            paper_notes = db.query(UserNote).filter(
                UserNote.user_id == user_id,
                UserNote.paper_id == item["paper"].id
            ).all()
            notes.extend(paper_notes)
        
        # Get user's literature reviews
        reviews = db.query(UserLiteratureReview).filter(
            UserLiteratureReview.user_id == user_id
        ).all()
        
        # Compile context
        context = {
            "papers": top_papers,
            "notes": notes,
            "reviews": reviews,
            "sources": [p["paper"].title for p in top_papers],
            "confidence": np.mean([p["similarity"] for p in top_papers])
        }
        
        return context
    
    async def _generate_answer(
        self,
        question: str,
        context: Dict
    ) -> str:
        """Generate answer using LLM with context"""
        
        # Build context string
        context_str = self._format_context(context)
        
        # Create prompt
        prompt = f"""
        You are an intelligent research assistant helping a researcher.
        
        The researcher has asked: "{question}"
        
        Here is the relevant information from their saved papers and notes:
        
        {context_str}
        
        Provide a helpful, accurate answer based on this information.
        If you cite information, mention which paper it came from.
        If the information isn't in the context, say so.
        """
        
        # Call LLM
        response = await self.llm_client.chat.completions.create(
            model="gpt-5-nano",  # Cheap and fast
            messages=[
                {"role": "system", "content": "You are a research assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def _format_context(self, context: Dict) -> str:
        """Format context for LLM"""
        formatted = []
        
        # Add papers
        for item in context["papers"]:
            paper = item["paper"]
            formatted.append(f"""
            Paper: {paper.title}
            Authors: {', '.join([a['name'] for a in paper.authors])}
            Abstract: {paper.abstract[:300]}...
            Relevance: {item['similarity']:.2f}
            """)
        
        # Add notes
        for note in context["notes"]:
            formatted.append(f"""
            Note: {note.content}
            """)
        
        # Add reviews
        for review in context["reviews"]:
            formatted.append(f"""
            Literature Review: {review.title}
            Content: {review.content[:500]}...
            """)
        
        return "\n\n".join(formatted)
```

---

### **Task 2.7: AI Assistant UI Component** (6 hours)

```typescript
// frontend/src/components/workspace/AIAssistant.tsx
import { useState } from 'react';

export function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSend = async () => {
    if (!input.trim()) return;
    
    // Add user message
    const userMessage = { role: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);
    
    try {
      // Call RAG assistant API
      const response = await fetch('/api/v1/ai-assistant/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input })
      });
      
      const data = await response.json();
      
      // Add AI response
      const aiMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        confidence: data.confidence
      };
      setMessages([...messages, userMessage, aiMessage]);
    } catch (error) {
      console.error('AI assistant error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="ai-assistant">
      <div className="ai-header">
        <h3>🤖 AI Research Assistant</h3>
        <p>Ask me anything about your saved papers</p>
      </div>
      
      <div className="ai-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message message-${msg.role}`}>
            <div className="message-content">{msg.content}</div>
            {msg.sources && (
              <div className="message-sources">
                <strong>Sources:</strong>
                {msg.sources.map((source, j) => (
                  <span key={j} className="source-tag">{source}</span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message-loading">Thinking...</div>}
      </div>
      
      <div className="ai-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about your research..."
        />
        <button onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
      
      <div className="ai-suggestions">
        <p>Try asking:</p>
        <button onClick={() => setInput("What papers do I have about transformers?")}>
          Papers about transformers
        </button>
        <button onClick={() => setInput("Summarize my notes on deep learning")}>
          Summarize my notes
        </button>
        <button onClick={() => setInput("Help me write a literature review")}>
          Help with lit review
        </button>
      </div>
    </div>
  );
}
```

---

### **Task 2.8: AI Can Edit Literature Reviews** (4 hours)

```python
# backend/app/services/rag_assistant_service.py

async def edit_literature_review(
    self,
    review_id: int,
    instruction: str,
    db: Session
) -> Dict:
    """
    AI can edit user's literature review
    
    Examples:
    - "Add a section about transformer models"
    - "Improve the introduction"
    - "Add citations from my saved papers"
    - "Make it more concise"
    """
    # Get review
    review = db.query(UserLiteratureReview).filter(
        UserLiteratureReview.id == review_id
    ).first()
    
    if not review:
        raise ValueError("Review not found")
    
    # Get user's saved papers for context
    user_papers = await self._get_user_papers(review.user_id, db)
    
    # Create edit prompt
    prompt = f"""
    You are helping edit a literature review.
    
    Current review:
    {review.content}
    
    User's instruction: {instruction}
    
    Available papers to cite:
    {self._format_papers_for_citation(user_papers)}
    
    Please edit the review according to the instruction.
    Maintain academic tone and proper citations.
    """
    
    # Call LLM
    response = await self.llm_client.chat.completions.create(
        model="gpt-5-mini",  # Better quality for editing
        messages=[
            {"role": "system", "content": "You are an academic writing assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    edited_content = response.choices[0].message.content
    
    # Save as new version
    review.content = edited_content
    review.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "review_id": review_id,
        "edited_content": edited_content,
        "instruction": instruction
    }
```

---

### **Task 2.9: Testing & Optimization** (2 hours)

**Test Cases:**

```python
# backend/tests/test_rag_assistant.py
import pytest

@pytest.mark.asyncio
async def test_rag_answer_question():
    """Test RAG can answer questions about user's papers"""
    service = RAGAssistantService()
    
    result = await service.answer_question(
        user_id="test-user",
        question="What papers do I have about deep learning?",
        db=test_db
    )
    
    assert result["answer"]
    assert len(result["sources"]) > 0
    assert result["confidence"] > 0.5

@pytest.mark.asyncio
async def test_rag_edit_review():
    """Test RAG can edit literature reviews"""
    service = RAGAssistantService()
    
    result = await service.edit_literature_review(
        review_id=1,
        instruction="Add a section about transformers",
        db=test_db
    )
    
    assert "transformer" in result["edited_content"].lower()
```

---

## 📊 **Phase 2 Summary**

### **What You Get:**
1. ✅ Beautiful, optimized workspace UI
2. ✅ Drag-and-drop organization
3. ✅ Collections and folders
4. ✅ Keyboard shortcuts
5. ✅ **Intelligent AI assistant with RAG**
6. ✅ AI can read your papers
7. ✅ AI can access your notes
8. ✅ AI can edit literature reviews
9. ✅ Context-aware suggestions

### **Timeline:**
- **Week 3, Days 1-3:** Workspace UI (20 hours)
- **Week 3, Days 4-5 + Week 4, Days 1-2:** RAG AI (20 hours)
- **Total: 40 hours**

### **Cost:**
- GPT-5 nano for RAG: $0.05/1M input, $0.40/1M output
- Average query: ~2,000 tokens input, ~500 tokens output
- Cost per query: ~$0.0003 (less than 1 cent!)
- **Very affordable** ✅

### **Dependencies:**
```bash
# Backend
pip install sentence-transformers scikit-learn openai

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
- [ ] Mobile-responsive design
- [ ] No performance degradation with 1000+ papers

---

**This transforms your app from a search tool into an intelligent research assistant!** 🚀
