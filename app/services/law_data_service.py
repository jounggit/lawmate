from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings

class LawDataService:
    def __init__(self):
        self.law_api_key = settings.LAW_API_KEY
        self.case_api_key = settings.CASE_API_KEY
        self.law_base_url = "https://www.law.go.kr/DRF/lawSearch.do"
        self.case_base_url = "https://www.data.go.kr/api/15048729/v1/openapi-data"
    
    async def search_laws(self, keywords: List[str], law_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        키워드와 법령명으로 관련 법령 검색
        국가법령정보센터 API 사용
        """
        params = {
            "OC": self.law_api_key,
            "target": "law",
            "type": "XML",
            "display": 10,
            "query": " ".join(keywords)
        }
        
        if law_name:
            params["query"] += f" {law_name}"
            
        async with httpx.AsyncClient() as client:
            response = await client.get(self.law_base_url, params=params)
            
            if response.status_code == 200:
                # XML 응답 파싱 (실제 구현에서는 XML 파싱 라이브러리 사용)
                # 예시로 간단히 딕셔너리 리스트 반환
                return self._parse_law_xml(response.text)
            else:
                raise Exception(f"법령 API 호출 실패: {response.status_code}")
    
    async def search_cases(self, keywords: List[str], court: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        키워드와 법원으로 관련 판례 검색
        공공데이터포털 판례 API 사용
        """
        params = {
            "serviceKey": self.case_api_key,
            "pageNo": 1,
            "numOfRows": 10,
            "keyword": " ".join(keywords)
        }
        
        if court:
            params["court"] = court
            
        async with httpx.AsyncClient() as client:
            response = await client.get(self.case_base_url, params=params)
            
            if response.status_code == 200:
                return response.json().get("items", [])
            else:
                raise Exception(f"판례 API 호출 실패: {response.status_code}")
    
    def _parse_law_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        XML 형식의 법령 정보를 파싱하는 함수
        실제 구현에서는 lxml 또는 xml.etree.ElementTree 등의 라이브러리 사용
        """
        # 예시 응답 (실제 구현은 XML 파싱 필요)
        return [
            {
                "lawId": "12345",
                "lawName": "민법",
                "article": "제750조",
                "content": "고의 또는 과실로 인한 위법행위로 타인에게 손해를 가한 자는 그 손해를 배상할 책임이 있다."
            },
            {
                "lawId": "23456",
                "lawName": "민사소송법",
                "article": "제247조",
                "content": "소는 법원에 소장을 제출함으로써 제기한다."
            }
        ]