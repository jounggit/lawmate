from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, Base

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="LawMate API",
    description="법률 정보 제공 및 문서 생성 API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 
from app.api.endpoints import auth, users, cases, lawyers, documents, laws, precedents

app.include_router(auth.router, tags=["인증"])
app.include_router(users.router, prefix="/users", tags=["사용자"])
app.include_router(cases.router, prefix="/cases", tags=["법률 사례"])
app.include_router(lawyers.router, prefix="/lawyers", tags=["변호사"])
app.include_router(documents.router, prefix="/documents", tags=["문서"])
app.include_router(laws.router, prefix="/laws", tags=["법령"])
app.include_router(precedents.router, prefix="/precedents", tags=["판례"])

@app.get("/")
def root():
    return {"message": "Welcome to LawMate API"}