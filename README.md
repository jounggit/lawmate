# LawMate (법친구)

법률 정보 제공 및 AI 기반 법률 문서 생성 서비스의 백엔드 API

## 프로젝트 소개

LawMate(법친구)는 Claude AI를 활용하여 사용자의 법률 문제에 대한 분석, 관련 법령 및 판례 제공, 기본적인 법률 문서 초안 생성을 지원하는 서비스입니다.

## 주요 기능

- 사용자 법률 문제 분석 및 관련 법령/판례 제공
- 법률 정보의 쉬운 해석 및 요약
- 상황별 대응 방안 제시 및 문서 초안 작성
- 전문 변호사 매칭 및 상담 연결
- 사용자 간의 경험 공유를 위한 커뮤니티 기능

## 주요 업데이트 내역

### 2025.06.09 업데이트
- aCase 테이블에 Claude API 상담 내용 저장 기능 추가
  - 사용자 법률 상담 내용이 aCase 테이블에 저장됩니다.
  - Claude API로 분석한 결과도 함께 저장됩니다.
  - 새로운 필드: claude_analysis, legal_category, keywords
- DB 마이그레이션 스크립트 추가
  - 기존 데이터베이스 구조를 업데이트하기 위한 마이그레이션 스크립트 추가

## 기술 스택

- 백엔드: Python, FastAPI
- 데이터베이스: MySQL, AWS RDS
- AI 엔진: Anthropic Claude API

## 설치 및 실행 방법

1. 환경 설정

```bash
# 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 필요한 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# .env 파일 내용 수정 (API 키, 데이터베이스 URL 등)
```

2. 데이터베이스 설정

```bash
# MySQL 데이터베이스 생성
# 예시: CREATE DATABASE lawmate CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 데이터베이스 테이블 생성
# 애플리케이션 실행 시 자동으로 생성됩니다.

# 마이그레이션 실행 (DB 스키마 업데이트)
python app/db/run_migration.py
```

3. 애플리케이션 실행

```bash
# 개발 모드로 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. API 문서 접근

애플리케이션이 실행된 후, 아래 URL에서 API 문서에 접근할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
lawmate/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 앱 인스턴스 및 기본 설정
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # 환경 변수 및 설정
│   │   ├── security.py         # JWT 토큰 및 인증 관련
│   │   └── errors.py           # 에러 핸들링
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # 데이터베이스 연결 설정
│   │   ├── models.py           # SQLAlchemy 모델
│   │   ├── migrations/         # DB 마이그레이션 스크립트
│   │   └── run_migration.py    # 마이그레이션 실행 스크립트
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # 의존성 주입
│   │   └── endpoints/
│   │       ├── __init__.py
│   │       ├── auth.py         # 인증 관련 엔드포인트
│   │       ├── users.py        # 사용자 관리 
│   │       ├── cases.py        # 법률 사례 관리
│   │       ├── lawyers.py      # 변호사 정보 및 매칭
│   │       └── documents.py    # 문서 생성 및 관리
│   ├── services/
│   │   ├── __init__.py
│   │   ├── claude_service.py   # Claude API 연동
│   │   ├── law_data_service.py # 법령/판례 데이터 처리
│   │   └── document_service.py # 문서 생성 서비스
│   └── schemas/
│       ├── __init__.py
│       ├── user.py             # 사용자 관련 스키마
│       ├── case.py             # 법률 사례 스키마
│       ├── lawyer.py           # 변호사 정보 스키마
│       └── document.py         # 문서 관련 스키마
├── .env.example                # 환경 변수 예시
└── requirements.txt            # 의존성 패키지
```

## aCase 테이블 구조 (업데이트됨)

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| aCase_id | Integer | 기본 키 (자동 증가) |
| user_id | Integer | 사용자 ID (외래 키) |
| aCase_type | String(50) | 사례 유형 |
| title | String(200) | 사례 제목 (추가됨) |
| description | Text | 사례 설명 |
| status | String(30) | 사례 상태 (기본값: "진행중") |
| created_at | DateTime | 생성 일시 |
| claude_analysis | Text | Claude API 분석 결과 (JSON 형식) (추가됨) |
| legal_category | String(100) | 법률 분야 (추가됨) |
| keywords | String(500) | 키워드 목록 (쉼표로 구분) (추가됨) |

## 라이센스

이 프로젝트는 MIT 라이센스를 따릅니다.