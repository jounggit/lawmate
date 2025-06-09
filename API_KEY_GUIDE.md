# Claude API 키 설정 가이드

## 문제 상황
Claude API 테스트 시 다음과 같은 인증 오류가 발생했습니다:
```
Claude API 호출 중...
=== API 호출 실패 ===
상태 코드: 401
응답: {"type":"error","error":{"type":"authentication_error","message":"invalid x-api-key"}}
```

## 해결 방법

### 1. 유효한 Claude API 키 획득하기
1. Anthropic 콘솔(https://console.anthropic.com/)에 로그인하세요.
2. 계정이 없다면 가입 후 결제 정보를 등록하세요.
3. API 키 섹션에서 새 API 키를 생성하세요.
4. 생성된 API 키를 안전하게 복사하세요. (키는 한 번만 표시됩니다!)

### 2. .env 파일에 API 키 설정하기
`.env` 파일을 열고 다음 줄을 찾으세요:
```
CLAUDE_API_KEY=your-claude-api-key
```

이를 실제 API 키로 변경하세요:
```
CLAUDE_API_KEY=sk-ant-YOUR-ACTUAL-API-KEY
```

### 3. API 키 형식 확인
Claude API 키는 일반적으로 `sk-ant-`로 시작합니다. 올바른 형식의 API 키를 사용하고 있는지 확인하세요.

### 4. 변경 후 테스트 다시 실행
API 키를 설정한 후 테스트를 다시 실행하세요:
```
python test_claude_api.py
```

## 추가 문제 해결
- API 키가 유효해도 문제가 지속된다면 Anthropic의 서비스 상태를 확인하세요: https://status.anthropic.com/
- 계정의 API 사용 한도를 확인하고 필요하다면 증가 요청을 검토하세요.
- 네트워크 연결이 안정적인지 확인하세요.
- 프록시나 방화벽 설정이 API 호출을 차단하지 않는지 확인하세요.

## 보안 주의사항
- API 키는 비밀번호와 같은 중요한 보안 정보입니다. 코드에 직접 입력하거나 버전 관리 시스템에 커밋하지 마세요.
- `.env` 파일은 항상 `.gitignore`에 포함시켜 실수로 공개되지 않도록 하세요.
- 의심스러운 활동이 감지되면 즉시 API 키를 교체하세요.
