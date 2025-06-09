from typing import List, Dict, Any, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ACase, User, Document, Law, LawArticle, Precedent
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse, CaseWithDocuments
from app.schemas.document import DocumentResponse
from app.services.claude_service import ClaudeService
from app.services.law_data_service import LawDataService
from app.services.legal_consultation_service import LegalConsultationService
from app.api.endpoints.auth import get_current_user

router = APIRouter()
claudeService = ClaudeService()
law_data_service = LawDataService()

# 개발 환경이나 API 연결 문제시 사용할 모의 데이터 플래그
# 실제 배포 환경에서는 False로 설정
USE_MOCK_DATA = True

legal_consultation_service = LegalConsultationService(use_mock_data=USE_MOCK_DATA)

@router.post("/", response_model=CaseResponse)
async def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """법률 사례 생성"""
    
    # 사례 분석 - Claude API 호출
    analysis = await claudeService.analyze_legal_issue(case_in.description)
    
    # 분석 결과에서 데이터 추출
    legal_category = analysis.get("legal_category", case_in.category) if isinstance(analysis, dict) else case_in.category
    
    # 키워드 추출 및 문자열로 변환
    keywords = ",".join(analysis.get("keywords", [])) if isinstance(analysis, dict) and "keywords" in analysis else ""
    
    # Claude 분석 결과를 JSON으로 저장
    claude_analysis_json = json.dumps(analysis, ensure_ascii=False) if isinstance(analysis, dict) else json.dumps({"raw_response": str(analysis)}, ensure_ascii=False)
    
    # 새 사례 생성 - Claude API 분석 결과 포함
    db_case = ACase(
        title=case_in.title,
        description=case_in.description,
        aCase_type=case_in.category or "일반",  # category를 aCase_type으로 맵핑
        status="open",  # 초기 상태
        user_id=current_user.id,
        claude_analysis=claude_analysis_json,  # Claude API 분석 결과 저장
        legal_category=legal_category,  # 법률 분야 저장
        keywords=keywords  # 키워드 저장
    )
    
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    # 법률 상담 서비스를 통한 추가 처리
    if isinstance(analysis, dict) and "keywords" in analysis:
        try:
            # 법령과 판례 검색 및 저장 (비동기로 처리)
            await legal_consultation_service.process_consultation(
                db=db,
                case_id=db_case.aCase_id,
                description=case_in.description
            )
        except Exception as e:
            print(f"법령/판례 처리 중 오류 발생: {e}")
            # 오류가 발생해도 사례 생성은 성공으로 처리
    
    return db_case

@router.get("/", response_model=List[CaseResponse])
async def read_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """사용자의 법률 사례 목록 조회"""
    cases = db.query(ACase).filter(ACase.user_id == current_user.id).offset(skip).limit(limit).all()
    
    # ACase 모델에서 CaseResponse 스키마로 변환
    result = []
    for case in cases:
        result.append({
            "id": case.aCase_id,
            "title": getattr(case, 'title', '제목 없음'),  # title 필드가 없을 수 있음
            "description": case.description,
            "category": getattr(case, 'aCase_type', None),  # aCase_type을 category로 매핑
            "status": case.status,
            "created_at": case.created_at,
            "updated_at": None,  # updated_at 필드가 없음
            "claude_analysis": case.claude_analysis,  # Claude 분석 결과 추가
            "legal_category": case.legal_category,  # 법률 분야 추가
            "keywords": case.keywords  # 키워드 추가
        })
    return result

@router.get("/{case_id}", response_model=CaseWithDocuments)
async def read_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """특정 법률 사례 상세 조회"""
    case = db.query(ACase).filter(ACase.aCase_id == case_id, ACase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # 관련 문서 조회
    documents = db.query(Document).filter(Document.aCase_id == case_id).all()
    
    # 관련 법령 및 조문 조회
    law_articles = []
    laws_query = db.query(Law, LawArticle)\
                  .join(ACaseLaw, ACaseLaw.law_id == Law.law_id)\
                  .join(LawArticle, LawArticle.law_id == Law.law_id)\
                  .filter(ACaseLaw.aCase_id == case_id)\
                  .all()
    
    # 관련 판례 조회
    precedents = db.query(Precedent)\
                  .join(ACasePrecedent, ACasePrecedent.precedent_id == Precedent.precedent_id)\
                  .filter(ACasePrecedent.aCase_id == case_id)\
                  .all()
    
    # 응답 포맷 구성
    return {
        "id": case.aCase_id,
        "title": getattr(case, 'title', '제목 없음'),  # title 필드가 없을 수 있음
        "description": case.description,
        "category": getattr(case, 'aCase_type', None),  # aCase_type을 category로 매핑
        "status": case.status,
        "created_at": case.created_at,
        "updated_at": None,  # updated_at 필드가 없음
        "claude_analysis": case.claude_analysis,  # Claude 분석 결과 추가
        "legal_category": case.legal_category,  # 법률 분야 추가
        "keywords": case.keywords,  # 키워드 추가
        "documents": documents,
        "laws": [{"law_name": law.law_name, "law_id": law.law_id} for law, _ in laws_query],
        "precedents": [{"case_number": p.case_number, "precedent_id": p.precedent_id} for p in precedents]
    }

@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_in: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """법률 사례 정보 업데이트"""
    case = db.query(ACase).filter(ACase.aCase_id == case_id, ACase.user_id == current_user.id).first()
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
    case = db.query(ACase).filter(ACase.aCase_id == case_id, ACase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # 법률 상담 처리
    try:
        consultation_result = await legal_consultation_service.process_consultation(
            db=db,
            case_id=case_id,
            description=case.description
        )
        
        # 처리 결과 반환
        return consultation_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"법률 상담 처리 중 오류가 발생했습니다: {str(e)}"
        )
