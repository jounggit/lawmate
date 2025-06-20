from typing import Optional, List
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    marketing_consent: Optional[bool] = False

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool = True

    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class LawyerBase(BaseModel):
    email: EmailStr
    full_name: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class LawyerCreate(LawyerBase):
    password: str
    license_number: str
    specialization: List[str] = []
    is_verified: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None