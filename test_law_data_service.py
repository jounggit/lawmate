import httpx
import asyncio
import json
from app.services.law_data_service import LawDataService

async def test_law_data_service():
    """
    법령 데이터 서비스 테스트
    """
    service = LawDataService()
    
    print("=== 법령 검색 테스트 ===")
    # 임대차 관련 법령 검색
    laws = await service.search_laws(["임대차", "보증금"])
    print(f"검색된 법령 수: {len(laws)}")
    for law in laws[:3]:  # 처음 3개만 출력
        print(f"법령명: {law.get('lawName')}, ID: {law.get('lawId')}")
    
    if laws:
        first_law_id = laws[0].get('lawId')
        print(f"\n=== 법령 상세 조회 테스트 (ID: {first_law_id}) ===")
        law_detail = await service.get_law_detail(first_law_id)
        print(f"법령명: {law_detail.get('법령명_한글')}")
        print(f"공포일자: {law_detail.get('공포일자')}")
        print(f"소관부처: {law_detail.get('소관부처')}")
        
        # 조문 출력 (처음 2개만)
        print("\n조문 정보:")
        for article in law_detail.get('조문', [])[:2]:
            print(f"제{article.get('조문번호')}조 {article.get('조문제목')}")
            print(f"내용: {article.get('조문내용')[:100]}...")  # 처음 100자만 출력
        
        print("\n=== 법령 조문 검색 테스트 ===")
        articles = await service.search_law_articles(first_law_id)
        print(f"검색된 조문 수: {len(articles)}")
        for article in articles[:3]:  # 처음 3개만 출력
            print(f"조문: 제{article.get('article')}조 {article.get('articleTitle')}")
    
    print("\n모든 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_law_data_service())