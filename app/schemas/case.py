from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.schemas.document import DocumentResponse

class CaseBase(BaseModel):
    title: str
    description: str
    category: Optional[str] = None

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class CaseResponse(CaseBase):
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class CaseWithDocuments(CaseResponse):
    documents: List[DocumentResponse]

    class Config:
        orm_mode = True