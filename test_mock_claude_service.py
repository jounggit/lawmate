import asyncio
from app.services.mock_claude_service import MockClaudeService

async def test_mock_claude_service():
    """MockClaudeService 테스트 함수"""
    service = MockClaudeService()
    
    print("\n===== 법률 문제 분석 테스트 =====")
    test_description = "아파트 전세 계약을 했는데, 계약 종료 3개월 전에 집주인이 갑자기 전세금을 2천만원 올려달라고 합니다. 거절하자 다른 세입자를 구하겠다고 합니다."
    
    print(f"테스트 설명: {test_description[:50]}...")
    analysis_result = await service.analyze_legal_issue(test_description)
    print("\n분석 결과:")
    for key, value in analysis_result.items():
        if isinstance(value, list):
            print(f"{key}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"{key}: {value}")
    
    print("\n===== 법령/판례 요약 테스트 =====")
    # 테스트용 가상 데이터
    test_laws = [
        {"lawName": "주택임대차보호법", "article": "제6조의3", "content": "임차인은 계약기간이 끝나기 전 2개월부터 1개월까지 임대인에게 계약갱신을 요구할 수 있다."},
        {"lawName": "민법", "article": "제618조", "content": "임대차는 당사자 일방이 상대방에게 목적물을 사용, 수익하게 할 것을 약정하고 상대방이 이에 대하여 차임을 지급할 것을 약정함으로써 그 효력이 생긴다."}
    ]
    test_cases = [
        {"caseNo": "대법원 2019다12345", "summary": "임대인이 계약 갱신을 거절하기 위해서는 정당한 사유가 있어야 한다는 원칙을 확인한 사례."}
    ]
    
    summary_result = await service.summarize_legal_info(test_laws, test_cases)
    print("\n요약 결과:")
    for key, value in summary_result.items():
        print(f"\n{key}:")
        if isinstance(value, list):
            if isinstance(value[0], dict):
                for item in value:
                    for k, v in item.items():
                        print(f"  - {k}: {v}")
                    print()
            else:
                for item in value:
                    print(f"  - {item}")
        else:
            print(f"  {value}")
    
    print("\n===== 문서 초안 생성 테스트 =====")
    test_case_info = {
        "title": "전세 계약 갱신 거부 건",
        "description": "아파트 전세 계약을 했는데, 계약 종료 3개월 전에 집주인이 갑자기 전세금을 2천만원 올려달라고 합니다.",
        "legal_category": "부동산/임대차"
    }
    test_recipient_info = {
        "name": "홍길동",
        "address": "서울시 강남구 테헤란로 123",
        "contact": "010-1234-5678"
    }
    
    doc_result = await service.generate_document_draft("내용증명", test_case_info, test_recipient_info)
    print("\n문서 초안:")
    print(doc_result)
    
    print("\n===== 테스트 완료 =====")
    print("모든 테스트가 성공적으로 완료되었습니다.")

if __name__ == "__main__":
    print("===== MockClaudeService 테스트 시작 =====")
    print("이 테스트는 실제 API를 호출하지 않고 모의 서비스를 사용합니다.")
    asyncio.run(test_mock_claude_service())
