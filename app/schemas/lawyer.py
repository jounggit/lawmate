from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

class LawyerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    specialization: str
    experience_years: int
    office_address: str
    bio: Optional[str] = None

class LawyerCreate(LawyerBase):
    is_verified: bool = False

class LawyerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    office_address: Optional[str] = None
    bio: Optional[str] = None
    rating: Optional[float] = None
    is_verified: Optional[bool] = None

class LawyerResponse(LawyerBase):
    id: int
    rating: float
    is_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True