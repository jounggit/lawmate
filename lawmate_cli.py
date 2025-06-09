import asyncio
import json
import os
import argparse
from dotenv import load_dotenv
import httpx

# .env 파일에서 환경 변수 로드
load_dotenv()

# Claude API 키 가져오기
api_key = os.getenv("CLAUDE_API_KEY")
if not api_key:
    raise ValueError("CLAUDE_API_KEY가 .env 파일에 설정되어 있지 않습니다.")

async def query_claude_api(prompt, format_json=True):
    """Claude API에 질의하는 함수"""
    base_url = "https://api.anthropic.com/v1/messages"
    model = "claude-3-7-sonnet-20250219"
    
    # JSON 형식 응답 요청 추가
    if format_json:
        prompt += "\n\n유효한 JSON 형식으로만 응답해주세요."
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                base_url,
                headers=headers,
                json=data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]
                
                if format_json:
                    try:
                        # JSON 문자열에서 실제 JSON 객체 추출 (텍스트 앞뒤 설명이 있을 수 있음)
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = content[json_start:json_end]
                            return json.loads(json_str)
                        else:
                            # JSON 형식이 아니면 원본 반환
                            return {"raw_response": content}
                    except json.JSONDecodeError:
                        return {"raw_response": content}
                else:
                    return content
            else:
                print(f"API 호출 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return None
    except Exception as e:
        print(f"오류 발생: {e}")
        return None

async def legal_analysis(case_description):
    """법률 문제 분석"""
    prompt = f"""
    당신은 법률 전문가입니다. 다음 사용자의 법률 문제를 분석하고, 
    관련된 법률 분야, 핵심 법률 쟁점과 키워드를 추출해주세요.
    
    사용자 문제:
    "{case_description}"
    
    다음 형식으로 JSON 응답을 제공해주세요:
    {{
        "legal_category": "관련 법률 분야 (예: 민사, 형사, 부동산, 계약, 노동 등)",
        "key_issues": ["핵심 법률 쟁점 1", "핵심 법률 쟁점 2", ...],
        "keywords": ["키워드1", "키워드2", ...],
        "relevant_laws": ["관련 법률1", "관련 법률2", ...],
        "initial_advice": "초기 법률 조언"
    }}
    """
    return await query_claude_api(prompt)

async def legal_document_draft(document_type, case_description):
    """법률 문서 초안 생성"""
    prompt = f"""
    당신은 법률 문서 작성 전문가입니다. 다음 정보를 바탕으로 {document_type} 문서 초안을 작성해주세요.
    
    사례 내용:
    "{case_description}"
    
    문서의 형식과 내용은 한국의 법률 관행에 맞게 작성해주세요.
    필요한 법적 문구와 형식을 갖추되, 일반인도 이해할 수 있는 명확한 언어로 작성해주세요.
    
    다음 형식으로 JSON 응답을 제공해주세요:
    {{
        "document_title": "문서 제목",
        "document_content": "문서 내용 (마크다운 형식)",
        "notes": "문서 사용 시 참고사항"
    }}
    """
    return await query_claude_api(prompt)

async def general_legal_inquiry(question):
    """일반 법률 질의"""
    prompt = f"""
    당신은 법률 전문가입니다. 다음 법률 질문에 대해 이해하기 쉽게 답변해주세요.
    
    질문:
    "{question}"
    
    다음 형식으로 JSON 응답을 제공해주세요:
    {{
        "answer": "질문에 대한 답변",
        "relevant_laws": ["관련 법률1", "관련 법률2", ...],
        "additional_info": "추가 참고사항"
    }}
    """
    return await query_claude_api(prompt)

async def main():
    parser = argparse.ArgumentParser(description='LawMate Claude API 테스트 도구')
    subparsers = parser.add_subparsers(dest='command', help='수행할 명령')
    
    # 법률 분석 명령
    analyze_parser = subparsers.add_parser('analyze', help='법률 문제 분석')
    analyze_parser.add_argument('description', help='법률 문제 설명')
    
    # 문서 초안 작성 명령
    document_parser = subparsers.add_parser('document', help='법률 문서 초안 생성')
    document_parser.add_argument('type', choices=['내용증명', '이의제기서', '합의서', '진술서'], help='문서 유형')
    document_parser.add_argument('description', help='사례 설명')
    
    # 일반 법률 질의 명령
    inquiry_parser = subparsers.add_parser('inquiry', help='일반 법률 질의')
    inquiry_parser.add_argument('question', help='법률 질문')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        print("법률 문제 분석 중...")
        result = await legal_analysis(args.description)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'document':
        print(f"{args.type} 문서 초안 생성 중...")
        result = await legal_document_draft(args.type, args.description)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == 'inquiry':
        print("법률 질의 처리 중...")
        result = await general_legal_inquiry(args.question)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
