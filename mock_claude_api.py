import asyncio
import json
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 모의 응답 데이터
MOCK_RESPONSE = {
    "legal_category": "부동산/임대차",
    "key_issues": [
        "전세금 인상 요구 거절 권리",
        "계약 갱신 요구권",
        "전세금 인상률 제한",
        "임대인의 계약 해지 가능 여부"
    ],
    "keywords": [
        "주택임대차보호법",
        "전세계약",
        "계약갱신요구권",
        "전세금 인상",
        "계약 종료",
        "세입자 권리"
    ],
    "relevant_laws": [
        "주택임대차보호법",
        "민법",
        "주택임대차보호법 시행령"
    ],
    "initial_advice": "현재 주택임대차보호법상 세입자는 계약갱신요구권이 있으며, 임대인은 특별한 사유 없이 이를 거절할 수 없습니다. 또한 전세금 인상은 5% 이내로 제한됩니다."
}

async def mock_claude_api():
    """Claude API 호출을 모의(Mock)하는 함수"""
    
    print("===== Claude API 모의 테스트 시작 =====")
    print("참고: 이 테스트는 실제 API를 호출하지 않고 모의 응답을 생성합니다.")
    
    print("\n=== 모의 응답 내용 ===")
    print(json.dumps(MOCK_RESPONSE, indent=2, ensure_ascii=False))
    
    print("\n=== 모의 테스트 완료 ===")
    return MOCK_RESPONSE

if __name__ == "__main__":
    print("LawMate Claude API 모의 테스트")
    result = asyncio.run(mock_claude_api())
    
    print("\n===== 테스트 결과 요약 =====")
    if "legal_category" in result:
        print(f"법률 분야: {result['legal_category']}")
    if "key_issues" in result:
        print(f"핵심 쟁점 수: {len(result['key_issues'])}")
    if "keywords" in result:
        print(f"키워드 수: {len(result['keywords'])}")
    if "relevant_laws" in result:
        print(f"관련 법률 수: {len(result['relevant_laws'])}")
    
    print("\n주의: 이것은 실제 API 응답이 아닌 모의 데이터입니다.")
    print("실제 Claude API를 테스트하려면 유효한 API 키를 설정하고 test_claude_api.py를 실행하세요.")
