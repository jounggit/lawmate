from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from app.services.law_data_service import LawDataService
from app.api.dependencies import get_current_user, get_law_data_service

router = APIRouter(
    prefix="/precedents",
    tags=["precedents"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search")
async def search_precedents(
    q: Optional[str] = Query(None, description="검색할 키워드 (공백으로 구분)"),
    court: Optional[str] = Query(None, description="법원명 (예: 대법원, 서울고등법원)"),
    search_type: int = Query(1, description="검색범위 (1: 판례명, 2: 본문검색)"),
    case_number: Optional[str] = Query(None, description="사건번호"),
    reference_law: Optional[str] = Query(None, description="참조법령명 (예: 형법, 민법)"),
    page: int = Query(1, description="검색 결과 페이지"),
    display: int = Query(20, description="검색 결과 개수 (최대 100)"),
    current_user = Depends(get_current_user),
    law_service: LawDataService = Depends(get_law_data_service)
):
    """
    키워드, 법원명, 사건번호 등으로 판례 검색
    """
    keywords = q.split() if q else None
    
    if not keywords and not court and not case_number and not reference_law:
        raise HTTPException(status_code=400, detail="최소한 하나 이상의 검색 조건이 필요합니다")
    
    precedents = await law_service.search_precedents(
        keywords=keywords, 
        court=court,
        search_type=search_type,
        case_number=case_number,
        reference_law=reference_law,
        page=page,
        display=display
    )
    
    return {"precedents": precedents}

@router.get("/{precedent_id}")
async def get_precedent_detail(
    precedent_id: str = Path(..., description="판례 일련번호"),
    current_user = Depends(get_current_user),
    law_service: LawDataService = Depends(get_law_data_service)
):
    """
    판례 상세 정보 조회
    """
    precedent_detail = await law_service.get_precedent_detail(precedent_id)
    if not precedent_detail:
        raise HTTPException(status_code=404, detail="판례를 찾을 수 없습니다")
    
    return precedent_detail
