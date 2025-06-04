from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 관계 설정
    cases = relationship("Case", back_populates="user")
    
class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(Text)
    category = Column(String(50))  # 법률 분야 카테고리
    status = Column(String(20))    # 진행 상태
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 관계 설정
    user = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case")
    
class Lawyer(Base):
    __tablename__ = "lawyers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    specialization = Column(String(100))  # 전문 분야
    experience_years = Column(Integer)
    office_address = Column(String(200))
    bio = Column(Text)
    rating = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    content = Column(Text)
    doc_type = Column(String(50))  # 문서 유형 (내용증명, 이의제기서 등)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    case_id = Column(Integer, ForeignKey("cases.id"))
    
    # 관계 설정
    case = relationship("Case", back_populates="documents")