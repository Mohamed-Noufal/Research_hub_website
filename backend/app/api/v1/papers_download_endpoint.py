@router.post("/{paper_id}/download-pdf")
async def download_pdf(
    paper_id: int,
    db: Session = Depends(get_db)
):
    """
    Download PDF from external URL and save locally
    """
    import httpx
    import asyncio
    
    # Check if paper exists
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if paper has external PDF URL
    if not paper.pdf_url:
        raise HTTPException(status_code=400, detail="Paper has no PDF URL")
    
    # Check if already local
    if paper.pdf_url.startswith("http://localhost"):
        return {
            "message": "PDF already stored locally",
            "pdf_url": paper.pdf_url,
            "already_local": True
        }
    
    # Create upload directory
    upload_dir = Path("uploads/pdfs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{paper_id}.pdf"
    file_path = upload_dir / filename
    
    try:
        # Download PDF with timeout
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            logger.info(f"Downloading PDF from {paper.pdf_url}")
            response = await client.get(paper.pdf_url)
            response.raise_for_status()
            
            # Verify content type
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"Unexpected content type: {content_type}")
            
            # Save file
            with file_path.open("wb") as f:
                f.write(response.content)
            
            logger.info(f"PDF downloaded successfully: {file_path}")
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to download PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")
    
    # Update paper PDF URL to local
    local_url = f"http://localhost:8000/uploads/pdfs/{filename}"
    paper.pdf_url = local_url
    
    db.commit()
    db.refresh(paper)
    
    return {
        "message": "PDF downloaded and saved successfully",
        "pdf_url": local_url,
        "paper_id": paper_id,
        "file_size": file_path.stat().st_size,
        "paper": {
            "id": paper.id,
            "title": paper.title,
            "abstract": paper.abstract,
            "authors": paper.authors,
            "publication_date": paper.publication_date,
            "doi": paper.doi,
            "citation_count": paper.citation_count,
            "venue": paper.venue,
            "pdf_url": paper.pdf_url,
            "source": paper.source,
            "category": paper.category
        }
    }
