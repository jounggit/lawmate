import asyncio
import json
from app.services.law_data_service import LawDataService
from app.services.claude_service import ClaudeService

async def test_lawmate_with_claude():
    """
    LawMate API와 Claude API 통합 테스트
    - 법령 및 판례 검색
    - 검색 결과를 바탕으로 Claude API 활용 답변 생성
    """
    print("\n=== LawMate + Claude 통합 테스트 ===\n")
    law_service = LawDataService()
    claude_service = ClaudeService()
    
    # 테스트 사례: 임대차 계약 문제
    test_case = """
    저는 월세 50만원, 보증금 1000만원으로 2년 계약한 세입자입니다. 
    계약기간이 아직 6개월 남았는데 집주인이 갑자기 다음 달까지 나가라고 합니다. 
    이사비용도 주지 않겠다고 하는데 제가 어떻게 대응해야 할까요?
    """
    
    print("테스트 사례:")
    print(test_case)
    print("\n1. Claude API로 법률 문제 분석 중...\n")
    
    # 1. Claude API로 법률 문제 분석
    analysis = await claude_service.analyze_legal_issue(test_case)
    
    print("법률 문제 분석 결과:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # 2. 분석 결과에서 키워드 추출
    keywords = analysis.get("keywords", [])
    relevant_laws = analysis.get("relevant_laws", [])
    
    # 키워드 수 제한 (3개 이하로)
    if len(keywords) > 3:
        keywords = keywords[:3]
    
    print(f"\n2. 추출된 키워드: {', '.join(keywords)}")
    print(f"   추천 법령: {', '.join(relevant_laws)}")
    
    # 3. 법령 검색
    print("\n3. 키워드로 법령 검색 중...")
    laws = await law_service.search_laws(keywords)  # 최대 3개 키워드만 사용
    
    print(f"   검색된 법령: {len(laws)}개")
    for i, law in enumerate(laws[:3], 1):
        print(f"   {i}. {law.get('lawName')} (ID: {law.get('lawId')})")
    
    # 4. 첫 번째 법령의 조문 검색
    formatted_articles = []
    if laws:
        first_law_id = laws[0].get('lawId')
        print(f"\n4. 첫 번째 법령의 조문 검색 중... (ID: {first_law_id})")
        
        law_articles = await law_service.search_law_articles(first_law_id)
        print(f"   검색된 조문: {len(law_articles)}개")
        
        # 조문 정보 구성 (최대 3개)
        for article in law_articles[:3]:
            formatted_article = {
                "lawName": article.get("lawName", ""),
                "article": article.get("article", ""),
                "content": article.get("content", "")
            }
            formatted_articles.append(formatted_article)
            print(f"   제{article.get('article')}조 {article.get('articleTitle', '')}")
    else:
        # 기본 예시 데이터 사용
        formatted_articles = [
            {
                "lawName": "주택임대차보호법",
                "article": "6조",
                "content": "임대인은 임대차기간이 끝나기 전에 정당한 사유 없이 임차인의 주거를 방해하거나 퇴거를 요구할 수 없다."
            }
        ]
    
    # 5. 판례 검색
    print("\n5. 키워드로 판례 검색 중...")
    precedents = await law_service.search_precedents(keywords=keywords[:2])  # 최대 2개 키워드만 사용
    
    print(f"   검색된 판례: {len(precedents)}개")
    for i, precedent in enumerate(precedents[:3], 1):
        print(f"   {i}. {precedent.get('caseName')} ({precedent.get('caseNumber')})")
    
    # 판례 정보 구성 (최대 3개)
    formatted_precedents = []
    for precedent in precedents[:3]:
        formatted_precedent = {
            "caseNo": precedent.get("caseNumber", ""),
            "court": precedent.get("court", ""),
            "decisionDate": precedent.get("decisionDate", ""),
            "summary": "임대인이 계약기간 중 임차인에게 퇴거를 요구한 사례에서, 정당한 사유 없는 퇴거 요구는 불법이며 이로 인한 손해배상 책임이 있다고 판결했습니다."
        }
        formatted_precedents.append(formatted_precedent)
    
    if not formatted_precedents:
        # 기본 예시 데이터 사용
        formatted_precedents = [
            {
                "caseNo": "대법원 2019다12345",
                "court": "대법원",
                "decisionDate": "2019-05-30",
                "summary": "임대인이 계약기간 중 임차인에게 퇴거를 요구한 사례에서, 정당한 사유 없는 퇴거 요구는 불법이며 이로 인한 손해배상 책임이 있다고 판결했습니다."
            }
        ]
    
    # 6. 새로운 상세 법률 상담 답변 생성
    print("\n6. Claude API로 상세 법률 상담 답변 생성 중...\n")
    
    consultation_response = await claude_service.generate_legal_consultation(
        test_case, formatted_articles, formatted_precedents
    )
    
    print("법률 상담 답변:")
    print("-" * 80)
    print(consultation_response)
    print("-" * 80)
    
    # 7. 내용증명 문서 초안 생성
    print("\n7. 내용증명 문서 초안 생성 중...\n")
    
    case_info = {
        "title": "임대차 계약 해지 거부 관련 내용증명",
        "description": test_case,
        "legal_category": analysis.get("legal_category", "부동산/임대차")
    }
    
    recipient_info = {
        "name": "홍길동",
        "address": "서울시 강남구 테헤란로 123",
        "contact": "010-1234-5678"
    }
    
    document_draft = await claude_service.generate_document_draft("내용증명", case_info, recipient_info)
    
    print("내용증명 문서 초안:")
    print("-" * 80)
    print(document_draft)
    print("-" * 80)
    
    print("\n통합 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_lawmate_with_claude())
