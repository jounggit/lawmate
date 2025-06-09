from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    """현재 로그인한 사용자 정보 조회"""
    return {
        "id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.name,
        "is_active": True
    }

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """현재 로그인한 사용자 정보 업데이트"""
    
    # 업데이트할 필드 설정
    update_data = user_in.dict(exclude_unset=True)
    
    # 비밀번호가 있으면 해시 처리
    if "password" in update_data:
        from app.api.endpoints.auth import get_password_hash
        update_data["password"] = get_password_hash(update_data.pop("password"))
    
    # 사용자 정보 업데이트
    for field, value in update_data.items():
        if field == "full_name":
            # full_name은 name 필드에 매핑
            setattr(current_user, "name", value)
        else:
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # 응답 데이터 구성
    return {
        "id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.name,
        "is_active": True
    }