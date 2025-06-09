import httpx
import asyncio
import json
from app.services.law_data_service import LawDataService

async def test_precedent_service():
    """
    판례 데이터 서비스 테스트
    """
    service = LawDataService()
    
    print("=== 판례 검색 테스트 ===")
    # 담보권 관련 판례 검색
    precedents = await service.search_precedents(keywords=["담보권"])
    print(f"검색된 판례 수: {len(precedents)}")
    for precedent in precedents[:3]:  # 처음 3개만 출력
        print(f"사건명: {precedent.get('caseName')}")
        print(f"사건번호: {precedent.get('caseNumber')}")
        print(f"법원: {precedent.get('court')}")
        print(f"선고일자: {precedent.get('decisionDate')}")
        print("---")
    
    if precedents:
        first_precedent_id = precedents[0].get('precedentId')
        print(f"\n=== 판례 상세 조회 테스트 (ID: {first_precedent_id}) ===")
        precedent_detail = await service.get_precedent_detail(first_precedent_id)
        print(f"사건명: {precedent_detail.get('사건명')}")
        print(f"사건번호: {precedent_detail.get('사건번호')}")
        print(f"법원명: {precedent_detail.get('법원명')}")
        
        # 판결요지 일부 출력
        judgment_summary = precedent_detail.get('판결요지', '')
        if judgment_summary:
            print(f"\n판결요지: {judgment_summary[:200]}...")  # 처음 200자만 출력
        
        # 참조조문 출력
        reference_articles = precedent_detail.get('참조조문', '')
        if reference_articles:
            print(f"\n참조조문: {reference_articles}")
    
    print("\n=== 대법원 판례 검색 테스트 ===")
    supreme_court_precedents = await service.search_precedents(keywords=["손해배상"], court="대법원")
    print(f"검색된 대법원 판례 수: {len(supreme_court_precedents)}")
    for precedent in supreme_court_precedents[:2]:  # 처음 2개만 출력
        print(f"사건명: {precedent.get('caseName')}")
        print(f"사건번호: {precedent.get('caseNumber')}")
        print("---")
    
    print("\n=== 사건번호로 판례 검색 테스트 ===")
    # 특정 사건번호로 검색 (실제 사건번호로 변경 필요)
    case_number_precedents = await service.search_precedents(case_number="2009느합133")
    print(f"사건번호로 검색된 판례 수: {len(case_number_precedents)}")
    for precedent in case_number_precedents:
        print(f"사건명: {precedent.get('caseName')}")
        print(f"사건번호: {precedent.get('caseNumber')}")
        print(f"법원: {precedent.get('court')}")
        print("---")
    
    print("\n모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_precedent_service())