from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(settings.DATABASE_URL)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모델 기본 클래스
Base = declarative_base()

# 의존성 주입용 데이터베이스 세션
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()