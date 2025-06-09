import asyncio
import json
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# .env 파일에서 환경 변수 로드
load_dotenv()

# 테스트를 위한 임시 데이터베이스 세션 설정
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 서비스 및 모델 임포트
from app.services.legal_consultation_service import LegalConsultationService
from app.db.models import ACase, Law, LawArticle, Precedent, ACaseLaw, ACasePrecedent

async def test_legal_consultation():
    """법률 상담 기능 테스트"""
    print("\n===== 법률 상담 기능 테스트 =====")
    
    # 테스트용 법률 상담 내용
    test_description = """
    아파트 전세 계약을 했는데, 계약 종료 3개월 전에 집주인이 갑자기 전세금을 2천만원 올려달라고 합니다.
    거절하자 다른 세입자를 구하겠다고 합니다. 전세금 인상 요구를 거절할 권리가 있나요?
    """
    
    # 법률 상담 서비스 인스턴스 생성
    service = LegalConsultationService()
    
    # 데이터베이스 세션 생성
    db = SessionLocal()
    
    try:
        # 테스트용 사례 생성 (실제 DB에 저장하지 않음)
        print("\n1. 키워드 추출 테스트")
        keywords, legal_category = await service._extract_keywords(test_description)
        
        print(f"추출된 키워드: {keywords}")
        print(f"법률 분야: {legal_category}")
        
        if not keywords:
            print("키워드 추출 실패!")
            return
        
        # 법령 검색 테스트
        print("\n2. 법령 검색 테스트")
        law_list = await service.law_data_service.search_laws(keywords)
        
        if law_list:
            print(f"검색된 법령: {len(law_list)}개")
            for i, law in enumerate(law_list[:3], 1):
                print(f"[법령 {i}] {law.get('lawName', 'N/A')} ({law.get('lawId', 'N/A')})")
                
            # 첫 번째 법령의 조문 검색 테스트
            if law_list and 'lawId' in law_list[0]:
                print("\n3. 법령 조문 검색 테스트")
                first_law_id = law_list[0]['lawId']
                articles = await service.law_data_service.search_law_articles(first_law_id)
                
                if articles:
                    print(f"검색된 조문: {len(articles)}개")
                    for i, article in enumerate(articles[:3], 1):
                        print(f"[조문 {i}] {article.get('articleTitle', 'N/A')} - {article.get('article', 'N/A')}")
                else:
                    print("조문 검색 결과 없음")
        else:
            print("법령 검색 결과 없음")
        
        # 판례 검색 테스트
        print("\n4. 판례 검색 테스트")
        precedent_list = await service.law_data_service.search_cases(keywords)
        
        if precedent_list:
            print(f"검색된 판례: {len(precedent_list)}개")
            for i, precedent in enumerate(precedent_list[:3], 1):
                print(f"[판례 {i}] {precedent.get('caseNo', 'N/A')}")
        else:
            print("판례 검색 결과 없음")
        
        # 법률 상담 답변 생성 테스트
        print("\n5. 법률 상담 답변 생성 테스트")
        
        # 임시 법령 및 판례 데이터 생성
        mock_law_articles = []
        if law_list and articles:
            for article in articles[:3]:
                mock_article = LawArticle(
                    article_id=1,
                    law_id=1,
                    article_number=article.get('article', 'N/A'),
                    article_title=article.get('articleTitle', 'N/A'),
                    content=article.get('content', 'N/A')
                )
                mock_law_articles.append(mock_article)
        
        mock_precedents = []
        if precedent_list:
            for precedent in precedent_list[:3]:
                mock_precedent = Precedent(
                    precedent_id=1,
                    case_number=precedent.get('caseNo', 'N/A'),
                    case_name=precedent.get('caseName', 'N/A'),
                    court=precedent.get('court', 'N/A'),
                    decision_date=precedent.get('decisionDate', 'N/A'),
                    summary=precedent.get('summary', 'N/A')
                )
                mock_precedents.append(mock_precedent)
        
        # 법률 상담 답변 생성
        consultation_response = await service._generate_consultation_response(
            test_description, keywords, legal_category, mock_law_articles, mock_precedents
        )
        
        print("\n법률 상담 답변:")
        print(consultation_response[:500] + "..." if len(consultation_response) > 500 else consultation_response)
        
        print("\n===== 테스트 완료 =====")
        
    finally:
        # 데이터베이스 세션 종료
        db.close()

if __name__ == "__main__":
    print("법률 상담 기능 테스트를 시작합니다...")
    asyncio.run(test_legal_consultation())
