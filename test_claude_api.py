import asyncio
import json
import os
import re
from dotenv import load_dotenv
import httpx

# .env 파일에서 환경 변수 로드
load_dotenv()

# Claude API 키 가져오기
api_key = os.getenv("CLAUDE_API_KEY")
if not api_key:
    raise ValueError("CLAUDE_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

# 테스트 모드에서는 기본값 검사를 건너뛰기 위해 주석 처리
# elif api_key == "your-claude-api-key":
#     raise ValueError("CLAUDE_API_KEY가 기본값('your-claude-api-key')으로 설정되어 있습니다. 실제 API 키로 업데이트하세요.")

def extract_json_from_text(text):
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
    
    # 모든 방법이 실패하면 None 반환
    return None

async def test_claude_api():
    """Claude API 테스트 함수"""
    
    # API 엔드포인트 및 모델 설정
    base_url = "https://api.anthropic.com/v1/messages"
    model = "claude-3-7-sonnet-20250219"
    
    # 테스트 프롬프트
    prompt = """
    당신은 법률 전문가입니다. 다음 사용자의 법률 문제를 분석하고, 
    관련된 법률 분야, 핵심 법률 쟁점과 키워드를 추출해주세요.
    
    사용자 문제:
    "아파트 전세 계약을 했는데, 계약 종료 3개월 전에 집주인이 갑자기 전세금을 2천만원 올려달라고 합니다.
    거절하자 다른 세입자를 구하겠다고 합니다. 전세금 인상 요구를 거절할 권리가 있나요?"
    
    JSON 형식으로만 응답해주세요. 다음 형식을 사용하세요:
    {
        "legal_category": "관련 법률 분야 (예: 민사, 형사, 부동산, 계약, 노동 등)",
        "key_issues": ["핵심 법률 쟁점 1", "핵심 법률 쟁점 2", ...],
        "keywords": ["키워드1", "키워드2", ...],
        "relevant_laws": ["관련 법률1", "관련 법률2", ...]
    }
    
    응답에 설명이나 추가 텍스트를 포함하지 말고 JSON만 반환해주세요.
    """
    
    # API 호출 헤더 (최신 Anthropic API 형식)
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    # API 요청 데이터
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000
    }
    
    print("Claude API 호출 중...")
    print(f"API URL: {base_url}")
    print(f"사용 모델: {model}")
    print(f"API 키 처음 7자: {api_key[:7]}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                base_url,
                headers=headers,
                json=data,
                timeout=60.0
            )
            
            print(f"\n응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]
                
                print("\n=== Claude API 응답 성공 ===")
                print("\n=== 응답 내용 ===")
                print(content)
                
                # 개선된 JSON 파싱
                json_data = extract_json_from_text(content)
                
                if json_data:
                    print("\n=== JSON 파싱 성공 ===")
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    return json_data
                else:
                    print("\n=== JSON 파싱 실패 ===")
                    print("응답에서 유효한 JSON을 추출할 수 없습니다.")
                    return {"raw_response": content}
            else:
                print(f"\n=== API 호출 실패 ===")
                print(f"상태 코드: {response.status_code}")
                print(f"응답: {response.text}")
                
                # 주요 오류 코드에 대한 추가 설명
                if response.status_code == 401:
                    print("\n인증 오류 (401):")
                    print("- API 키가 유효하지 않거나 만료되었습니다.")
                    print("- .env 파일에 올바른 API 키가 설정되어 있는지 확인하세요.")
                    print("- Anthropic 콘솔에서 API 키를 다시 생성해보세요: https://console.anthropic.com/")
                elif response.status_code == 400:
                    print("\n요청 오류 (400):")
                    print("- 요청 형식이나 매개변수가 잘못되었습니다.")
                    print("- 모델명, 메시지 형식 등을 확인하세요.")
                elif response.status_code == 429:
                    print("\n요청 한도 초과 (429):")
                    print("- API 호출 한도를 초과했습니다.")
                    print("- 잠시 후 다시 시도하거나 Anthropic 콘솔에서 한도를 확인하세요.")
                elif response.status_code == 500:
                    print("\n서버 오류 (500):")
                    print("- Anthropic 서버에 문제가 있습니다.")
                    print("- 잠시 후 다시 시도하세요.")
                
                return None
    except httpx.RequestError as e:
        print(f"\n=== 네트워크 오류 ===")
        print(f"오류: {e}")
        print("- 인터넷 연결을 확인하세요.")
        print("- 프록시 설정을 확인하세요.")
        return None
    except Exception as e:
        print(f"\n=== 예외 발생 ===")
        print(f"오류 유형: {type(e).__name__}")
        print(f"오류 메시지: {e}")
        return None

if __name__ == "__main__":
    print("===== Claude API 테스트 시작 =====")
    result = asyncio.run(test_claude_api())
    
    if result:
        print("\n===== 테스트 결과 요약 =====")
        if "legal_category" in result:
            print(f"법률 분야: {result['legal_category']}")
        if "key_issues" in result:
            print(f"핵심 쟁점 수: {len(result['key_issues'])}")
        if "keywords" in result:
            print(f"키워드 수: {len(result['keywords'])}")
        if "relevant_laws" in result:
            print(f"관련 법률 수: {len(result['relevant_laws'])}")
        print("\n테스트 완료!")
    else:
        print("\n테스트 실패: API 응답을 받지 못했습니다.")
        print("\n문제 해결 방법:")
        print("1. .env 파일에 유효한 Claude API 키가 설정되어 있는지 확인하세요.")
        print("2. API 키 형식이 올바른지 확인하세요 (일반적으로 'sk-ant-...'로 시작).")
        print("3. 인터넷 연결 상태를 확인하세요.")
        print("4. Anthropic 서비스 상태를 확인하세요: https://status.anthropic.com/")
