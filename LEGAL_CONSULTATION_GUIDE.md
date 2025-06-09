# LawMate - 법률 상담 및 법령/판례 검색 기능 구현 가이드

## 1. 기능 개요

이 기능은 사용자가 입력한 법률 상담 내용을 바탕으로 다음 프로세스를 수행합니다:

1. **키워드 추출**: Claude API를 활용하여 법률 문제에서 키워드를 추출합니다.
2. **법령 검색**: 추출된 키워드로 국가법령정보 API를 통해 관련 법령을 검색합니다.
3. **판례 검색**: 추출된 키워드로 판례 API를 통해 관련 판례를 검색합니다.
4. **상위 3개 법령/판례 본문 조회**: 검색된 법령과 판례 중 상위 3개의 본문을 조회합니다.
5. **DB 저장**: 조회한 법령과 판례 정보를 데이터베이스에 저장합니다.
6. **법률 상담 답변 생성**: 조회된 법령과 판례 정보를 바탕으로 Claude API를 통해 법률 상담 답변을 생성합니다.

## 2. 구현 내용

### 2.1 데이터베이스 모델 변경

1. **Law 테이블**: 법령 정보 저장
   - law_id, law_code, law_name, law_type, promulgation_date, link 등

2. **Law_Article 테이블**: 법령 조문 저장
   - article_id, law_id, article_number, article_title, content 등

3. **Precedent 테이블**: 판례 정보 저장
   - precedent_id, case_number, case_name, court, decision_date, summary, judgment_text 등

4. **aCase_Law 테이블**: 사례와 법령 연결
   - id, aCase_id, law_id, article_id, relevance_score 등

5. **aCase_Precedent 테이블**: 사례와 판례 연결
   - id, aCase_id, precedent_id, relevance_score 등

### 2.2 서비스 구현

1. **LegalConsultationService**: 법률 상담 서비스
   - 키워드 추출, 법령/판례 검색, 저장, 답변 생성 등의 기능 포함

2. **LawDataService**: 법령 및 판례 데이터 서비스
   - 국가법령정보 API 및 판례 API 호출 기능 개선

3. **ClaudeService**: Claude API 서비스
   - 법률 문제 분석 및 답변 생성 기능 개선

### 2.3 API 엔드포인트 개선

1. **POST /api/cases/**: 법률 사례 생성 및 분석
   - 사례 생성 시 자동으로 법령/판례 검색 및 저장

2. **GET /api/cases/{case_id}**: 사례 상세 조회
   - 관련 법령 및 판례 정보 포함하여 반환

3. **POST /api/cases/{case_id}/analyze**: 사례 분석
   - 법률 상담 서비스를 통한 추가 분석 수행

## 3. 데이터베이스 마이그레이션

데이터베이스 변경을 적용하기 위해 마이그레이션 스크립트를 제공합니다:

1. **add_law_and_precedent_tables.sql**: 
   - Law, Law_Article, Precedent, aCase_Law, aCase_Precedent 테이블 생성/변경

2. 마이그레이션 실행 방법:
   - Windows: `run_law_migration.bat` 실행
   - Linux/Mac: `run_law_migration.sh` 실행

## 4. 사용 방법

### 4.1 법률 상담 입력 및 분석

1. 사용자가 법률 상담 내용 입력
2. 시스템이 자동으로 키워드 추출 및 법령/판례 검색
3. 검색된 법령/판례 정보를 바탕으로 답변 생성
4. 생성된 답변과 관련 법령/판례 정보 제공

### 4.2 사례 분석 요청

이미 생성된 사례에 대해 추가 분석이 필요한 경우:

```
POST /api/cases/{case_id}/analyze
```

를 호출하여 법률 상담 서비스를 통한 추가 분석을 수행할 수 있습니다.

## 5. 추가 개선 사항

1. **법령/판례 캐싱**: 자주 사용되는 법령과 판례 정보를 캐싱하여 API 호출 최소화
2. **관련성 점수 개선**: 키워드와 법령/판례 간의 관련성 계산 알고리즘 개선
3. **UI 개선**: 법령 및 판례 정보를 보기 좋게 표시하는 UI 구현
4. **검색 최적화**: 검색 키워드 최적화 및 검색 결과 필터링 기능 추가
5. **오류 처리 강화**: API 호출 실패 시 재시도 및 대체 방안 구현

## 6. API 문서 참고

1. **국가법령정보 API**: 기관코드(OC)는 로그인 이메일의 ID값(jhb1107) 사용
2. **판례 API**: 해당 API 문서 참고하여 실제 API 연동 구현 필요
