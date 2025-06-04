from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.db.models import Lawyer, User
from app.schemas.lawyer import LawyerResponse, LawyerCreate, LawyerUpdate
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[LawyerResponse])
async def search_lawyers(
    keyword: str = None,
    specialization: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
) -> Any:
    """변호사 검색"""
    
    query = db.query(Lawyer).filter(Lawyer.is_verified == True)
    
    # 키워드 검색 (이름, 전문 분야, 소개)
    if keyword:
        query = query.filter(
            or_(
                Lawyer.name.contains(keyword),
                Lawyer.specialization.contains(keyword),
                Lawyer.bio.contains(keyword)
            )
        )
    
    # 전문 분야별 필터링
    if specialization:
        query = query.filter(Lawyer.specialization.contains(specialization))
    
    # 결과 정렬 (경력 및 평점 기준)
    query = query.order_by(Lawyer.experience_years.desc(), Lawyer.rating.desc())
    
    lawyers = query.offset(skip).limit(limit).all()
    return lawyers

@router.get("/{lawyer_id}", response_model=LawyerResponse)
async def read_lawyer(
    lawyer_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """특정 변호사 정보 조회"""
    lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id, Lawyer.is_verified == True).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return lawyer

@router.post("/", response_model=LawyerResponse)
async def create_lawyer(
    lawyer_in: LawyerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """변호사 정보 등록 (관리자 전용)"""
    
    # 관리자 권한 확인 (간단한 예시, 실제로는 더 복잡한 권한 체크 필요)
    if current_user.email != "admin@lawmate.com":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 이메일 중복 확인
    db_lawyer = db.query(Lawyer).filter(Lawyer.email == lawyer_in.email).first()
    if db_lawyer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 변호사 정보 생성
    db_lawyer = Lawyer(**lawyer_in.dict())
    db.add(db_lawyer)
    db.commit()
    db.refresh(db_lawyer)
    
    return db_lawyer

@router.put("/{lawyer_id}", response_model=LawyerResponse)
async def update_lawyer(
    lawyer_id: int,
    lawyer_in: LawyerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """변호사 정보 업데이트 (관리자 전용)"""
    
    # 관리자 권한 확인
    if current_user.email != "admin@lawmate.com":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    
    # 업데이트할 필드 설정
    update_data = lawyer_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lawyer, field, value)
    
    db.commit()
    db.refresh(lawyer)
    return lawyer

@router.get("/recommend/{case_id}", response_model=List[LawyerResponse])
async def recommend_lawyers(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """사례 기반 변호사 추천"""
    
    from app.db.models import Case
    
    # 사례 조회
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # 사례 카테고리에 맞는 변호사 추천
    recommended_lawyers = db.query(Lawyer).filter(
        Lawyer.is_verified == True,
        Lawyer.specialization.contains(case.category)
    ).order_by(
        Lawyer.experience_years.desc(),
        Lawyer.rating.desc()
    ).limit(5).all()
    
    return recommended_lawyers