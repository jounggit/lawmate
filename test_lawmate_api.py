import asyncio
import json
import httpx
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 기본 URL 설정
API_BASE_URL = "http://localhost:8000"  # LawMate 서버 주소

async def login():
    """테스트용 로그인 함수"""
    url = f"{API_BASE_URL}/api/auth/login"
    
    # 테스트 계정 정보
    login_data = {
        "email": os.getenv("TEST_USER_EMAIL", "test@example.com"),
        "password": os.getenv("TEST_USER_PASSWORD", "testpassword")
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=login_data)
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                print(f"로그인 실패: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"로그인 중 오류 발생: {e}")
        return None

async def create_case(token, case_data):
    """법률 사례 생성 함수"""
    url = f"{API_BASE_URL}/api/cases/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=case_data, headers=headers)
            if response.status_code in (200, 201):
                return response.json()
            else:
                print(f"사례 생성 실패: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"사례 생성 중 오류 발생: {e}")
        return None

async def analyze_case(token, case_id):
    """법률 사례 분석 함수"""
    url = f"{API_BASE_URL}/api/cases/{case_id}/analyze"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"사례 분석 실패: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"사례 분석 중 오류 발생: {e}")
        return None

async def get_case(token, case_id):
    """법률 사례 조회 함수"""
    url = f"{API_BASE_URL}/api/cases/{case_id}"
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"사례 조회 실패: {response.status_code}, {response.text}")
                return None
    except Exception as e:
        print(f"사례 조회 중 오류 발생: {e}")
        return None

async def main():
    """테스트 메인 함수"""
    print("===== LawMate API 테스트 시작 =====")
    
    # 로그인
    print("\n1. 로그인 중...")
    token = await login()
    if not token:
        print("로그인에 실패하여 테스트를 중단합니다.")
        return
    print("로그인 성공!")
    
    # 테스트 케이스 데이터
    test_case = {
        "title": "전세 계약 갱신 문제",
        "description": "아파트 전세 계약을 했는데, 계약 종료 3개월 전에 집주인이 갑자기 전세금을 2천만원 올려달라고 합니다. 거절하자 다른 세입자를 구하겠다고 합니다. 전세금 인상 요구를 거절할 권리가 있나요?",
        "category": "부동산"
    }
    
    # 사례 생성
    print("\n2. 법률 사례 생성 중...")
    case_result = await create_case(token, test_case)
    if not case_result:
        print("사례 생성에 실패하여 테스트를 중단합니다.")
        return
    
    case_id = case_result.get("id")
    print(f"사례 생성 성공! (ID: {case_id})")
    print(f"Claude 분석 결과: {case_result.get('claude_analysis', '분석 결과 없음')}")
    
    # 생성된 사례 조회
    print("\n3. 생성된 사례 조회 중...")
    case_detail = await get_case(token, case_id)
    if case_detail:
        print("사례 조회 성공!")
        print(f"사례 제목: {case_detail.get('title')}")
        print(f"법률 분야: {case_detail.get('legal_category', '정보 없음')}")
        print(f"키워드: {case_detail.get('keywords', '정보 없음')}")
        
        # Claude 분석 결과 출력 (JSON 형식이면 예쁘게 출력)
        claude_analysis = case_detail.get('claude_analysis')
        if claude_analysis:
            try:
                analysis_json = json.loads(claude_analysis)
                print("\nClaude 분석 결과:")
                print(json.dumps(analysis_json, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"\nClaude 분석 결과: {claude_analysis}")
    
    # 사례 분석
    print("\n4. 법률 사례 분석 중...")
    analysis_result = await analyze_case(token, case_id)
    if analysis_result:
        print("사례 분석 성공!")
        print("\n분석 결과:")
        print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
    
    print("\n===== 테스트 완료 =====")

if __name__ == "__main__":
    asyncio.run(main())
