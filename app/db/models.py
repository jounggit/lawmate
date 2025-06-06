from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint, Date
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime


Base = declarative_base()

# User 테이블
class User(Base):
    __tablename__ = "User"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    is_lawyer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Lawyer 테이블
class Lawyer(Base):
    __tablename__ = "Lawyer"

    lawyer_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    registration_number = Column(String(100), unique=True, nullable=False)
    expertise = Column(String(100))
    region = Column(String(100))
    verified = Column(Boolean, default=False)
    approved_at = Column(DateTime)

# Review 테이블
class Review(Base):
    __tablename__ = "Review"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("Lawyer.lawyer_id"), nullable=False)
    match_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="rating_range"),
    )

# Notice 테이블
class Notice(Base):
    __tablename__ = "Notice"

    notice_id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Community_Post 테이블
class CommunityPost(Base):
    __tablename__ = "Community_Post"

    post_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50))
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# aCase 테이블
class ACase(Base):
    __tablename__ = "aCase"

    aCase_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    aCase_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="진행중")
    created_at = Column(DateTime, default=datetime.utcnow)

# Matching_Log 테이블
class MatchingLog(Base):
    __tablename__ = "Matching_Log"

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.user_id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("Lawyer.lawyer_id"), nullable=False)
    aCase_id = Column(Integer, ForeignKey("aCase.aCase_id"), nullable=False)
    matched_at = Column(DateTime, default=datetime.utcnow)

# Law_Reference 테이블
class LawReference(Base):
    __tablename__ = "Law_Reference"

    law_id = Column(Integer, primary_key=True, autoincrement=True)
    aCase_id = Column(Integer, ForeignKey("aCase.aCase_id"), nullable=False)
    law_title = Column(String(100), nullable=False)
    article_number = Column(String(20))
    summary = Column(Text)

# Document 테이블
class Document(Base):
    __tablename__ = "Document"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    aCase_id = Column(Integer, ForeignKey("aCase.aCase_id"), nullable=False)
    doc_type = Column(String(50))
    content = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)

# Law 테이블
class Law(Base):
    __tablename__ = "Law"

    law_id = Column(Integer, primary_key=True, autoincrement=True)
    law_name = Column(String(100), nullable=False)
    category = Column(String(50))
    article = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    last_updated = Column(Date)
    source_url = Column(Text)

# Precedent 테이블
class Precedent(Base):
    __tablename__ = "Precedent"

    precedent_id = Column(Integer, primary_key=True, autoincrement=True)
    aCase = Column(String(100), nullable=False)
    aCase_number = Column(String(100), nullable=False)
    decision_date = Column(Date)
    summary = Column(Text)
    judgment_text = Column(Text)
    legal_basis = Column(Text)
    source_url = Column(Text)
