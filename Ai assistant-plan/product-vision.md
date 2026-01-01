# AI Research Hub - Product Vision

## The Ultimate Research Platform

**Mission**: Create the all-in-one platform where researchers can do EVERYTHING - from discovery to publication.

---

## Core App Features

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AI RESEARCH HUB                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   │   SEARCH     │  │   LIBRARY    │  │   REVIEW     │  │   WRITE      │   │
│   │              │  │              │  │              │  │              │   │
│   │ • Semantic   │  │ • Projects   │  │ • Compare    │  │ • Paraphrase │   │
│   │ • Keywords   │  │ • Folders    │  │ • Synthesize │  │ • Summarize  │   │
│   │ • Citations  │  │ • Tags       │  │ • Gaps       │  │ • Citations  │   │
│   │ • DOI/arXiv  │  │ • Notes      │  │ • Themes     │  │ • References │   │
│   └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│                    ┌────────────────────────────────────┐                    │
│                    │         AI ASSISTANT               │                    │
│                    │   Full Access to All Features      │                    │
│                    │   Through Tools & Endpoints        │                    │
│                    └────────────────────────────────────┘                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## AI Assistant Vision

### Core Principle
> **The AI Assistant is not separate from the app - it IS the app's brain.**
> 
> It can SEE, CREATE, UPDATE, and DELETE anything a user can do through the UI.

### Capability Matrix

| Category | CREATE | READ | UPDATE | DELETE |
|----------|--------|------|--------|--------|
| **Papers** | Add from search/DOI | View metadata | Edit notes | Remove from library |
| **Projects** | Create new | List all | Rename, configure | Archive |
| **Comparisons** | Generate auto | View tables | Edit cells | Clear |
| **Findings** | Extract from papers | Summarize | Refine | Remove |
| **Synthesis** | Write drafts | Show current | Revise | Reset |
| **Citations** | Generate | Format | Convert style | - |
| **Notes** | Create | Read | Edit | Delete |
| **Tags** | Add | List | Rename | Remove |

---

## AI Assistant Tools (Complete List)

### 1. SEARCH Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_papers` | Semantic + keyword search | query, filters, top_k |
| `search_by_doi` | Find paper by DOI | doi |
| `search_by_arxiv` | Find paper by arXiv ID | arxiv_id |
| `search_citations` | Find papers citing a paper | paper_id |
| `search_references` | Find papers a paper cites | paper_id |
| `find_similar_papers` | Find semantically similar | paper_id, top_k |

### 2. LIBRARY Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `create_project` | Create new project | name, description |
| `list_projects` | List user's projects | user_id |
| `add_paper_to_project` | Add paper to project | paper_id, project_id |
| `remove_paper_from_project` | Remove paper | paper_id, project_id |
| `create_folder` | Create folder in project | project_id, name |
| `move_paper_to_folder` | Organize papers | paper_id, folder_id |
| `add_tag` | Tag a paper | paper_id, tag |
| `add_note` | Add note to paper | paper_id, note_text |
| `update_note` | Edit note | note_id, new_text |

### 3. REVIEW Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `compare_papers` | Compare N papers | paper_ids, aspects |
| `extract_methodology` | Get methodology details | paper_id |
| `extract_findings` | Get key findings | paper_id |
| `identify_themes` | Find themes across papers | project_id |
| `find_research_gaps` | Identify gaps | project_id |
| `create_synthesis_table` | Build comparison table | paper_ids, columns |
| `update_synthesis_cell` | Edit table cell | table_id, cell_id, value |

### 4. WRITE Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `summarize_paper` | Generate summary | paper_id, length |
| `summarize_section` | Summarize specific section | paper_id, section |
| `paraphrase_text` | Rewrite text | text, style |
| `generate_abstract` | Write abstract from papers | paper_ids |
| `write_literature_review` | Draft lit review | project_id, structure |
| `generate_citation` | Create citation | paper_id, style |
| `format_bibliography` | Format all citations | paper_ids, style |

### 5. UTILITY Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_paper_pdf` | Download/view PDF | paper_id |
| `extract_tables` | Get tables from PDF | paper_id |
| `extract_figures` | Get figures from PDF | paper_id |
| `export_to_word` | Export to DOCX | content, format |
| `export_to_bibtex` | Export citations | paper_ids |

---

## User Journeys

### Journey 1: Literature Review

```
User: "I need to write a literature review on transformer models in NLP"

AI Actions:
1. search_papers("transformer models NLP") → Find 50 papers
2. create_project("Transformer NLP Review") → New project
3. add_paper_to_project() → Add top 20 relevant papers
4. identify_themes(project_id) → Find 5 key themes
5. find_research_gaps(project_id) → Identify 3 gaps
6. write_literature_review(project_id) → Draft review
7. format_bibliography(paper_ids, "APA") → Add citations

Result: Complete literature review draft with citations
```

### Journey 2: Paper Comparison

```
User: "Compare these 3 papers on their methodology"

AI Actions:
1. extract_methodology(paper_1) → Get methods
2. extract_methodology(paper_2) → Get methods
3. extract_methodology(paper_3) → Get methods
4. compare_papers([1,2,3], "methodology") → Generate comparison
5. create_synthesis_table(paper_ids, ["Method", "Dataset", "Metrics"])

Result: Side-by-side methodology comparison table
```

### Journey 3: Quick Write

```
User: "Paraphrase this paragraph and cite the source"

AI Actions:
1. paraphrase_text(text, style="academic") → Rewrite
2. generate_citation(paper_id, "APA") → Add citation

Result: Paraphrased text with proper citation
```

---

## Current vs. Future Tool Coverage

### Tools Already Implemented ✅

| Tool | File | Status |
|------|------|--------|
| `semantic_search` | rag_tools.py | ✅ Working |
| `get_paper_sections` | rag_tools.py | ✅ Working |
| `compare_papers` | rag_tools.py | ✅ Working |
| `extract_methodology` | rag_tools.py | ✅ Working |
| `find_research_gaps` | rag_tools.py | ✅ Working |
| `get_project_by_name` | database_tools.py | ✅ Working |
| `get_project_papers` | database_tools.py | ✅ Working |
| `link_paper_to_project` | database_tools.py | ✅ Working |
| `update_comparison` | database_tools.py | ✅ Working |
| `update_findings` | database_tools.py | ✅ Working |
| `update_methodology` | database_tools.py | ✅ Working |
| `update_synthesis` | database_tools.py | ✅ Working |

### Tools To Build 🔧

| Tool | Priority | Complexity | Notes |
|------|----------|------------|-------|
| `search_by_doi` | HIGH | Low | API call to CrossRef |
| `search_citations` | HIGH | Medium | Semantic Scholar API |
| `find_similar_papers` | HIGH | Low | Use existing embeddings |
| `create_project` | HIGH | Low | DB insert |
| `add_note` | MEDIUM | Low | DB insert |
| `summarize_paper` | HIGH | Medium | LLM call |
| `paraphrase_text` | HIGH | Low | LLM call |
| `generate_citation` | HIGH | Low | Template + data |
| `write_literature_review` | HIGH | High | Multi-step LLM |
| `export_to_bibtex` | MEDIUM | Low | Template format |
| `extract_tables` | HIGH | Medium | Docling already does this |
| `extract_figures` | MEDIUM | Medium | Docling extraction |

---

## Target Users

| User Type | Needs | Key Features |
|-----------|-------|--------------|
| **PhD Students** | Literature reviews, gap analysis | Synthesis, comparison |
| **Professors** | Quick searches, paper management | Search, organize |
| **Industry Researchers** | Fast insights, summaries | Summarize, extract |
| **Medical Researchers** | Systematic reviews | Structured extraction |
| **Writers** | Paraphrasing, citations | Write tools |

---

## Implementation Priorities

### Phase 1: Core AI Tools (Week 1-2)
- [ ] `search_by_doi` - Quick paper add
- [ ] `find_similar_papers` - Discovery
- [ ] `summarize_paper` - Quick insights
- [ ] `paraphrase_text` - Writing help
- [ ] `generate_citation` - Citation support

### Phase 2: Project Tools (Week 2-3)
- [ ] `create_project` - Full project CRUD
- [ ] `add_note` / `update_note` - Note taking
- [ ] `add_tag` - Organization
- [ ] `move_paper_to_folder` - Structure

### Phase 3: Advanced Analysis (Week 3-4)
- [ ] `search_citations` - Citation network
- [ ] `search_references` - Reference network
- [ ] `identify_themes` - Theme extraction
- [ ] `write_literature_review` - Auto-drafting

### Phase 4: Export & Polish (Week 4-5)
- [ ] `export_to_word` - Document export
- [ ] `export_to_bibtex` - Citation export
- [ ] `format_bibliography` - Style formatting

---

## Success Metrics

| Metric | Target |
|--------|--------|
| User can complete lit review | < 2 hours (vs. 2 days manual) |
| Paper comparison | < 30 seconds |
| Citation generation | < 5 seconds |
| Tool coverage | 90% of research tasks |
| User satisfaction | 4.5+ stars |

---

## Visual: The AI Research Hub Experience

```
┌─────────────────────────────────────────────────────────────────┐
│  🔬 AI Research Hub                              [User] [⚙️]    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌────────────────────────────────────┐  │
│  │  📚 My Library   │  │  Paper Viewer / Workspace          │  │
│  │                  │  │                                    │  │
│  │  ▸ Project A     │  │  [Currently: Analyzing 3 papers]   │  │
│  │  ▸ Project B     │  │                                    │  │
│  │  ▸ Favorites     │  │  ┌────────────────────────────┐   │  │
│  │                  │  │  │  Comparison Table          │   │  │
│  │  📄 Recent       │  │  │  ├─ Paper 1: Method A      │   │  │
│  │  • Paper 1       │  │  │  ├─ Paper 2: Method B      │   │  │
│  │  • Paper 2       │  │  │  └─ Paper 3: Method C      │   │  │
│  │  • Paper 3       │  │  └────────────────────────────┘   │  │
│  │                  │  │                                    │  │
│  └──────────────────┘  └────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  💬 AI Assistant                                        │   │
│  │                                                         │   │
│  │  You: "Compare these papers on methodology"             │   │
│  │                                                         │   │
│  │  AI: Analyzing papers...                                │   │
│  │      ✓ Extracted methodology from Paper 1               │   │
│  │      ✓ Extracted methodology from Paper 2               │   │
│  │      ✓ Extracted methodology from Paper 3               │   │
│  │      ✓ Generated comparison table                       │   │
│  │                                                         │   │
│  │  [The comparison table above has been updated]          │   │
│  │                                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │ Ask anything...                          [Send] │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Document Current Tool Gaps** - Audit what's missing
2. **Prioritize by User Value** - What saves most time?
3. **Build Missing Tools** - Start with high-impact, low-complexity
4. **Test User Journeys** - Validate with real research tasks
5. **Iterate on Prompts** - Improve AI decision-making
