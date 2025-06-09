from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any

from app.api.endpoints.auth import get_current_user
from app.services.law_data_service import LawDataService
from app.services.legal_consultation_service import LegalConsultationService

# 공통 의존성 함수들
def get_admin_user(current_user = Depends(get_current_user)):
    """관리자 권한 확인 의존성"""
    if current_user.email != "admin@lawmate.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user

def get_law_data_service() -> LawDataService:
    """법률 데이터 서비스 인스턴스 제공"""
    return LawDataService()

def get_legal_consultation_service() -> LegalConsultationService:
    """법률 상담 서비스 인스턴스 제공"""
    return LegalConsultationService()