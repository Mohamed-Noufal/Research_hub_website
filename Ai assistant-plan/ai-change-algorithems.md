# AI Assistant - Production Architecture: Global Smart Index

## 1. VISION: THE GLOBAL SMART INDEX (Production Grade)
We are moving from a "Project-Based Manual Index" to a **"Global Smart Index"**.
Instead of requiring users to manually "Convert to Knowledge Base" (with a 7-paper limit), the system will **Auto-Index everything** in the background.

**Core Philosophy:** "Embed Once, Use Everywhere."

---

## 2. THE ARCHITECTURE

### A. Ingestion Pipeline (Auto-Indexing)
**Trigger:** Immediate upon file upload or saved in liberary.
**Process:**
1.  **File Upload:** PDF saved to disk.
2.  **Duplicate Check:** Check `paper_hash` in `paper_chunks`. If exists, skip (Zero cost).
3.  **Parsing (Docling):**
    *   **Text:** Extracted.
    *   **Structure:** `section_type` identified (Methodology, Abstract, Results, etc.).
    *   **Rich Content:**
        *   **Tables:** Converted to Markdown/HTML (Preserve structure).
        *   **Equations:** Extracted as LaTeX (Preserve math).
4.  **Chunking (Hierarchical):**
    *   **Parent:** 1024 tokens (For context).
    *   **Child:** 256 tokens (For precise vector match).
5.  **Embedding:** Nomic v1.5 (768 dimensions).
6.  **Storage:** Global `paper_chunks` table.

### B. "Smart Synthesis" Retrieval Strategy
To answer "Summarize these 7 papers", we don't use random vector search. We use **Structured Section Filtering**.

**The Mechanism (Tool Calling):**
The LLM does not write raw SQL. It calls a specific Python tool.

1.  **Tool Definition:**
    ```python
    @tool
    def get_paper_sections(section_type: str, paper_ids: List[int]):
        """
        Retrieves full text of a specific section (Methodology, Results, etc.) 
        from a list of papers. Use this for summaries and comparisons.
        """
        # Python code executes the SQL safely:
        # SELECT text FROM paper_chunks WHERE ...
    ```

2.  **Execution Flow:**
    *   **User:** "Compare the methodology..."
    *   **LLM Decides:** Call `get_paper_sections(section_type='methodology', paper_ids=[1,2,3])`
    *   **System (Python):** Executes SQL with JOIN to ensure data integrity:
        ```sql
        SELECT p.title, c.text 
        FROM paper_chunks c
        JOIN papers p ON c.paper_id = p.id 
        WHERE c.paper_id IN (...) AND c.section_type = 'methodology'
        ```
    *   **Formatting:** Returns clearly labeled text:
        > **[Paper: Transformer Networks]**
        > The methodology involves...
        >
        > **[Paper: LSTM]**
        > We utilized...

    *   **LLM:** specific "The papers differ in their approach..."

*   **Result:** The LLM receives the *exact* methodology sections, ensuring 100% coverage and high-quality synthesis without noise.

### C. "Deep Search" Retrieval Strategy
To answer specific questions ("What is the accuracy on ImageNet?"), we use **Advanced RAG**:

1.  **Hybrid Search:** BM25 (Keywords) + Vector (Semantic).
2.  **Reranking:** Top 25 results re-scored by `BAAI/bge-reranker`.
3.  **Result:** Top 5-7 highly relevant chunks.

---

## 3. DATABASE SCHEMA (Global Table)

**Table:** `paper_chunks` (Single Source of Truth)
```sql
CREATE TABLE paper_chunks (
    id UUID PRIMARY KEY,
    paper_id INTEGER REFERENCES papers(id),  -- Global Paper ID
    
    -- Hierarchy
    parent_id UUID,          -- Link child to parent
    level INTEGER,           -- 0=Child, 1=Parent
    
    -- Content & Tags
    section_type VARCHAR(50), -- 'abstract', 'methodology', 'results', 'conclusion'
    text TEXT,               -- Content (Markdown for tables)
    
    -- Search
    embedding vector(768),   -- Nomic Dimensions
    metadata JSONB           -- { "keywords": ["..."], "has_table": true }
);
```

---

## 4. UI SPECIFICATION (AI Assistant)

### Scope Selector (The New Control)
Instead of "Add to KB", the user controls the **Context Scope** of the chat.

**Location:** Top of AI Assistant.
**Component:** Dropdown / Multi-select.

**Options:**
1.  **"Active Project" (Default):**
    *   Context: All papers in the current project list.
2.  **"Selected Papers":**
    *   Action: User checks boxes next to papers in the library.
    *   Context: Only related to those specific  papers IDs.
3.  **"Entire Library":**
    *   Context: ALL papers owned by the user.

### Status Indicator
*   **"Indexing..."** spinner next to papers that are currently processing.
*   **"Ready"** checkmark when embeddings are complete.

---

## 5. FUTURE PROOFING

**The "AI Writer" Foundation:**
Because we store Tables as Markdown and Equations as LaTeX, a future "Drafting Agent" can:
1.  **Cite Figures:** "See Figure 3 in Paper A..."
2.  **Reconstruct Tables:** Generate a comparison table by pulling authoritative rows.
3.  **Verify Math:** Solve/Check equations found in the text.

---

## 6. MIGRATION PLAN (Immediate Steps)

1.  **Database:** Run `021_advanced_rag.sql` (Done).
2.  **Backend:**
    *   [ ] Update `pdf_tools.py` to Auto-Index on upload.
    *   [ ] Update `rag_engine.py` to support `section_type` tagging.
    *   [ ] Create "Smart Synthesis" query method in `agent_service`.
3.  **Frontend:**
    *   [ ] Implement **Scope Selector** in `AIAssistant.tsx`.
    *   [ ] Remove old "KB Modal" code.
    *   [ ] Add "Indexing" status icons to Paper List.

**Status:** Plan Approved. Coding in Progress.
