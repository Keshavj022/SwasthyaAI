"""
Medical Document & Image Vault API.

Provides secure file upload, storage, retrieval, and search for medical documents.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models.patient import Patient, DocumentAttachment
from services.file_storage import file_storage

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    patient_id: str = Form(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_date: Optional[date] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    visit_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload medical document or image.

    Args:
        patient_id: Patient identifier
        document_type: Type (xray, lab_report, prescription, etc.)
        title: Document title
        description: Optional description
        document_date: Date of document (not upload date)
        tags: Optional comma-separated tags
        visit_id: Optional link to specific visit
        file: File to upload

    Returns:
        Uploaded document record

    Example:
        ```bash
        curl -X POST "http://127.0.0.1:8000/api/documents/upload" \\
          -F "patient_id=P12345" \\
          -F "document_type=xray" \\
          -F "title=Chest X-Ray" \\
          -F "document_date=2026-01-31" \\
          -F "file=@chest_xray.jpg"
        ```
    """
    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    try:
        # Read file content
        file_content = await file.read()

        # Save file to storage
        file_info = file_storage.save_file(
            file_content=file_content,
            file_name=file.filename,
            patient_id=patient_id,
            document_type=document_type
        )

        # Parse tags
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create database record
        document = DocumentAttachment(
            patient_id=patient.id,
            document_type=document_type,
            title=title,
            description=description,
            file_path=file_info["file_path"],
            file_name=file_info["file_name"],
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            document_date=document_date,
            tags=tag_list,
            visit_id=visit_id
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return {
            "success": True,
            "document_id": document.id,
            "file_name": file_info["file_name"],
            "file_size": file_info["file_size"],
            "mime_type": file_info["mime_type"],
            "title": document.title,
            "document_type": document.document_type,
            "uploaded_at": document.uploaded_at.isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Download document file.

    Args:
        document_id: Document ID

    Returns:
        File content with appropriate MIME type

    Example:
        ```bash
        curl "http://127.0.0.1:8000/api/documents/123/download" -o file.pdf
        ```
    """
    # Get document record
    document = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get file content
    file_content = file_storage.get_file(document.file_path)

    if not file_content:
        raise HTTPException(status_code=404, detail="File not found in storage")

    # Return file with appropriate headers
    return Response(
        content=file_content,
        media_type=document.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{document.file_name}"'
        }
    )


@router.get("/patient/{patient_id}")
async def list_patient_documents(
    patient_id: str,
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    List all documents for a patient.

    Args:
        patient_id: Patient identifier
        document_type: Optional filter by type
        limit: Max results

    Returns:
        List of document records

    Example:
        ```bash
        GET /api/documents/patient/P12345?document_type=xray&limit=10
        ```
    """
    # Verify patient exists
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id,
        Patient.active == True
    ).first()

    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

    # Query documents
    query = db.query(DocumentAttachment).filter(
        DocumentAttachment.patient_id == patient.id
    )

    if document_type:
        query = query.filter(DocumentAttachment.document_type == document_type)

    documents = query.order_by(
        DocumentAttachment.uploaded_at.desc()
    ).limit(limit).all()

    return {
        "patient_id": patient_id,
        "total_documents": len(documents),
        "documents": [
            {
                "document_id": doc.id,
                "title": doc.title,
                "document_type": doc.document_type,
                "file_name": doc.file_name,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "document_date": doc.document_date.isoformat() if doc.document_date else None,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "tags": doc.tags,
                "visit_id": doc.visit_id
            }
            for doc in documents
        ]
    }


@router.get("/search")
async def search_documents(
    patient_id: Optional[str] = Query(None, description="Filter by patient"),
    query: Optional[str] = Query(None, min_length=2, description="Search term"),
    document_type: Optional[str] = Query(None, description="Filter by type"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Search documents by title, description, or tags.

    Args:
        patient_id: Optional patient filter
        query: Search term (searches title and description)
        document_type: Optional document type filter
        tags: Optional comma-separated tags
        limit: Max results

    Returns:
        List of matching documents

    Example:
        ```bash
        GET /api/documents/search?patient_id=P12345&query=xray&tags=chest
        ```
    """
    # Build query
    db_query = db.query(DocumentAttachment)

    # Filter by patient
    if patient_id:
        patient = db.query(Patient).filter(
            Patient.patient_id == patient_id,
            Patient.active == True
        ).first()

        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

        db_query = db_query.filter(DocumentAttachment.patient_id == patient.id)

    # Filter by document type
    if document_type:
        db_query = db_query.filter(DocumentAttachment.document_type == document_type)

    # Search in title and description
    if query:
        search_term = f"%{query}%"
        db_query = db_query.filter(
            (DocumentAttachment.title.ilike(search_term)) |
            (DocumentAttachment.description.ilike(search_term))
        )

    # Filter by tags
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        # Note: SQLite JSON search is limited, this is a simple implementation
        # For production, consider using PostgreSQL with proper JSON operators
        for tag in tag_list:
            db_query = db_query.filter(
                DocumentAttachment.tags.contains(tag)
            )

    # Execute query
    documents = db_query.order_by(
        DocumentAttachment.uploaded_at.desc()
    ).limit(limit).all()

    return {
        "total_results": len(documents),
        "search_params": {
            "patient_id": patient_id,
            "query": query,
            "document_type": document_type,
            "tags": tags
        },
        "documents": [
            {
                "document_id": doc.id,
                "patient_id": patient_id,  # Include for cross-patient searches
                "title": doc.title,
                "description": doc.description,
                "document_type": doc.document_type,
                "file_name": doc.file_name,
                "document_date": doc.document_date.isoformat() if doc.document_date else None,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "tags": doc.tags
            }
            for doc in documents
        ]
    }


@router.get("/{document_id}")
async def get_document_info(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get document metadata (without downloading file).

    Args:
        document_id: Document ID

    Returns:
        Document metadata

    Example:
        ```bash
        GET /api/documents/123
        ```
    """
    document = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get patient info
    patient = db.query(Patient).filter(Patient.id == document.patient_id).first()

    return {
        "document_id": document.id,
        "patient_id": patient.patient_id if patient else None,
        "patient_name": f"{patient.first_name} {patient.last_name}" if patient else None,
        "title": document.title,
        "description": document.description,
        "document_type": document.document_type,
        "file_name": document.file_name,
        "file_size": document.file_size,
        "mime_type": document.mime_type,
        "document_date": document.document_date.isoformat() if document.document_date else None,
        "uploaded_at": document.uploaded_at.isoformat(),
        "tags": document.tags,
        "visit_id": document.visit_id
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete document and associated file.

    Args:
        document_id: Document ID

    Returns:
        Confirmation message

    Example:
        ```bash
        DELETE /api/documents/123
        ```
    """
    document = db.query(DocumentAttachment).filter(
        DocumentAttachment.id == document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from storage
    file_deleted = file_storage.delete_file(document.file_path)

    if not file_deleted:
        # Log warning but continue (file may already be deleted)
        import logging
        logging.warning(f"File not found in storage: {document.file_path}")

    # Delete database record
    db.delete(document)
    db.commit()

    return {
        "success": True,
        "message": "Document deleted",
        "document_id": document_id
    }


@router.get("/storage/stats")
async def get_storage_stats():
    """
    Get storage statistics.

    Returns:
        Storage usage information

    Example:
        ```bash
        GET /api/documents/storage/stats
        ```
    """
    stats = file_storage.get_storage_stats()
    return stats


@router.get("/types")
async def list_document_types():
    """
    List available document types.

    Returns:
        List of document type categories

    Example:
        ```bash
        GET /api/documents/types
        ```
    """
    return {
        "document_types": [
            {"value": "xray", "label": "X-Ray", "category": "imaging"},
            {"value": "ct_scan", "label": "CT Scan", "category": "imaging"},
            {"value": "mri", "label": "MRI", "category": "imaging"},
            {"value": "ultrasound", "label": "Ultrasound", "category": "imaging"},
            {"value": "lab_report", "label": "Lab Report", "category": "lab"},
            {"value": "prescription", "label": "Prescription", "category": "medication"},
            {"value": "insurance_card", "label": "Insurance Card", "category": "administrative"},
            {"value": "consent_form", "label": "Consent Form", "category": "administrative"},
            {"value": "discharge_summary", "label": "Discharge Summary", "category": "clinical"},
            {"value": "other", "label": "Other", "category": "other"}
        ],
        "allowed_extensions": [".jpg", ".jpeg", ".png", ".pdf", ".dcm", ".doc", ".docx", ".txt"],
        "max_file_size_mb": 50
    }
