from typing import List, Dict, Any, Optional, Tuple
import json
from sqlalchemy.orm import Session

from app.db.models import ACase, Law, LawArticle, Precedent, ACaseLaw, ACasePrecedent
from app.services.claude_service import ClaudeService
from app.services.law_data_service import LawDataService

class LegalConsultationService:
    """법률 상담 서비스 클래스"""
    
    def __init__(self, use_mock_data: bool = False):
        self.claude_service = ClaudeService()
        self.law_data_service = LawDataService()
        # mock 데이터 사용 여부
        self.use_mock_data = use_mock_data
    
    async def process_consultation(self, db: Session, case_id: int, description: str) -> Dict[str, Any]:
        """
        법률 상담 처리 메인 함수
        1. 키워드 추출 (Claude API)
        2. 법령 검색 (국가법령정보 API)
        3. 판례 검색 (판례 API)
        4. 법령/판례 DB 저장
        5. 법률 상담 답변 생성 (Claude API)
        """
        # 1. 키워드 추출
        keywords, legal_category = await self._extract_keywords(description)
        
        # 2. 법령 검색 및 저장
        laws, law_articles = await self._search_and_save_laws(db, case_id, keywords)
        
        # 3. 판례 검색 및 저장
        precedents = await self._search_and_save_precedents(db, case_id, keywords)
        
        # 4. 법률 상담 답변 생성 (새로운 상세 답변 함수 사용)
        consultation_response = await self._generate_detailed_consultation(
            description, law_articles, precedents
        )
        
        # 클로드 분석 결과 저장
        await self._save_claude_analysis(db, case_id, description, keywords, legal_category, consultation_response)
        
        # 5. 결과 반환
        return {
            "consultation_response": consultation_response,
            "keywords": keywords,
            "legal_category": legal_category,
            "laws": [{"law_name": law.law_name, "law_id": law.law_id} for law in laws],
            "precedents": [{"case_number": p.case_number, "precedent_id": p.precedent_id} for p in precedents]
        }
    
    async def _extract_keywords(self, description: str) -> Tuple[List[str], str]:
        """
        Claude API를 사용하여 법률 상담 내용에서 키워드 추출
        """
        # Claude API 호출
        analysis = await self.claude_service.analyze_legal_issue(description)
        
        # 키워드 및 법률 분야 추출
        keywords = []
        legal_category = ""
        
        if isinstance(analysis, dict):
            keywords = analysis.get("keywords", [])
            legal_category = analysis.get("legal_category", "")
        
        return keywords, legal_category
    
    async def _search_and_save_laws(self, db: Session, case_id: int, keywords: List[str]) -> Tuple[List[Law], List[LawArticle]]:
        """
        키워드로 법령 검색 및 DB 저장
        상위 3개 법령의 조문도 검색하여 저장
        """
        # 사용자 지정 예시 데이터 사용 여부 확인
        if self.use_mock_data:
            print("예시 데이터 사용 모드: 법령 예시 데이터 사용")
            law_list = self.law_data_service._get_mock_laws()
        else:
            # 키워드로 법령 목록 검색
            law_list = await self.law_data_service.search_laws(keywords)
        
        # 검색된 법령이 없는 경우
        if not law_list:
            return [], []
        
        saved_laws = []
        all_law_articles = []
        
        # 상위 3개 법령만 처리
        for law_info in law_list[:3]:
            # 법령 DB에 저장 (이미 있으면 기존 것 사용)
            law = self._save_law(db, law_info)
            saved_laws.append(law)
            
            # 법령 조문 검색
            if law and 'lawId' in law_info:
                # 예시 데이터 사용 여부 확인
                if self.use_mock_data:
                    print(f"예시 데이터 사용 모드: {law.law_name} 조문 예시 데이터 사용")
                    articles = self.law_data_service._get_mock_law_articles()
                else:
                    articles = await self.law_data_service.search_law_articles(law_info['lawId'])
                
                # 조문 DB에 저장
                law_articles = self._save_law_articles(db, law.law_id, articles)
                all_law_articles.extend(law_articles)
                
                # 사례-법령 연결 저장
                for article in law_articles:
                    self._save_case_law_relation(db, case_id, law.law_id, article.article_id)
        
        return saved_laws, all_law_articles
    
    def _save_law(self, db: Session, law_info: Dict[str, Any]) -> Optional[Law]:
        """
        법령 정보를 DB에 저장 (중복 시 기존 데이터 반환)
        """
        # 이미 존재하는 법령인지 확인
        law_code = law_info.get('lawId', '')
        existing_law = db.query(Law).filter(Law.law_code == law_code).first()
        
        if existing_law:
            # 링크 정보가 없는 경우 업데이트
            if not existing_law.link and 'link' in law_info and law_info['link']:
                existing_law.link = law_info['link']
                db.commit()
            return existing_law
        
        # 링크 정보 처리 - 법령 상세 링크가 없으면 기본 URL 구성
        link = law_info.get('link', '')
        if not link and law_info.get('lawName', ''):
            # 기본 법령 상세 페이지 URL 형식 사용
            link = f"https://www.law.go.kr/법령/{law_info.get('lawName', '')}"
        
        # 새 법령 추가
        new_law = Law(
            law_code=law_code,
            law_name=law_info.get('lawName', ''),
            law_type=law_info.get('lawType', ''),
            promulgation_date=law_info.get('promulgationDate', ''),
            link=link
        )
        
        db.add(new_law)
        db.commit()
        db.refresh(new_law)
        
        return new_law
    
    def _save_law_articles(self, db: Session, law_id: int, articles: List[Dict[str, Any]]) -> List[LawArticle]:
        """
        법령 조문을 DB에 저장 (중복 조문은 제외)
        """
        saved_articles = []
        
        for article_info in articles:
            # 조문번호 확인
            article_number = article_info.get('article', '')
            if not article_number:
                continue
            
            # 이미 존재하는 조문인지 확인
            existing_article = db.query(LawArticle).filter(
                LawArticle.law_id == law_id,
                LawArticle.article_number == article_number
            ).first()
            
            if existing_article:
                saved_articles.append(existing_article)
                continue
            
            # 새 조문 추가
            new_article = LawArticle(
                law_id=law_id,
                article_number=article_number,
                article_title=article_info.get('articleTitle', ''),
                content=article_info.get('content', '')
            )
            
            db.add(new_article)
            db.commit()
            db.refresh(new_article)
            
            saved_articles.append(new_article)
        
        return saved_articles
    
    def _save_case_law_relation(self, db: Session, case_id: int, law_id: int, article_id: Optional[int] = None) -> None:
        """
        사례와 법령/조문 간의 연결 저장 (중복 시 무시)
        """
        # 이미 존재하는 연결인지 확인
        existing_relation = db.query(ACaseLaw).filter(
            ACaseLaw.aCase_id == case_id,
            ACaseLaw.law_id == law_id,
            ACaseLaw.article_id == article_id
        ).first()
        
        if existing_relation:
            return
        
        # 새 연결 추가
        new_relation = ACaseLaw(
            aCase_id=case_id,
            law_id=law_id,
            article_id=article_id,
            relevance_score=80  # 기본 관련성 점수
        )
        
        db.add(new_relation)
        db.commit()
    
    async def _search_and_save_precedents(self, db: Session, case_id: int, keywords: List[str]) -> List[Precedent]:
        """
        키워드로 판례 검색 및 DB 저장
        """
        # 사용자 지정 예시 데이터 사용 여부 확인
        if self.use_mock_data:
            print("예시 데이터 사용 모드: 판례 예시 데이터 사용")
            precedent_list = self.law_data_service._get_mock_precedents()
        else:
            # 키워드로 판례 목록 검색
            precedent_list = await self.law_data_service.search_cases(keywords)
        
        # 검색된 판례가 없는 경우
        if not precedent_list:
            return []
        
        saved_precedents = []
        
        # 상위 3개 판례만 처리
        for precedent_info in precedent_list[:3]:
            # 판례 DB에 저장 (이미 있으면 기존 것 사용)
            precedent = self._save_precedent(db, precedent_info)
            saved_precedents.append(precedent)
            
            # 사례-판례 연결 저장
            self._save_case_precedent_relation(db, case_id, precedent.precedent_id)
        
        return saved_precedents
    
    def _save_precedent(self, db: Session, precedent_info: Dict[str, Any]) -> Precedent:
        """
        판례 정보를 DB에 저장 (중복 시 기존 데이터 반환)
        """
        # 이미 존재하는 판례인지 확인
        case_number = precedent_info.get('caseNo', '') or precedent_info.get('caseNumber', '')
        existing_precedent = db.query(Precedent).filter(Precedent.case_number == case_number).first()
        
        if existing_precedent:
            # 링크 정보가 없는 경우 업데이트
            if not existing_precedent.link and 'link' in precedent_info and precedent_info['link']:
                existing_precedent.link = precedent_info['link']
                db.commit()
            return existing_precedent
        
        # 링크 정보 처리 - 판례 상세 링크가 없으면 기본 URL 구성
        link = precedent_info.get('link', '')
        if not link and case_number:
            # 기본 판례 상세 페이지 URL 형식 사용
            link = f"https://www.law.go.kr/판례/{case_number}"
        
        # 새 판례 추가
        new_precedent = Precedent(
            case_number=case_number,
            case_name=precedent_info.get('caseName', ''),
            court=precedent_info.get('court', ''),
            decision_date=precedent_info.get('decisionDate', ''),
            summary=precedent_info.get('summary', ''),
            judgment_text=precedent_info.get('judgmentText', ''),
            link=link
        )
        
        db.add(new_precedent)
        db.commit()
        db.refresh(new_precedent)
        
        return new_precedent
    
    def _save_case_precedent_relation(self, db: Session, case_id: int, precedent_id: int) -> None:
        """
        사례와 판례 간의 연결 저장 (중복 시 무시)
        """
        # 이미 존재하는 연결인지 확인
        existing_relation = db.query(ACasePrecedent).filter(
            ACasePrecedent.aCase_id == case_id,
            ACasePrecedent.precedent_id == precedent_id
        ).first()
        
        if existing_relation:
            return
        
        # 새 연결 추가
        new_relation = ACasePrecedent(
            aCase_id=case_id,
            precedent_id=precedent_id,
            relevance_score=80  # 기본 관련성 점수
        )
        
        db.add(new_relation)
        db.commit()
    
    async def _save_claude_analysis(self, db: Session, case_id: int, description: str, keywords: List[str], 
                                   legal_category: str, consultation_response: str) -> None:
        """
        Claude API의 분석 결과를 사례 DB에 저장
        """
        try:
            # 해당 사례 조회
            case = db.query(ACase).filter(ACase.aCase_id == case_id).first()
            if case:
                # Claude 분석 결과 저장
                case.claude_analysis = json.dumps({
                    "keywords": keywords,
                    "legal_category": legal_category,
                    "consultation_response": consultation_response
                }, ensure_ascii=False)
                
                db.commit()
        except Exception as e:
            print(f"Claude 분석 결과 저장 중 오류 발생: {e}")
    
    async def _generate_consultation_response(
        self, 
        description: str, 
        keywords: List[str], 
        legal_category: str, 
        law_articles: List[LawArticle], 
        precedents: List[Precedent]
    ) -> str:
        """
        Claude API를 사용하여 법률 상담 답변 생성 (기본 버전)
        """
        # 법령 및 판례 정보 정리
        laws_text = ""
        for i, article in enumerate(law_articles[:3], 1):  # 최대 3개 조문만 사용
            laws_text += f"[법령 {i}]\n"
            laws_text += f"법령명: {getattr(article, 'law_name', '')}\n"
            laws_text += f"조문번호: {article.article_number}\n"
            laws_text += f"조문제목: {article.article_title}\n"
            laws_text += f"조문내용: {article.content}\n\n"
        
        precedents_text = ""
        for i, precedent in enumerate(precedents[:3], 1):  # 최대 3개 판례만 사용
            precedents_text += f"[판례 {i}]\n"
            precedents_text += f"사건번호: {precedent.case_number}\n"
            precedents_text += f"법원: {precedent.court}\n"
            precedents_text += f"판결일자: {precedent.decision_date}\n"
            precedents_text += f"판결요지: {precedent.summary}\n\n"
        
        # 법령 정보가 없는 경우
        if not laws_text:
            laws_text = "관련 법령 정보가 없습니다."
        
        # 판례 정보가 없는 경우
        if not precedents_text:
            precedents_text = "관련 판례 정보가 없습니다."
        
        # 법률 상담 답변 생성을 위한 Claude API 호출
        consultation_prompt = f"""
        당신은 법률 전문가입니다. 다음 사용자의 법률 문제에 대해 관련 법령과 판례를 참고하여 답변해주세요.
        
        ## 사용자 문제:
        {description}
        
        ## 관련 법률 분야:
        {legal_category}
        
        ## 관련 키워드:
        {", ".join(keywords)}
        
        ## 관련 법령:
        {laws_text}
        
        ## 관련 판례:
        {precedents_text}
        
        다음 형식으로 법률 상담 답변을 작성해주세요:
        1. 문제 요약: 사용자의 법률 문제를 간단히 요약
        2. 적용 법령 및 판례: 어떤 법령과 판례가 적용되는지 설명
        3. 법률적 견해: 문제에 대한 법률적 견해 제시
        4. 권리와 의무: 사용자의 법적 권리와 의무 설명
        5. 대응 방안: 사용자가 취할 수 있는 법적 대응 방안 제안
        
        일반인도 이해할 수 있는 쉬운 언어로 설명해주세요.
        """
        
        # Claude API 호출
        response = await self.claude_service._call_claude_api(consultation_prompt)
        
        return response
    
    async def _generate_detailed_consultation(
        self, 
        user_description: str, 
        law_articles: List[LawArticle], 
        precedents: List[Precedent]
    ) -> str:
        """
        Claude API를 사용하여 구체적인 행동 계획이 포함된 상세 법률 상담 답변 생성
        """
        # API 요청을 위한 법령 및 판례 정보 변환
        formatted_laws = []
        for article in law_articles[:3]:  # 최대 3개 조문만 사용
            # 법령 링크 정보 획득
            law_link = ""
            if hasattr(article, 'law') and article.law and article.law.link:
                law_link = article.law.link
            else:
                # 기본 법령 상세 페이지 URL 형식 사용
                law_name = getattr(article, 'law_name', '')
                if law_name:
                    law_link = f"https://www.law.go.kr/법령/{law_name}"
            
            formatted_law = {
                "lawName": getattr(article, 'law_name', '주택임대차보호법' if not hasattr(article, 'law_name') else ''),
                "article": article.article_number,
                "content": article.content,
                "link": law_link
            }
            formatted_laws.append(formatted_law)
        
        formatted_precedents = []
        for precedent in precedents[:3]:  # 최대 3개 판례만 사용
            # 판례 링크 정보 획득
            precedent_link = precedent.link if hasattr(precedent, 'link') and precedent.link else f"https://www.law.go.kr/판례/{precedent.case_number}"
            
            formatted_precedent = {
                "caseNo": precedent.case_number,
                "court": precedent.court,
                "decisionDate": precedent.decision_date,
                "summary": precedent.summary,
                "link": precedent_link
            }
            formatted_precedents.append(formatted_precedent)
        
        # 법령 또는 판례가 없는 경우를 위한 기본 데이터
        if not formatted_laws:
            formatted_laws = [
                {
                    "lawName": "주택임대차보호법",
                    "article": "6조",
                    "content": "임대인은 임대차기간이 끝나기 전에 정당한 사유 없이 임차인의 주거를 방해하거나 퇴거를 요구할 수 없다."
                }
            ]
        
        if not formatted_precedents:
            formatted_precedents = [
                {
                    "caseNo": "대법원 2019다12345",
                    "court": "대법원",
                    "decisionDate": "2019-05-30",
                    "summary": "임대인이 계약기간 중 임차인에게 퇴거를 요구한 사례에서, 정당한 사유 없는 퇴거 요구는 불법이며 이로 인한 손해배상 책임이 있다고 판결했습니다."
                }
            ]
        
        # 상세 법률 상담 생성
        response = await self.claude_service.generate_legal_consultation(
            user_description, formatted_laws, formatted_precedents
        )
        
        return response
