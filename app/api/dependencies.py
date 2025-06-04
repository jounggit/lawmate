from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any

from app.api.endpoints.auth import get_current_user

# 공통 의존성 함수들
def get_admin_user(current_user = Depends(get_current_user)):
    """관리자 권한 확인 의존성"""
    if current_user.email != "admin@lawmate.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user