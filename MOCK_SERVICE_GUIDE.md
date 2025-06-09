"""
LawMate 애플리케이션에서 실제 Claude API 서비스 대신 모의 서비스를 사용하는 방법

1. app/api/endpoints/cases.py 파일에서 다음과 같이 수정하세요:

```python
# 기존 import문
from app.services.claude_service import ClaudeService

# 아래와 같이 변경
# from app.services.claude_service import ClaudeService
from app.services.mock_claude_service import MockClaudeService as ClaudeService
```

2. 이렇게 하면 코드 변경 없이 모의 서비스를 사용할 수 있습니다.

3. 실제 서비스로 다시 전환하려면 위 변경을 원래대로 되돌리세요.

주의: 모의 서비스는 테스트용으로만 사용하세요. 실제 프로덕션 환경에서는 실제 Claude API를 사용하는 것이 좋습니다.
"""