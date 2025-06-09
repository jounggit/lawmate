from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Document, ACase, User
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentFormat
from app.services.document_service import DocumentService
from app.api.endpoints.auth import get_current_user

router = APIRouter()
document_service = DocumentService()

@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_in: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """법률 문서 초안 생성"""
    
    # 사례가 사용자의 것인지 확인
    case = db.query(ACase).filter(ACase.aCase_id == document_in.aCase_id, ACase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or not owned by current user")
    
    # 문서 생성
    document = await document_service.create_document(
        db=db,
        case_id=document_in.aCase_id,
        doc_type=document_in.doc_type,
        recipient_info=document_in.recipient_info
    )
    
    return document

@router.get("/", response_model=List[DocumentResponse])
async def read_documents(
    case_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """문서 목록 조회"""
    
    # 쿼리 기본 설정 - 사용자의 사례에 속한 문서만 조회
    query = db.query(Document).join(ACase).filter(ACase.user_id == current_user.id)
    
    # 특정 사례의 문서만 조회
    if case_id:
        query = query.filter(Document.aCase_id == case_id)
    
    # 쿼리 실행
    documents = query.offset(skip).limit(limit).all()
    
    # 응답 포맷 구성
    document_responses = []
    for doc in documents:
        document_responses.append({
            "id": doc.id,
            "title": doc.title,
            "doc_type": doc.doc_type,
            "content": doc.content,
            "created_at": doc.generated_at,
            "updated_at": None,
            "aCase_id": doc.aCase_id
        })
    return document_responses

@router.get("/{document_id}", response_model=DocumentResponse)
async def read_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """특정 문서 조회"""
    document = db.query(Document).join(ACase).filter(
        Document.id == document_id,
        ACase.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 응답 포맷 구성
    return {
        "id": document.id,
        "title": document.title,
        "doc_type": document.doc_type,
        "content": document.content,
        "created_at": document.generated_at,
        "updated_at": None,
        "aCase_id": document.aCase_id
    }

@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    format_type: DocumentFormat = DocumentFormat.txt,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """문서 다운로드"""
    document = db.query(Document).join(ACase).filter(
        Document.id == document_id,
        ACase.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 문서 포맷팅
    formatted = document_service.format_document_for_download(document, format_type.value)
    
    # 응답 생성
    return Response(
        content=formatted["content"],
        media_type=formatted["mime_type"],
        headers={"Content-Disposition": f"attachment; filename={formatted['filename']}"}
    )