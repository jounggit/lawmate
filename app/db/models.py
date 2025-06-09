from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint, Date
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime


Base = declarative_base()

# User 테이블
class User(Base):
    __tablename__ = "user"  # 대문자 'User'에서 소문자 'user'로 변경

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
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(String(30), default="진행중")
    created_at = Column(DateTime, default=datetime.utcnow)
    claude_analysis = Column(Text, nullable=True)  # Claude API 상담 내용 저장 필드
    legal_category = Column(String(100), nullable=True)  # 법률 분야
    keywords = Column(String(500), nullable=True)  # 키워드 (쉼표로 구분)

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
    law_code = Column(String(20), unique=True, nullable=False)  # 법령 ID (국가법령정보 API에서 반환하는 lawId)
    law_name = Column(String(100), nullable=False)  # 법령명
    law_type = Column(String(50))  # 법종구분
    promulgation_date = Column(String(10))  # 공포일자
    link = Column(Text)  # 법령 링크
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Law_Article 테이블 (법령 조문)
class LawArticle(Base):
    __tablename__ = "Law_Article"

    article_id = Column(Integer, primary_key=True, autoincrement=True)
    law_id = Column(Integer, ForeignKey("Law.law_id"), nullable=False)  # 법령 ID
    article_number = Column(String(50), nullable=False)  # 조문번호
    article_title = Column(String(200))  # 조문제목
    content = Column(Text, nullable=False)  # 조문내용
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Law 테이블과의 관계 설정
    law = relationship("Law", backref="articles")

    # 동일 법령의 동일 조문번호는 중복되지 않음
    __table_args__ = (
        UniqueConstraint('law_id', 'article_number', name='uix_law_article'),
    )

# Precedent 테이블
class Precedent(Base):
    __tablename__ = "Precedent"

    precedent_id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(100), unique=True, nullable=False)  # 사건번호
    case_name = Column(String(200))  # 사건명
    court = Column(String(100))  # 법원
    decision_date = Column(String(10))  # 판결일자
    summary = Column(Text)  # 판결요지
    judgment_text = Column(Text)  # 판결내용
    link = Column(Text)  # 판례 링크
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# aCase_Law 테이블 (aCase와 법령 연결)
class ACaseLaw(Base):
    __tablename__ = "aCase_Law"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aCase_id = Column(Integer, ForeignKey("aCase.aCase_id"), nullable=False)
    law_id = Column(Integer, ForeignKey("Law.law_id"), nullable=False)
    article_id = Column(Integer, ForeignKey("Law_Article.article_id"), nullable=True)  # 특정 조문을 참조하는 경우
    relevance_score = Column(Integer, default=0)  # 관련성 점수 (0-100)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 동일 사례에 동일 법령/조문 중복 방지
    __table_args__ = (
        UniqueConstraint('aCase_id', 'law_id', 'article_id', name='uix_case_law_article'),
    )

# aCase_Precedent 테이블 (aCase와 판례 연결)
class ACasePrecedent(Base):
    __tablename__ = "aCase_Precedent"

    id = Column(Integer, primary_key=True, autoincrement=True)
    aCase_id = Column(Integer, ForeignKey("aCase.aCase_id"), nullable=False)
    precedent_id = Column(Integer, ForeignKey("Precedent.precedent_id"), nullable=False)
    relevance_score = Column(Integer, default=0)  # 관련성 점수 (0-100)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 동일 사례에 동일 판례 중복 방지
    __table_args__ = (
        UniqueConstraint('aCase_id', 'precedent_id', name='uix_case_precedent'),
    )
