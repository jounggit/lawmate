import json
import re
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings

class ClaudeService:
    def __init__(self):
        self.api_key = settings.CLAUDE_API_KEY
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-7-sonnet-20250219"  # 최신 모델 사용
    
    def extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        텍스트에서 JSON 내용을 추출하는 함수
        여러 방법으로 추출을 시도하며, 가능한 형식:
        1. 일반 JSON 객체
        2. 마크다운 코드 블록 내 JSON (```json ... ```)
        3. 중괄호({})로 둘러싸인 내용
        """
        # 방법 1: 전체 텍스트가 JSON인 경우
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 방법 2: 마크다운 코드 블록에서 JSON 추출
        json_code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_code_block:
            try:
                return json.loads(json_code_block.group(1))
            except json.JSONDecodeError:
                pass
        
        # 방법 3: 텍스트에서 중괄호로 둘러싸인 부분 찾기
        json_braces = re.search(r'({[\s\S]*?})', text)
        if json_braces:
            try:
                return json.loads(json_braces.group(1))
            except json.JSONDecodeError:
                pass
        
        # 모든 방법이 실패하면 원본 텍스트를 반환
        return {"raw_response": text}
        
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
        
        JSON 형식으로만 응답해주세요. 추가 설명이나 텍스트를 포함하지 마세요.
        """
        
        response = await self._call_claude_api(prompt)
        
        # 향상된 JSON 추출 로직 사용
        return self.extract_json_from_text(response)
    
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
        
        JSON 형식으로만 응답해주세요. 추가 설명이나 텍스트를 포함하지 마세요.
        """
        
        response = await self._call_claude_api(prompt)
        
        # 향상된 JSON 추출 로직 사용
        return self.extract_json_from_text(response)
    
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
    
    async def generate_legal_consultation(self, user_description: str, laws: List[Dict], cases: List[Dict]) -> str:
        """
        사용자의 법률 문제와 관련 법령 및 판례를 바탕으로 종합적인 법률 상담 답변 생성
        사용자가 구체적으로 어떻게 대응해야 하는지에 대한 단계별 안내 포함
        
        Parameters:
        - user_description: 사용자가 설명한 법률 문제
        - laws: 관련 법령 정보 리스트 (법령명, 조항, 내용, 링크 포함)
        - cases: 관련 판례 정보 리스트 (사건번호, 법원, 판결일, 판결요지, 링크 포함)
        
        Returns:
        - 법률 상담 답변 (종합적인 분석, 대응 방안, 구체적 절차 포함)
        """
        # 법령 및 판례 정보 정리 (링크 정보 포함)
        laws_text = "\n\n".join([f"법령명: {law.get('lawName')}\n조항: {law.get('article')}\n내용: {law.get('content')}\n링크: {law.get('link', '')}" for law in laws])
        cases_text = "\n\n".join([f"사건번호: {case.get('caseNo')}\n법원: {case.get('court', '')}\n판결일: {case.get('decisionDate', '')}\n판결요지: {case.get('summary')}\n링크: {case.get('link', '')}" for case in cases])
        
        prompt = f"""
        당신은 경험이 풍부한 법률 전문가입니다. 다음 사용자의 법률 문제에 대해 관련 법령과 판례를 참고하여 
        상세하고 실용적인 법률 상담 답변을 제공해주세요. 전문 용어는 쉽게 풀어서 설명하고, 
        사용자가 취해야 할 구체적인 행동 단계와 대응 방법을 명확하게 제시해주세요.
        
        ## 사용자 문제:
        {user_description}
        
        ## 관련 법령:
        {laws_text if laws_text else "관련 법령 정보가 없습니다."}
        
        ## 관련 판례:
        {cases_text if cases_text else "관련 판례 정보가 없습니다."}
        
        다음 구조로 법률 상담 답변을 작성해주세요:
        
        1. 문제 요약: 사용자의 법률 문제를 명확하게 요약
        2. 법적 분석: 관련 법령과 판례를 바탕으로 사용자의 법적 상황 분석
        3. 사용자의 권리와 의무: 현 상황에서 사용자가 가진 법적 권리와 의무 설명
        4. 대응 방안: 구체적인 대응 방법 제시 (여러 선택지가 있다면 각 옵션의 장단점 설명)
        5. 단계별 행동 계획: 사용자가 취해야 할 구체적인 행동을 순차적으로 안내
        6. 필요 서류/증거: 준비해야 할 서류나 확보해야 할 증거 안내
        7. 법적 시간 제한: 관련 소멸시효나 기한이 있다면 명시
        8. 전문가 도움 여부: 변호사 상담이 필요한 시점과 이유 안내
        9. 참고 자료: 답변에서 사용한 법령 및 판례의 링크 제공
        
        각 법령과 판례의 링크 정보를 적극 활용하여, 사용자가 필요시 원본 법령이나 판례를 직접 확인할 수 있도록 안내해주세요.
        답변의 끝부분에는 "더 자세한 법령 및 판례 정보는 위에 제공된 링크에서 확인하실 수 있습니다."라는 문구를 추가해주세요.
        
        명확하고 실용적인 조언을 제공하되, 단정적인 법적 판단은 피하고 상황에 따른 가능성을 설명해주세요.
        일반인도 쉽게 이해하고 따를 수 있는 언어로 작성해주세요.
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
        
        try:
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
                    error_msg = f"Claude API 호출 실패: {response.status_code}, {response.text}"
                    
                    # 주요 오류 코드에 대한 추가 정보
                    if response.status_code == 401:
                        error_msg += "\n인증 오류: API 키가 유효하지 않거나 만료되었습니다."
                    elif response.status_code == 400:
                        error_msg += "\n요청 오류: 요청 형식이나 매개변수가 잘못되었습니다."
                    elif response.status_code == 429:
                        error_msg += "\n요청 한도 초과: API 호출 한도를 초과했습니다."
                    
                    raise Exception(error_msg)
        except httpx.RequestError as e:
            raise Exception(f"네트워크 오류: {e}")
        except Exception as e:
            if not str(e).startswith("Claude API 호출 실패") and not str(e).startswith("네트워크 오류"):
                raise Exception(f"예상치 못한 오류: {e}")
            raise
