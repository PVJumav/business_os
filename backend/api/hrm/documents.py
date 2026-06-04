from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from backend.core.database import get_db
from backend.models.hrm import HRMDocument
from backend.schemas.hrm.documents import HRDocumentCreate, HRDocumentUpdate, HRDocumentResponse


router = APIRouter(prefix="/hrm/documents", tags=["HRM Documents"])


@router.post("", response_model=HRDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(document: HRDocumentCreate, db: Session = Depends(get_db)):
    new_document = HRMDocument(**document.model_dump())
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    return new_document


@router.get("", response_model=List[HRDocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(HRMDocument).order_by(HRMDocument.created_at.desc()).all()


@router.get("/{document_id}", response_model=HRDocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(HRMDocument).filter(HRMDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="HR document not found")

    return document


@router.put("/{document_id}", response_model=HRDocumentResponse)
def update_document(document_id: UUID, document_update: HRDocumentUpdate, db: Session = Depends(get_db)):
    document = db.query(HRMDocument).filter(HRMDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="HR document not found")

    for field, value in document_update.model_dump(exclude_unset=True).items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}")
def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    document = db.query(HRMDocument).filter(HRMDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="HR document not found")

    db.delete(document)
    db.commit()

    return {"status": "success", "message": "HR document deleted successfully"}