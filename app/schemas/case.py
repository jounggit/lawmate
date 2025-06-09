from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

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
    id: int = Field(alias="aCase_id")
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    claude_analysis: Optional[str] = None
    legal_category: Optional[str] = None
    keywords: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True
        populate_by_name = True
        arbitrary_types_allowed = True

class CaseWithDocuments(CaseResponse):
    documents: List[DocumentResponse]

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True