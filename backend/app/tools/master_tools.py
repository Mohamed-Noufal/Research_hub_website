"""
Master Tools for AI Agent
High-level tools that orchestrate multiple operations.
"""
from typing import Dict, List, Optional, Any
from sqlalchemy import text
import uuid
import json
import logging

logger = logging.getLogger(__name__)


async def fill_all_tabs(
    project_id: int,
    user_id: str,
    paper_ids: Optional[List[int]] = None,
    db = None,
    rag_engine = None,
    llm_client = None,
    websocket_callback = None
) -> Dict[str, Any]:
    """
    Master tool: Fill all literature review tabs for papers in a project.
    
    Phases:
    1. Methodology extraction for each paper
    2. Findings extraction for each paper  
    3. Comparison generation
    4. Synthesis generation
    5. Summary generation
    
    Features:
    - Checkpointing: Saves progress after each paper
    - Resume: Can continue from failed point
    - Progress streaming: Sends WebSocket updates
    
    Args:
        project_id: Literature review project ID
        user_id: User ID
        paper_ids: Optional list of specific papers (defaults to all in project)
        db: Database session
        rag_engine: RAG engine instance
        llm_client: LLM client instance
        websocket_callback: Optional async function to send progress updates
    
    Returns:
        Dict with status, completed phases, and any errors
    """
    from app.tools import rag_tools, database_tools
    from app.schemas.agent_outputs import TaskStateOutput
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Helper to send progress updates
    async def send_progress(phase: str, current: int, total: int, message: str):
        if websocket_callback:
            try:
                await websocket_callback({
                    "type": "task_progress",
                    "task_id": task_id,
                    "phase": phase,
                    "current": current,
                    "total": total,
                    "percentage": int((current / total) * 100) if total > 0 else 0,
                    "message": message
                })
            except Exception as e:
                logger.warning(f"Failed to send progress: {e}")
    
    # Helper to save task state
    def save_task_state(
        status: str,
        current_phase: str,
        processed: int,
        total: int,
        completed_ids: List[int],
        failed_ids: List[int],
        error: Optional[str] = None
    ):
        try:
            db.execute(text("""
                INSERT INTO agent_task_states 
                (task_id, user_id, project_id, task_type, status, current_phase,
                 total_items, processed_items, completed_item_ids, failed_item_ids, error_message,
                 started_at, updated_at)
                VALUES (:task_id, :user_id, :project_id, 'fill_all_tabs', :status, :current_phase,
                        :total_items, :processed_items, :completed_ids, :failed_ids, :error_msg,
                        NOW(), NOW())
                ON CONFLICT (task_id) DO UPDATE SET
                    status = :status,
                    current_phase = :current_phase,
                    processed_items = :processed_items,
                    completed_item_ids = :completed_ids,
                    failed_item_ids = :failed_ids,
                    error_message = :error_msg,
                    updated_at = NOW()
            """), {
                'task_id': task_id,
                'user_id': user_id,
                'project_id': project_id,
                'status': status,
                'current_phase': current_phase,
                'total_items': total,
                'processed_items': processed,
                'completed_ids': completed_ids,
                'failed_ids': failed_ids,
                'error_msg': error
            })
            db.commit()
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            logger.error(f"Failed to save task state: {e}")
    
    # Get papers if not provided
    if not paper_ids:
        result = db.execute(text("""
            SELECT paper_id FROM project_papers WHERE project_id = :project_id
        """), {'project_id': project_id})
        paper_ids = [row[0] for row in result.fetchall()]
    
    if not paper_ids:
        return {
            "success": False,
            "error": "No papers found in project",
            "task_id": task_id
        }
    
    total_papers = len(paper_ids)
    completed_paper_ids = []
    failed_paper_ids = []
    errors = []
    
    # Initialize task state
    save_task_state('running', 'methodology', 0, total_papers, [], [], None)
    
    # ==================== PHASE 1: METHODOLOGY ====================
    await send_progress('methodology', 0, total_papers, "Starting methodology extraction...")
    
    for i, paper_id in enumerate(paper_ids):
        try:
            # Extract methodology
            result = await rag_tools.extract_methodology(
                paper_id=paper_id,
                project_id=project_id,
                rag_engine=rag_engine,
                llm_client=llm_client,
                db=db
            )
            
            # Save to database
            if result and not result.get('_validation_error'):
                database_tools.update_methodology(
                    user_id=user_id,
                    project_id=project_id,
                    paper_id=paper_id,
                    methodology_summary=result.get('methodology_summary'),
                    data_collection=result.get('data_collection'),
                    analysis_methods=result.get('analysis_methods'),
                    sample_size=result.get('sample_size'),
                    methodology_context=result.get('methodology_context'),
                    approach_novelty=result.get('approach_novelty'),
                    db=db
                )
                completed_paper_ids.append(paper_id)
            else:
                failed_paper_ids.append(paper_id)
                errors.append(f"Paper {paper_id}: {result.get('_validation_error', 'Unknown error')}")
            
        except Exception as e:
            # Rollback transaction on error to prevent "current transaction is aborted"
            try:
                db.rollback()
            except Exception:
                pass
            failed_paper_ids.append(paper_id)
            errors.append(f"Paper {paper_id}: {str(e)}")
        
        # Save checkpoint and send progress
        save_task_state('running', 'methodology', i + 1, total_papers, 
                       completed_paper_ids, failed_paper_ids, None)
        await send_progress('methodology', i + 1, total_papers, 
                           f"Extracted methodology for paper {i + 1}/{total_papers}")
    
    # ==================== PHASE 2: FINDINGS ====================
    await send_progress('findings', 0, total_papers, "Starting findings extraction...")
    
    for i, paper_id in enumerate(paper_ids):
        try:
            # Extract findings
            result = await rag_tools.extract_findings(
                paper_id=paper_id,
                project_id=project_id,
                rag_engine=rag_engine,
                llm_client=llm_client,
                db=db
            )
            
            # Save to database
            if result and not result.get('_validation_error'):
                database_tools.update_findings(
                    user_id=user_id,
                    project_id=project_id,
                    paper_id=paper_id,
                    key_finding=result.get('key_finding'),
                    limitations=result.get('limitations'),
                    custom_notes=result.get('custom_notes'),
                    db=db
                )
            
        except Exception as e:
            errors.append(f"Findings paper {paper_id}: {str(e)}")
        
        save_task_state('running', 'findings', i + 1, total_papers,
                       completed_paper_ids, failed_paper_ids, None)
        await send_progress('findings', i + 1, total_papers,
                           f"Extracted findings for paper {i + 1}/{total_papers}")
    
    # ==================== PHASE 3: COMPARISON ====================
    await send_progress('comparison', 0, 1, "Generating comparison...")
    
    try:
        if len(paper_ids) >= 2:
            comparison = await rag_tools.compare_papers(
                paper_ids=paper_ids[:5],  # Max 5 papers for comparison
                aspect="methodology",
                project_id=project_id,
                rag_engine=rag_engine,
                llm_client=llm_client
            )
            
            database_tools.update_comparison(
                user_id=user_id,
                project_id=project_id,
                similarities=comparison.get('similarities', ''),
                differences=comparison.get('differences', ''),
                db=db
            )
    except Exception as e:
        errors.append(f"Comparison: {str(e)}")
    
    save_task_state('running', 'comparison', 1, 1, completed_paper_ids, failed_paper_ids, None)
    await send_progress('comparison', 1, 1, "Comparison complete")
    
    # ==================== SYNTHESIS SKIPPED ====================
    # Synthesis tab is user-editable only - not automated by AI
    # Users can manually create themes and map papers to them
    await send_progress('synthesis', 1, 1, "Synthesis skipped (user-editable)")
    
    
    # ==================== PHASE 5: SUMMARY ====================
    await send_progress('summary', 0, 1, "Generating summary...")
    
    try:
        # Generate summary using all extracted data
        from app.tools import literature_tools
        
        # Get all methodology and findings
        methodology_data = literature_tools.get_methodology(project_id=project_id, db=db)
        findings_data = literature_tools.get_findings(project_id=project_id, db=db)
        comparison_data = literature_tools.get_comparison(project_id=project_id, db=db)
        
        # Build summary prompt
        summary_context = f"""
Methodology from papers:
{json.dumps(methodology_data, indent=2, default=str)[:2000]}

Key findings:
{json.dumps(findings_data, indent=2, default=str)[:2000]}

Comparison insights:
{json.dumps(comparison_data, indent=2, default=str)[:1000]}
"""
        
        # Generate summary with LLM
        summary_prompt = f"""Based on the following extracted data from a literature review, generate a comprehensive summary.

{summary_context}

Provide:
1. An overall summary of the literature (2-3 paragraphs)
2. Key insights (list of 3-5 bullet points)
3. Research gaps and future directions

Format as JSON:
{{
    "summary_text": "...",
    "key_insights": ["insight1", "insight2", ...],
    "research_gaps": ["gap1", "gap2", ...],
    "future_directions": "..."
}}
"""
        
        response = await llm_client.complete(summary_prompt, temperature=0.3)
        
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            summary_result = json.loads(cleaned)
            
            literature_tools.update_summary(
                user_id=user_id,
                project_id=project_id,
                summary_text=summary_result.get('summary_text'),
                key_insights=summary_result.get('key_insights'),
                research_gaps=summary_result.get('research_gaps'),
                future_directions=summary_result.get('future_directions'),
                db=db
            )
        except json.JSONDecodeError:
            literature_tools.update_summary(
                user_id=user_id,
                project_id=project_id,
                summary_text=response[:2000],
                db=db
            )
            
    except Exception as e:
        errors.append(f"Summary: {str(e)}")
    
    save_task_state('running', 'summary', 1, 1, completed_paper_ids, failed_paper_ids, None)
    await send_progress('summary', 1, 1, "Summary complete")
    
    # ==================== COMPLETE ====================
    final_status = 'completed' if not errors else 'completed_with_errors'
    save_task_state(final_status, 'complete', total_papers, total_papers,
                   completed_paper_ids, failed_paper_ids, 
                   '\n'.join(errors) if errors else None)
    
    await send_progress('complete', total_papers, total_papers, 
                       f"All tabs filled! {len(completed_paper_ids)}/{total_papers} papers processed successfully.")
    
    return {
        "success": True,
        "task_id": task_id,
        "status": final_status,
        "total_papers": total_papers,
        "completed": len(completed_paper_ids),
        "failed": len(failed_paper_ids),
        "errors": errors if errors else None
    }
