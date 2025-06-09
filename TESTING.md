# LawMate Claude API 테스트 가이드

이 문서는 LawMate 프로젝트의 Claude API 연동을 테스트하기 위한 방법을 설명합니다.

## 1. 환경 설정

테스트를 실행하기 전에 다음 환경 변수가 `.env` 파일에 설정되어 있는지 확인하세요:

```
CLAUDE_API_KEY=your_api_key_here
TEST_USER_EMAIL=test@example.com
TEST_USER_PASSWORD=testpassword
```

## 2. 단독 Claude API 테스트

Claude API가 제대로 작동하는지 직접 테스트합니다.

```bash
python test_claude_api.py
```

이 스크립트는 Claude API를 직접 호출하여 법률 문제 분석 요청을 보내고 응답을 확인합니다.

## 3. LawMate API 통합 테스트

LawMate 서버 API를 통해 Claude API 연동이 제대로 작동하는지 테스트합니다.

```bash
python test_lawmate_api.py
```

이 스크립트는 다음 과정을 테스트합니다:
1. 사용자 로그인
2. 법률 사례 생성 (Claude API 분석 포함)
3. 생성된 사례 조회
4. 추가 법률 분석 요청

## 4. CLI 도구를 사용한 테스트

다양한 법률 관련 작업을 명령줄에서 테스트할 수 있는 도구입니다.

### 법률 문제 분석

```bash
python lawmate_cli.py analyze "아파트 전세 계약을 했는데, 계약 종료 3개월 전에 집주인이 갑자기 전세금을 2천만원 올려달라고 합니다. 거절하자 다른 세입자를 구하겠다고 합니다."
```

### 법률 문서 초안 생성

```bash
python lawmate_cli.py document 내용증명 "2년 전에 빌려준 1000만원을 약속한 날짜에 갚지 않고 있습니다. 여러 차례 상환을 요청했으나 계속 미루고 있습니다."
```

### 법률 질문 답변

```bash
python lawmate_cli.py inquiry "상가 임대차 계약에서 묵시적 갱신이 이루어지면 계약 기간은 어떻게 되나요?"
```

## 5. 테스트 결과 확인

각 테스트 스크립트는 실행 결과를 콘솔에 출력합니다. 다음 사항을 확인하세요:

1. API 응답 상태 코드가 200인지 확인
2. Claude API가 예상대로 JSON 형식으로 응답하는지 확인
3. 응답 내용이 요청한 형식(법률 분야, 키워드, 관련 법령 등)을 포함하는지 확인
4. aCase 테이블에 claude_analysis 필드가 제대로 저장되는지 확인

## 6. 문제 해결

테스트 중 오류가 발생하는 경우:

1. `.env` 파일에 API 키가 올바르게 설정되어 있는지 확인
2. LawMate 서버가 실행 중인지 확인
3. 네트워크 연결 상태 확인
4. Claude API 할당량(rate limit) 초과 여부 확인
5. 응답 시간이 길어질 경우 타임아웃 설정 조정 (60초 → 120초)

## 7. 데이터베이스 확인

테스트 후 데이터베이스에 데이터가 제대로 저장되었는지 확인:

```sql
SELECT aCase_id, title, claude_analysis, legal_category, keywords 
FROM aCase 
ORDER BY created_at DESC 
LIMIT 5;
```

이 쿼리를 실행하여 최근 생성된 사례의 Claude API 분석 결과가 제대로 저장되었는지 확인할 수 있습니다.
