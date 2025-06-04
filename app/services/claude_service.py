import json
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings

class ClaudeService:
    def __init__(self):
        self.api_key = settings.CLAUDE_API_KEY
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-7-sonnet-20250219"  # 최신 모델 사용
        
    async def analyze_legal_issue(self, description: str) -> Dict[str, Any]:
        """사용자의 법률 문제를 분석하여 관련 법률 분야와 키워드 추출"""
        
        prompt = f"""
        당신은 법률 전문가입니다. 다음 사용자의 법률 문제를 분석하고, 
        관련된 법률 분야, 핵심 법률 쟁점과 키워드를 추출해주세요.
        
        사용자 문제:
        {description}
        
        다음 형식으로 JSON 응답을 제공해주세요:
        {{
            "legal_category": "관련 법률 분야 (예: 민사, 형사, 부동산, 계약, 노동 등)",
            "key_issues": ["핵심 법률 쟁점 1", "핵심 법률 쟁점 2", ...],
            "keywords": ["키워드1", "키워드2", ...],
            "relevant_laws": ["관련 법률1", "관련 법률2", ...]
        }}
        """
        
        response = await self._call_claude_api(prompt)
        
        # Claude 응답에서 JSON 추출
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트 응답 그대로 반환
            return {"raw_response": response}
    
    async def summarize_legal_info(self, laws: List[Dict], cases: List[Dict]) -> Dict[str, Any]:
        """법령과 판례 정보를 요약하고 쉽게 해석"""
        
        laws_text = "\n\n".join([f"법령명: {law['lawName']}\n조항: {law['article']}\n내용: {law['content']}" for law in laws])
        cases_text = "\n\n".join([f"사건번호: {case['caseNo']}\n판결요지: {case['summary']}" for case in cases])
        
        prompt = f"""
        당신은 법률 전문가입니다. 다음 법령과 판례 정보를 일반인이 이해하기 쉽게 요약하고 
        해석해주세요. 전문 용어는 가능한 쉬운 언어로 풀어서 설명해주세요.
        
        ## 관련 법령
        {laws_text}
        
        ## 관련 판례
        {cases_text}
        
        다음 형식으로 JSON 응답을 제공해주세요:
        {{
            "simplified_laws": [
                {{"law_name": "법령명", "explanation": "쉬운 설명"}}
            ],
            "simplified_cases": [
                {{"case_no": "사건번호", "explanation": "쉬운 설명", "implications": "이 판례가 의미하는 바"}}
            ],
            "user_rights": ["사용자의 법적 권리 1", "사용자의 법적 권리 2", ...],
            "user_obligations": ["사용자의 법적 의무 1", "사용자의 법적 의무 2", ...]
        }}
        """
        
        response = await self._call_claude_api(prompt)
        
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {"raw_response": response}
    
    async def generate_document_draft(self, doc_type: str, case_info: Dict[str, Any], 
                                     recipient_info: Optional[Dict[str, Any]] = None) -> str:
        """법률 문서 초안 생성 (내용증명, 이의제기서 등)"""
        
        recipient_text = ""
        if recipient_info:
            recipient_text = f"""
            수신자 정보:
            이름/기관명: {recipient_info.get('name', '')}
            주소: {recipient_info.get('address', '')}
            연락처: {recipient_info.get('contact', '')}
            """
        
        prompt = f"""
        당신은 법률 문서 작성 전문가입니다. 다음 정보를 바탕으로 {doc_type} 문서 초안을 작성해주세요.
        
        ## 사례 정보
        제목: {case_info.get('title', '')}
        내용: {case_info.get('description', '')}
        관련 법률 분야: {case_info.get('legal_category', '')}
        
        {recipient_text}
        
        문서의 형식과 내용은 한국의 법률 관행에 맞게 작성해주세요. 
        필요한 법적 문구와 형식을 갖추되, 일반인도 이해할 수 있는 명확한 언어로 작성해주세요.
        """
        
        response = await self._call_claude_api(prompt)
        return response
    
    async def _call_claude_api(self, prompt: str) -> str:
        """Claude API 호출 함수"""
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=60.0  # 타임아웃 설정
            )
            
            if response.status_code == 200:
                result = response.json()
                # Claude API 응답에서 텍스트 추출
                return result["content"][0]["text"]
            else:
                raise Exception(f"Claude API 호출 실패: {response.status_code}, {response.text}")