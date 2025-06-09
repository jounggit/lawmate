from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

from app.core.config import settings
from app.db.database import engine, Base, create_tables

# 데이터베이스 테이블 생성 여부 확인
if create_tables:
    # 테이블 생성 옵션이 True인 경우에만 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("테이블 생성이 진행되었습니다.")
else:
    print("기존 테이블을 사용합니다. 테이블 생성을 건너뜁니다.")

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 프론트엔드 주소를 명시적으로 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# 요청 미들웨어 추가 - 모든 요청 로깅
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"\n\n[요청] {request.method} {request.url}")
    print(f"API 경로: {request.url.path}")
    print(f"Headers: {dict(request.headers)}")
    
    # 요청 처리
    response = await call_next(request)
    
    # 응답 정보 로깅
    print(f"[응답] 상태 코드: {response.status_code}")
    
    return response

# 라우터 등록 
from app.api.endpoints import auth, users, cases, lawyers, documents, laws, precedents

# API 버전 경로 설정
api_v1_prefix = settings.API_V1_STR

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=f"{api_v1_prefix}/users", tags=["사용자"])
app.include_router(cases.router, prefix=f"{api_v1_prefix}/cases", tags=["법률 사례"])
app.include_router(lawyers.router, prefix=f"{api_v1_prefix}/lawyers", tags=["변호사"])
app.include_router(documents.router, prefix=f"{api_v1_prefix}/documents", tags=["문서"])
app.include_router(laws.router, prefix=f"{api_v1_prefix}/laws", tags=["법령"])
app.include_router(precedents.router, prefix=f"{api_v1_prefix}/precedents", tags=["판례"])

# 전역 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 서버 로그에 예외 정보 출력
    print("\n\n서버 오류 발생:", str(exc))
    print("\n예외 정보:\n", traceback.format_exc())
    
    # 클라이언트에게 예외 정보 응답
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )

@app.get("/")
def root():
    return {"message": "Welcome to LawMate API", "status": "running", "version": "0.1.0"}

@app.get("/api/v1/test")
def test_api():
    return {"message": "API v1 is working", "endpoints": ["/api/v1/auth/register", "/api/v1/auth/token"]}
