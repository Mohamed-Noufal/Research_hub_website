# AI Assistant: Complete Integration Flow with Existing System

## 🎯 Production-Ready Workflow

### User Flow Example

```
USER: "Generate summary and methodology sections for my AI in Healthcare project"

AI ASSISTANT:
  ✓ Identifies project: "AI in Healthcare" (project_id=5)
  ✓ Fetches papers in project (4 papers found)
  ✓ Checks if papers are processed (embeddings exist)
  ✓ Generates both sections
  ✓ Updates database
  ✓ UI auto-refreshes
```

---

## 🔗 Integration with Existing System

### Current System Architecture

```
YOUR EXISTING SYSTEM:
├── Library (Saved Papers)
│   ├── Folders (user-created)
│   └── Papers (user_saved_papers table)
│
└── Literature Review Projects
    ├── Project metadata (user_literature_reviews table)
    ├── Selected papers (project_papers table)
    └── Sections (comparison, methodology, findings, etc.)
```

### AI Assistant Integration Points

```python
# backend/app/agents/database_agent.py

class DatabaseAgent(BaseAgent):
    """
    Integrates with ALL existing endpoints and tables
    """
    
    def _initialize_tools(self):
        return {
            # Project Management
            'get_project_by_name': self._get_project_by_name,
            'get_project_papers': self._get_project_papers,
            'get_user_library': self._get_user_library,
            
            # Paper Processing
            'check_paper_processed': self._check_paper_processed,
            'get_paper_embeddings': self._get_paper_embeddings,
            
            # Literature Review Updates
            'update_comparison_tab': self._update_comparison_tab,
            'update_methodology_tab': self._update_methodology_tab,
            'update_findings_tab': self._update_findings_tab,
            'update_synthesis_tab': self._update_synthesis_tab,
        }
    
    async def _get_project_by_name(self, context: AgentContext):
        """
        Find project by name (fuzzy matching)
        """
        project_name = context.metadata['project_name']
        user_id = context.user_id
        
        # Fuzzy search using PostgreSQL similarity
        result = await self.db.execute(
            text("""
                SELECT id, title, description
                FROM user_literature_reviews
                WHERE user_id = :user_id
                  AND LOWER(title) LIKE LOWER(:pattern)
                ORDER BY similarity(title, :project_name) DESC
                LIMIT 1
            """),
            {
                'user_id': user_id,
                'pattern': f'%{project_name}%',
                'project_name': project_name
            }
        )
        
        project = result.fetchone()
        
        if not project:
            raise ValueError(f"Project '{project_name}' not found")
        
        return {
            'project_id': project.id,
            'title': project.title,
            'description': project.description
        }
    
    async def _get_project_papers(self, context: AgentContext):
        """
        Get all papers in a literature review project
        Uses EXISTING project_papers table
        """
        project_id = context.metadata['project_id']
        
        result = await self.db.execute(
            text("""
                SELECT 
                    p.id,
                    p.title,
                    p.authors,
                    p.abstract,
                    p.publication_date,
                    p.doi,
                    pp.added_at
                FROM papers p
                JOIN project_papers pp ON pp.paper_id = p.id
                WHERE pp.project_id = :project_id
                ORDER BY pp.added_at DESC
            """),
            {'project_id': project_id}
        )
        
        papers = result.fetchall()
        
        return {
            'papers': [dict(p) for p in papers],
            'count': len(papers)
        }
    
    async def _check_paper_processed(self, context: AgentContext):
        """
        Check if paper has embeddings (already processed)
        """
        paper_id = context.metadata['paper_id']
        
        result = await self.db.execute(
            text("""
                SELECT COUNT(*) as chunk_count
                FROM paper_chunks
                WHERE paper_id = :paper_id
            """),
            {'paper_id': paper_id}
        )
        
        count = result.fetchone().chunk_count
        
        return {
            'is_processed': count > 0,
            'chunk_count': count
        }
```

---

## 📋 Complete Workflow: "Generate Summary and Methodology"

### Step-by-Step Execution

```python
# backend/app/agents/orchestrator.py

class OrchestratorAgent(BaseAgent):
    
    async def execute(self, user_message: str, context: AgentContext):
        """
        USER: "Generate summary and methodology for AI in Healthcare project"
        """
        
        # ===== STEP 1: Parse Intent =====
        intent = await self._parse_intent(user_message)
        # Result: {
        #   "action": "generate_sections",
        #   "sections": ["summary", "methodology"],
        #   "project_name": "AI in Healthcare"
        # }
        
        # ===== STEP 2: Get Project =====
        project = await self.database_agent.execute(
            'get_project_by_name',
            context.with_metadata({'project_name': intent['project_name']})
        )
        # Result: {project_id: 5, title: "AI in Healthcare Review"}
        
        context.metadata['project_id'] = project['project_id']
        
        # ===== STEP 3: Get Papers in Project =====
        papers_data = await self.database_agent.execute(
            'get_project_papers',
            context
        )
        # Result: {papers: [paper1, paper2, paper3, paper4], count: 4}
        
        papers = papers_data['papers']
        
        # ===== STEP 4: Check Which Papers Need Processing =====
        unprocessed_papers = []
        for paper in papers:
            check = await self.database_agent.execute(
                'check_paper_processed',
                context.with_metadata({'paper_id': paper['id']})
            )
            
            if not check['is_processed']:
                unprocessed_papers.append(paper)
        
        # ===== STEP 5: Process Unprocessed Papers =====
        if unprocessed_papers:
            await self._emit_progress(
                f"Processing {len(unprocessed_papers)} papers..."
            )
            
            for paper in unprocessed_papers:
                # Parse PDF (if we have file)
                await self.paper_agent.execute('parse_pdf', context)
                
                # Generate embeddings
                await self.paper_agent.execute('generate_embeddings', context)
                
                # Store chunks
                await self.database_agent.execute('store_chunks', context)
        
        # ===== STEP 6: Generate Each Section =====
        results = []
        
        for section_type in intent['sections']:
            await self._emit_progress(f"Generating {section_type} section...")
            
            # Get section schema
            schema = await self.writing_agent.execute(
                'get_section_schema',
                context.with_metadata({'section_type': section_type})
            )
            
            # Query relevant content via RAG
            rag_results = await self.analysis_agent.execute(
                'query_rag',
                context.with_metadata({
                    'query': f"{section_type} content",
                    'section_filter': [section_type],
                    'paper_ids': [p['id'] for p in papers]
                })
            )
            
            # Generate content
            content = await self.writing_agent.execute(
                'generate_content',
                context.with_metadata({
                    'schema': schema,
                    'context': rag_results['chunks'],
                    'section_type': section_type
                })
            )
            
            # Update database using EXISTING endpoints
            await self._update_section_in_db(
                section_type=section_type,
                content=content,
                context=context
            )
            
            results.append({
                'section': section_type,
                'status': 'completed',
                'word_count': len(content.split())
            })
        
        # ===== STEP 7: Emit WebSocket Event =====
        await self._emit_event('sections_updated', {
            'project_id': project['project_id'],
            'sections': intent['sections']
        })
        
        # ===== STEP 8: Return Summary =====
        return {
            'message': f"✓ Generated {len(results)} sections for '{project['title']}'",
            'results': results
        }
    
    async def _update_section_in_db(self, section_type: str, content: str, context: AgentContext):
        """
        Update specific tab based on section type
        Uses EXISTING database schema
        """
        
        if section_type == 'methodology':
            # Update methodology in comparison_attributes table
            await self.database_agent.execute(
                'update_methodology_tab',
                context.with_metadata({'content': content})
            )
        
        elif section_type == 'summary':
            # Update project description or create synthesis
            await self.database_agent.execute(
                'update_synthesis_tab',
                context.with_metadata({'content': content})
            )
        
        elif section_type == 'findings':
            # Update findings table
            await self.database_agent.execute(
                'update_findings_tab',
                context.with_metadata({'content': content})
            )
```

---

## 🔧 Tools for Updating Existing Tabs

### Tool: Update Comparison Tab

```python
async def _update_comparison_tab(self, context: AgentContext):
    """
    Updates comparison_configs and comparison_attributes tables
    """
    project_id = context.metadata['project_id']
    user_id = context.user_id
    comparison_data = context.metadata['comparison_data']
    
    async with self.db.begin():
        # Update comparison_configs
        await self.db.execute(
            text("""
                INSERT INTO comparison_configs (
                    user_id, project_id, 
                    selected_paper_ids,
                    insights_similarities,
                    insights_differences
                ) VALUES (
                    :user_id, :project_id,
                    :paper_ids,
                    :similarities,
                    :differences
                )
                ON CONFLICT (user_id, project_id) 
                DO UPDATE SET
                    insights_similarities = EXCLUDED.insights_similarities,
                    insights_differences = EXCLUDED.insights_differences,
                    updated_at = NOW()
            """),
            {
                'user_id': user_id,
                'project_id': project_id,
                'paper_ids': comparison_data['selected_paper_ids'],
                'similarities': comparison_data['similarities'],
                'differences': comparison_data['differences']
            }
        )
        
        # Update comparison_attributes for each paper
        for paper_id, attributes in comparison_data['attributes'].items():
            for attr_name, attr_value in attributes.items():
                await self.db.execute(
                    text("""
                        INSERT INTO comparison_attributes (
                            user_id, project_id, paper_id,
                            attribute_name, attribute_value
                        ) VALUES (
                            :user_id, :project_id, :paper_id,
                            :attr_name, :attr_value
                        )
                        ON CONFLICT (user_id, project_id, paper_id, attribute_name)
                        DO UPDATE SET
                            attribute_value = EXCLUDED.attribute_value,
                            updated_at = NOW()
                    """),
                    {
                        'user_id': user_id,
                        'project_id': project_id,
                        'paper_id': paper_id,
                        'attr_name': attr_name,
                        'attr_value': attr_value
                    }
                )
        
        await self.db.commit()
    
    return {'status': 'success', 'tab': 'comparison'}
```

### Tool: Update Methodology Tab

```python
async def _update_methodology_tab(self, context: AgentContext):
    """
    Updates methodology data in comparison_attributes
    """
    project_id = context.metadata['project_id']
    user_id = context.user_id
    methodology_data = context.metadata['methodology_data']
    
    # Methodology is stored as attributes in comparison_attributes
    methodology_fields = [
        'methodologySummary',
        'methodologyType',
        'dataCollection',
        'analysisMethod'
    ]
    
    async with self.db.begin():
        for paper_id, methods in methodology_data.items():
            for field in methodology_fields:
                if field in methods:
                    await self.db.execute(
                        text("""
                            INSERT INTO comparison_attributes (
                                user_id, project_id, paper_id,
                                attribute_name, attribute_value
                            ) VALUES (
                                :user_id, :project_id, :paper_id,
                                :attr_name, :attr_value
                            )
                            ON CONFLICT (user_id, project_id, paper_id, attribute_name)
                            DO UPDATE SET
                                attribute_value = EXCLUDED.attribute_value,
                                updated_at = NOW()
                        """),
                        {
                            'user_id': user_id,
                            'project_id': project_id,
                            'paper_id': paper_id,
                            'attr_name': field,
                            'attr_value': methods[field]
                        }
                    )
        
        await self.db.commit()
    
    return {'status': 'success', 'tab': 'methodology'}
```

### Tool: Update Findings Tab

```python
async def _update_findings_tab(self, context: AgentContext):
    """
    Updates findings and research_gaps tables
    """
    project_id = context.metadata['project_id']
    user_id = context.user_id
    findings_data = context.metadata['findings_data']
    
    async with self.db.begin():
        # Update findings for each paper
        for paper_id, finding in findings_data['paper_findings'].items():
            await self.db.execute(
                text("""
                    INSERT INTO findings (
                        user_id, project_id, paper_id,
                        key_finding, limitations
                    ) VALUES (
                        :user_id, :project_id, :paper_id,
                        :key_finding, :limitations
                    )
                    ON CONFLICT (user_id, project_id, paper_id)
                    DO UPDATE SET
                        key_finding = EXCLUDED.key_finding,
                        limitations = EXCLUDED.limitations,
                        updated_at = NOW()
                """),
                {
                    'user_id': user_id,
                    'project_id': project_id,
                    'paper_id': paper_id,
                    'key_finding': finding['key_finding'],
                    'limitations': finding['limitations']
                }
            )
        
        # Update research gaps
        for gap in findings_data['research_gaps']:
            await self.db.execute(
                text("""
                    INSERT INTO research_gaps (
                        id, user_id, project_id,
                        description, priority, notes
                    ) VALUES (
                        gen_random_uuid(), :user_id, :project_id,
                        :description, :priority, :notes
                    )
                """),
                {
                    'user_id': user_id,
                    'project_id': project_id,
                    'description': gap['description'],
                    'priority': gap['priority'],
                    'notes': gap['notes']
                }
            )
        
        await self.db.commit()
    
    return {'status': 'success', 'tab': 'findings'}
```

---

## 🎨 Frontend Auto-Refresh

### WebSocket Integration

```tsx
// frontend/src/hooks/useAgentUpdates.ts

export function useAgentUpdates(projectId: number) {
  const queryClient = useQueryClient();
  const [ws, setWs] = useState<WebSocket | null>(null);
  
  useEffect(() => {
    // Connect to WebSocket
    const socket = new WebSocket(`ws://localhost:8000/api/v1/agent/ws/${projectId}`);
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.event === 'sections_updated') {
        // Invalidate queries to refetch data
        queryClient.invalidateQueries(['project', projectId]);
        queryClient.invalidateQueries(['comparison', projectId]);
        queryClient.invalidateQueries(['findings', projectId]);
        
        // Show notification
        toast.success(`${data.sections.join(', ')} sections updated!`);
      }
      
      if (data.event === 'progress') {
        // Show progress indicator
        setProgress(data.progress);
      }
    };
    
    setWs(socket);
    
    return () => socket.close();
  }, [projectId]);
  
  return { ws };
}
```

### Usage in Literature Review Component

```tsx
// frontend/src/components/workspace/LiteratureReview.tsx

function LiteratureReview({ project }: { project: Project }) {
  // Auto-refresh when AI updates data
  useAgentUpdates(project.id);
  
  // Existing hooks still work
  const { data: papers } = useProjectPapers(project.id);
  const { data: comparison } = useComparisonConfig(project.id);
  const { data: findings } = useFindings(project.id);
  
  // Everything auto-refreshes when AI updates!
  return (
    <div>
      <ComparisonView papers={papers} projectId={project.id} />
      <FindingsView findings={findings} />
      {/* ... other tabs */}
    </div>
  );
}
```

---

## 🚀 Production Best Practices

### 1. **Context-Aware AI**

```python
# AI knows about user's entire workspace
context = AgentContext(
    user_id=user_id,
    project_id=project_id,
    metadata={
        'available_projects': [...],  # All user's projects
        'library_folders': [...],      # User's folder structure
        'recent_papers': [...]         # Recently added papers
    }
)
```

### 2. **Smart Paper Selection**

```python
# AI can intelligently select papers
USER: "Compare the 3 most recent papers in my project"

# AI automatically:
# 1. Gets project papers
# 2. Sorts by added_at DESC
# 3. Takes top 3
# 4. Runs comparison
```

### 3. **Incremental Processing**

```python
# Only process what's needed
if paper.has_embeddings:
    # Skip processing, use existing embeddings
    pass
else:
    # Process only this paper
    await process_paper(paper)
```

### 4. **Transaction Safety**

```python
# All updates use transactions
async with db.begin():
    # Multiple updates
    await update_comparison()
    await update_methodology()
    await update_findings()
    await db.commit()  # All or nothing
```

---

## 📊 Recommended Architecture

```
USER MESSAGE: "Generate summary and methodology for AI Healthcare project"
     ↓
ORCHESTRATOR
     ↓
[1] DATABASE AGENT: Get project by name → project_id=5
     ↓
[2] DATABASE AGENT: Get papers in project → 4 papers
     ↓
[3] PAPER AGENT: Check if processed → 2 need processing
     ↓
[4] PAPER AGENT: Process unprocessed papers
     ↓
[5] ANALYSIS AGENT: RAG query for summary content
     ↓
[6] WRITING AGENT: Generate summary section
     ↓
[7] DATABASE AGENT: Update synthesis_tab
     ↓
[8] ANALYSIS AGENT: RAG query for methodology
     ↓
[9] WRITING AGENT: Generate methodology section
     ↓
[10] DATABASE AGENT: Update methodology_tab
     ↓
[11] ORCHESTRATOR: Emit WebSocket event
     ↓
FRONTEND: Auto-refresh all tabs
```

---

## ✅ Summary: Best for Production

1. **AI accesses existing tables** - No schema changes needed
2. **Tools update specific tabs** - Clean separation of concerns
3. **WebSocket for real-time updates** - UI stays in sync
4. **Transaction safety** - No data corruption
5. **Incremental processing** - Only process what's needed
6. **Context-aware** - AI knows user's entire workspace

**Ready to implement?** This architecture integrates seamlessly with your existing system!
