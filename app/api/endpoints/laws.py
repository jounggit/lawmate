from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from app.services.law_data_service import LawDataService
from app.api.dependencies import get_current_user, get_law_data_service

router = APIRouter(
    prefix="/laws",
    tags=["laws"],
    responses={404: {"description": "Not found"}},
)

@router.get("/search")
async def search_laws(
    q: str = Query(..., description="검색할 키워드 (공백으로 구분)"),
    law_name: Optional[str] = Query(None, description="특정 법령명"),
    current_user = Depends(get_current_user),
    law_service: LawDataService = Depends(get_law_data_service)
):
    """
    키워드로 법령 검색
    """
    keywords = q.split()
    if not keywords:
        raise HTTPException(status_code=400, detail="검색어를 입력해주세요")
    
    laws = await law_service.search_laws(keywords, law_name)
    return {"laws": laws}

@router.get("/detail/{mst}")
async def get_law_detail(
    mst: str = Path(..., description="법령 마스터 번호"),
    law_id: Optional[str] = Query(None, description="법령 ID"),
    jo: Optional[str] = Query(None, description="조번호 (예: 000200 - 2조)"),
    current_user = Depends(get_current_user),
    law_service: LawDataService = Depends(get_law_data_service)
):
    """
    법령 상세 정보 조회
    """
    law_detail = await law_service.get_law_detail(mst, law_id, jo)
    if not law_detail:
        raise HTTPException(status_code=404, detail="법령을 찾을 수 없습니다")
    
    return law_detail

@router.get("/{law_id}/articles")
async def get_law_articles(
    law_id: str = Path(..., description="법령 ID"),
    current_user = Depends(get_current_user),
    law_service: LawDataService = Depends(get_law_data_service)
):
    """
    법령의 조문 목록 조회
    """
    articles = await law_service.search_law_articles(law_id)
    if not articles:
        raise HTTPException(status_code=404, detail="법령 조문을 찾을 수 없습니다")
    
    return {"articles": articles}
