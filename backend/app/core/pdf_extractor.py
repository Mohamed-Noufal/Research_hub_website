"""
Enhanced PDF content extraction and storage
Stores sections, figures, tables, equations in database
"""
import re
import os
import logging
from typing import Dict, List, Optional
from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.orm import Session

# Docling imported lazily inside functions to avoid import errors

logger = logging.getLogger(__name__)


def extract_sections_from_markdown(markdown_content: str) -> List[Dict]:
    """
    Extract sections from markdown based on headings.
    Returns list of {section_type, section_title, content, order_index}
    """
    sections = []
    
    # Common academic section patterns
    section_patterns = {
        'abstract': r'(?i)^#+\s*abstract',
        'introduction': r'(?i)^#+\s*introduction',
        'methodology': r'(?i)^#+\s*(methodology|methods|materials\s+and\s+methods)',
        'results': r'(?i)^#+\s*results',
        'discussion': r'(?i)^#+\s*discussion',
        'conclusion': r'(?i)^#+\s*(conclusion|conclusions)',
        'references': r'(?i)^#+\s*references',
        'related_work': r'(?i)^#+\s*(related\s+work|literature\s+review|background)',
    }
    
    # Split by headings (lines starting with #)
    lines = markdown_content.split('\n')
    current_section = None
    current_content = []
    order_index = 0
    
    for line in lines:
        # Check if this is a heading
        if line.strip().startswith('#'):
            # Save previous section
            if current_section:
                sections.append({
                    'section_type': current_section['type'],
                    'section_title': current_section['title'],
                    'content': '\n'.join(current_content).strip(),
                    'order_index': order_index
                })
                order_index += 1
            
            # Determine section type from heading
            heading_text = line.strip().lstrip('#').strip()
            section_type = 'other'
            
            for stype, pattern in section_patterns.items():
                if re.match(pattern, line.strip()):
                    section_type = stype
                    break
            
            current_section = {'type': section_type, 'title': heading_text}
            current_content = []
        else:
            if current_section:
                current_content.append(line)
    
    # Don't forget last section
    if current_section and current_content:
        sections.append({
            'section_type': current_section['type'],
            'section_title': current_section['title'],
            'content': '\n'.join(current_content).strip(),
            'order_index': order_index
        })
    
    # If no sections found, treat entire content as one section
    if not sections:
        sections.append({
            'section_type': 'full_document',
            'section_title': 'Document',
            'content': markdown_content,
            'order_index': 0
        })
    
    return sections


def extract_tables_from_docling(doc_result) -> List[Dict]:
    """Extract tables from Docling result"""
    tables = []
    try:
        # Docling stores tables in document.tables
        if hasattr(doc_result.document, 'tables'):
            for idx, table in enumerate(doc_result.document.tables):
                tables.append({
                    'table_number': f"Table {idx + 1}",
                    'caption': getattr(table, 'caption', ''),
                    'content_markdown': table.export_to_markdown() if hasattr(table, 'export_to_markdown') else str(table),
                    'content_json': None,  # Would need more parsing
                    'order_index': idx
                })
    except Exception as e:
        logger.warning(f"Could not extract tables: {e}")
    return tables


def extract_equations_from_markdown(markdown_content: str) -> List[Dict]:
    """Extract equations from markdown (LaTeX blocks)"""
    equations = []
    
    # Match inline math $...$ and block math $$...$$
    inline_pattern = r'\$([^$]+)\$'
    block_pattern = r'\$\$([^$]+)\$\$'
    
    # Block equations
    for idx, match in enumerate(re.finditer(block_pattern, markdown_content)):
        latex = match.group(1).strip()
        # Get some context around the equation
        start = max(0, match.start() - 100)
        end = min(len(markdown_content), match.end() + 100)
        context = markdown_content[start:end]
        
        equations.append({
            'equation_number': f"Eq. {idx + 1}",
            'latex': latex,
            'context': context.strip(),
            'order_index': idx
        })
    
    return equations


async def process_and_store_pdf(
    db: Session,
    paper_id: int,
    pdf_path: str,
    user_id: str,
    embed_model = None
) -> Dict:
    """
    Process PDF and store all extracted content in database tables.
    
    Args:
        db: Database session
        paper_id: Paper ID in papers table
        pdf_path: Path to PDF file
        user_id: User who owns this paper
        embed_model: HuggingFace embedding model for generating embeddings
    
    Returns:
        Dict with extraction statistics
    """
    stats = {
        'sections': 0,
        'figures': 0,
        'tables': 0,
        'equations': 0,
        'error': None
    }
    
    if not os.path.exists(pdf_path):
        stats['error'] = f"PDF not found: {pdf_path}"
        return stats
    
    try:
        # Update processing status
        db.execute(text("""
            UPDATE papers 
            SET processing_status = 'processing', processing_started_at = NOW()
            WHERE id = :paper_id
        """), {'paper_id': paper_id})
        db.commit()
        
        # Parse PDF with Docling (blocking operation, run in thread pool)
        import asyncio
        loop = asyncio.get_event_loop()
        
        def run_docling_conversion():
            logger.info(f"📄 Parsing PDF for paper {paper_id} with Docling...")
            from docling.document_converter import DocumentConverter
            converter = DocumentConverter()
            return converter.convert(pdf_path)
            
        result = await loop.run_in_executor(None, run_docling_conversion)
        
        # Export to markdown
        markdown_content = result.document.export_to_markdown()
        
        if not markdown_content or len(markdown_content) < 100:
            stats['error'] = "Very little content extracted"
            return stats
        
        # 1. Extract and store SECTIONS
        sections = extract_sections_from_markdown(markdown_content)
        for section in sections:
            # Generate embedding if model available
            embedding = None
            if embed_model and section['content']:
                try:
                    embedding = embed_model.get_text_embedding(section['content'][:2000])
                except Exception as e:
                    logger.warning(f"Failed to embed section: {e}")
            
            db.execute(text("""
                INSERT INTO paper_sections 
                (paper_id, user_id, section_type, section_title, content, word_count, order_index, embedding)
                VALUES (:paper_id, :user_id, :section_type, :section_title, :content, :word_count, :order_index, :embedding)
            """), {
                'paper_id': paper_id,
                'user_id': user_id,
                'section_type': section['section_type'],
                'section_title': section['section_title'],
                'content': section['content'],
                'word_count': len(section['content'].split()),
                'order_index': section['order_index'],
                'embedding': embedding
            })
            stats['sections'] += 1
        
        # 2. Extract and store TABLES
        tables = extract_tables_from_docling(result)
        for table in tables:
            db.execute(text("""
                INSERT INTO paper_tables
                (paper_id, user_id, table_number, caption, content_markdown, order_index)
                VALUES (:paper_id, :user_id, :table_number, :caption, :content_markdown, :order_index)
            """), {
                'paper_id': paper_id,
                'user_id': user_id,
                'table_number': table['table_number'],
                'caption': table.get('caption', ''),
                'content_markdown': table['content_markdown'],
                'order_index': table['order_index']
            })
            stats['tables'] += 1
        
        # 3. Extract and store EQUATIONS
        equations = extract_equations_from_markdown(markdown_content)
        for equation in equations:
            db.execute(text("""
                INSERT INTO paper_equations
                (paper_id, user_id, equation_number, latex, context, order_index)
                VALUES (:paper_id, :user_id, :equation_number, :latex, :context, :order_index)
            """), {
                'paper_id': paper_id,
                'user_id': user_id,
                'equation_number': equation['equation_number'],
                'latex': equation['latex'],
                'context': equation['context'],
                'order_index': equation['order_index']
            })
            stats['equations'] += 1
        
        # Update paper with counts
        db.execute(text("""
            UPDATE papers SET
                processing_status = 'completed',
                processing_completed_at = NOW(),
                section_count = :sections,
                table_count = :tables,
                equation_count = :equations,
                is_processed = TRUE
            WHERE id = :paper_id
        """), {
            'paper_id': paper_id,
            'sections': stats['sections'],
            'tables': stats['tables'],
            'equations': stats['equations']
        })
        
        db.commit()
        logger.info(f"✅ Stored: {stats['sections']} sections, {stats['tables']} tables, {stats['equations']} equations")
        
    except Exception as e:
        logger.error(f"❌ Error processing PDF: {e}")
        stats['error'] = str(e)
        db.execute(text("""
            UPDATE papers 
            SET processing_status = 'failed', processing_error = :error
            WHERE id = :paper_id
        """), {'paper_id': paper_id, 'error': str(e)})
        db.commit()
    
    return stats
