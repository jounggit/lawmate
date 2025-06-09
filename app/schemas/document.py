from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class DocumentFormat(str, Enum):
    txt = "txt"
    html = "html"

class DocumentBase(BaseModel):
    title: Optional[str] = None
    doc_type: str

class DocumentCreate(DocumentBase):
    aCase_id: int
    recipient_info: Optional[Dict[str, Any]] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int = Field(alias="doc_id")
    content: str
    created_at: datetime = Field(alias="generated_at")
    updated_at: Optional[datetime] = None
    aCase_id: int

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True