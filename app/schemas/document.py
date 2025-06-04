from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class DocumentFormat(str, Enum):
    txt = "txt"
    html = "html"

class DocumentBase(BaseModel):
    title: Optional[str] = None
    doc_type: str

class DocumentCreate(DocumentBase):
    case_id: int
    recipient_info: Optional[Dict[str, Any]] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    case_id: int

    class Config:
        orm_mode = True