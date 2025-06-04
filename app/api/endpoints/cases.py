from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Case, User, Document
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseWithDocuments
from app.schemas.document import DocumentResponse
from app.services.claude_service import ClaudeService
from app.services.law_data_service import LawDataService
from app.api.endpoints.auth import get_current_user

router = APIRouter()
claude_service = ClaudeService()
law_data_service = LawDataService()

@router.post("/", response_model=CaseResponse)
async def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """법률 사례 생성"""
    
    # 사례 분석
    analysis = await claude_service.analyze_legal_issue(case_in.description)
    
    # 법률 카테고리 설정 (분석 결과에서 가져오거나 사용자 입력 사용)
    category = analysis.get("legal_category", case_in.category) if isinstance(analysis, dict) else case_in.category
    
    # 새 사례 생성
    db_case = Case(
        title=case_in.title,
        description=case_in.description,
        category=category,
        status="open",  # 초기 상태
        user_id=current_user.id
    )
    
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    return db_case

@router.get("/", response_model=List[CaseResponse])
async def read_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """사용자의 법률 사례 목록 조회"""
    cases = db.query(Case).filter(Case.user_id == current_user.id).offset(skip).limit(limit).all()
    return cases

@router.get("/{case_id}", response_model=CaseWithDocuments)
async def read_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """특정 법률 사례 상세 조회"""
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # 관련 문서 조회
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    
    # 응답 포맷 구성
    return {
        "id": case.id,
        "title": case.title,
        "description": case.description,
        "category": case.category,
        "status": case.status,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "documents": documents
    }

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_in: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """법률 사례 정보 업데이트"""
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # 업데이트할 필드 설정
    update_data = case_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    db.commit()
    db.refresh(case)
    return case

@router.post("/{case_id}/analyze", response_model=Dict[str, Any])
async def analyze_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """법률 사례 분석 및 관련 법령/판례 조회"""
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # 사례 분석
    analysis = await claude_service.analyze_legal_issue(case.description)
    
    # 분석 결과에서 키워드 추출
    keywords = analysis.get("keywords", []) if isinstance(analysis, dict) else []
    if not keywords and isinstance(analysis, dict):
        # 키워드가 없으면 법률 쟁점 사용
        keywords = analysis.get("key_issues", [])
    
    # 관련 법령 조회
    laws = []
    if keywords:
        laws = await law_data_service.search_laws(keywords)
    
    # 관련 판례 조회
    cases = []
    if keywords:
        cases = await law_data_service.search_cases(keywords)
    
    # 법령 및 판례 요약
    summary = await claude_service.summarize_legal_info(laws, cases)
    
    # 종합 결과 반환
    return {
        "analysis": analysis,
        "relevant_laws": laws,
        "relevant_cases": cases,
        "summary": summary
    }