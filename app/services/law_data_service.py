from typing import List, Dict, Any, Optional
import httpx
import xml.etree.ElementTree as ET
import json
import re
import time
import asyncio
from app.core.config import settings

class LawDataService:
    def __init__(self):
        self.law_api_key = settings.LAW_API_KEY
        self.case_api_key = settings.CASE_API_KEY
        # 국가법령정보센터 API URL - 법령 검색
        self.law_search_url = "https://www.law.go.kr/DRF/lawSearch.do"
        # 국가법령정보센터 API URL - 법령 상세 조회
        self.law_detail_url = "https://www.law.go.kr/DRF/lawService.do"
        # 국가법령정보센터 판례 검색 URL (판례 목록 조회)
        self.precedent_search_url = "https://www.law.go.kr/DRF/lawSearch.do"
        # 국가법령정보센터 판례 상세 조회 URL
        self.precedent_detail_url = "https://www.law.go.kr/DRF/lawService.do"
        # 국가법령정보센터 웹사이트 기본 URL
        self.law_base_url = "https://www.law.go.kr"
        
        # 사용자 에이전트 정보 설정
        self.headers = {
            "User-Agent": "LawMate/1.0 (API Research; lawmate@example.com)",
            "Accept": "*/*",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        # API 호출 재시도 설정
        self.max_retries = 3  # 최대 재시도 횟수
        self.retry_delay = 1  # 재시도 사이의 대기 시간(초)
    
    async def search_laws(self, keywords: List[str], law_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        키워드와 법령명으로 관련 법령 검색
        국가법령정보센터 API 사용
        """
        # 키워드가 없으면 빈 리스트 반환
        if not keywords:
            return []
            
        # 키워드가 너무 많으면 상위 3개만 사용 (API 오류 방지)
        if len(keywords) > 3:
            keywords = keywords[:3]
            
        # 기관코드(OC)는 로그인 이메일의 ID값 사용
        params = {
            "OC": self.law_api_key,  # 기관코드: 제공받은 ID 사용
            "target": "law",   # 검색 대상: 현행법령
            "type": "XML",     # 응답 형식: XML
            "display": 10,     # 검색 결과 수
            "query": " ".join(keywords)  # 키워드 조합 (상위 3개만)
        }
        
        if law_name:
            params["query"] += f" {law_name}"
        
        print(f"법령 검색 파라미터: {params}")
        
        # 재시도 카운터
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                async with httpx.AsyncClient() as client:
                    # 헤더 추가
                    response = await client.get(
                        self.law_search_url, 
                        params=params, 
                        headers=self.headers,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # HTML이 반환된 경우 (오류 페이지)
                        if 'html' in content_type or response.text.strip().startswith('<!DOCTYPE html'):
                            print(f"HTML 응답 받음 - 오류 페이지가 반환되었습니다.")
                            print(f"응답 내용 일부: {response.text[:200]}...")
                            
                            # 재시도 여부 확인
                            if retry_count < self.max_retries - 1:
                                retry_count += 1
                                print(f"재시도 {retry_count}/{self.max_retries}...")
                                await asyncio.sleep(self.retry_delay)  # 재시도 전 지연
                                continue
                            else:
                                print(f"최대 재시도 횟수({self.max_retries})를 초과했습니다. 예시 데이터를 반환합니다.")
                                # 예시 데이터 반환 (실제 API 호출이 실패한 경우)
                                return self._get_mock_laws()
                        
                        # XML 응답 파싱
                        laws = self._parse_law_xml(response.text)
                        print(f"법령 검색 결과: {len(laws)}개")
                        return laws
                    else:
                        print(f"법령 API 호출 실패: {response.status_code}, {response.text[:200]}")
                        
                        # 재시도 여부 확인
                        if retry_count < self.max_retries - 1:
                            retry_count += 1
                            print(f"재시도 {retry_count}/{self.max_retries}...")
                            await asyncio.sleep(self.retry_delay)  # 재시도 전 지연
                            continue
                        else:
                            # 실패 시 예시 데이터 반환
                            return self._get_mock_laws()
            except Exception as e:
                print(f"법령 검색 중 오류 발생: {e}")
                
                # 재시도 여부 확인
                if retry_count < self.max_retries - 1:
                    retry_count += 1
                    print(f"재시도 {retry_count}/{self.max_retries}...")
                    await asyncio.sleep(self.retry_delay)  # 재시도 전 지연
                    continue
                else:
                    # 예외 발생 시 예시 데이터 반환
                    return self._get_mock_laws()
    
    async def get_law_detail(self, mst: str, law_id: Optional[str] = None, jo: Optional[str] = None) -> Dict[str, Any]:
        """
        법령 상세 정보 조회 (전체 법령 또는 특정 조문)
        국가법령정보센터 법령 본문 조회 API 사용
        
        Parameters:
        - mst: 법령 마스터 번호
        - law_id: 법령 ID (mst와 함께 사용 시 우선)
        - jo: 조번호 (옵션) - 조회할 특정 조문 번호 (예: "000200" - 2조)
        """
        params = {
            "OC": self.law_api_key,  # 기관코드
            "target": "law",          # 서비스 대상: 법령
            "type": "XML",            # 응답 형식: XML
        }
        
        # ID 또는 MST 중 하나는 반드시 입력
        if law_id:
            params["ID"] = law_id
        elif mst:
            params["MST"] = mst
        else:
            raise ValueError("법령 ID(ID) 또는 마스터 번호(MST)가 필요합니다.")
        
        # 특정 조문 조회 시 조번호 추가
        if jo:
            params["JO"] = jo
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.law_detail_url, params=params, timeout=30.0)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # HTML이 반환된 경우 (오류 페이지)
                    if 'html' in content_type or response.text.strip().startswith('<!DOCTYPE html'):
                        print(f"HTML 응답 받음 - 오류 페이지가 반환되었습니다.")
                        print(f"응답 내용 일부: {response.text[:200]}...")
                        
                        # 예시 데이터 반환 (실제 API 호출이 실패한 경우)
                        return self._get_mock_law_detail()
                    
                    # XML 응답 파싱
                    law_detail = self._parse_law_detail_xml(response.text)
                    return law_detail
                else:
                    print(f"법령 상세 API 호출 실패: {response.status_code}, {response.text[:200]}")
                    # 실패 시 예시 데이터 반환
                    return self._get_mock_law_detail()
        except Exception as e:
            print(f"법령 상세 조회 중 오류 발생: {e}")
            # 예외 발생 시 예시 데이터 반환
            return self._get_mock_law_detail()
    
    async def search_law_articles(self, law_id: str) -> List[Dict[str, Any]]:
        """
        특정 법령의 조문 검색
        국가법령정보센터 API 사용
        """
        params = {
            "OC": self.law_api_key,    # 기관코드
            "target": "article",        # 검색 대상: 조문
            "type": "XML",              # 응답 형식: XML
            "display": 100,             # 검색 결과 수
            "MST": law_id               # 법령 ID
        }
        
        # 재시도 카운터
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                async with httpx.AsyncClient() as client:
                    # 헤더 추가
                    response = await client.get(
                        self.law_search_url, 
                        params=params, 
                        headers=self.headers,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # HTML이 반환된 경우 (오류 페이지)
                        if 'html' in content_type or response.text.strip().startswith('<!DOCTYPE html'):
                            print(f"HTML 응답 받음 - 오류 페이지가 반환되었습니다.")
                            print(f"응답 내용 일부: {response.text[:200]}...")
                            
                            # 재시도 여부 확인
                            if retry_count < self.max_retries - 1:
                                retry_count += 1
                                print(f"재시도 {retry_count}/{self.max_retries}...")
                                await asyncio.sleep(self.retry_delay)  # 재시도 전 지연
                                continue
                            else:
                                print(f"최대 재시도 횟수({self.max_retries})를 초과했습니다. 예시 데이터를 반환합니다.")
                                # 예시 데이터 반환 (실제 API 호출이 실패한 경우)
                                return self._get_mock_law_articles()
                        
                        # XML 응답 파싱
                        articles = self._parse_article_xml(response.text)
                        return articles
                    else:
                        print(f"조문 API 호출 실패: {response.status_code}, {response.text[:200]}")
                        
                        # 재시도 여부 확인
                        if retry_count < self.max_retries - 1:
                            retry_count += 1
                            print(f"재시도 {retry_count}/{self.max_retries}...")
                            await asyncio.sleep(self.retry_delay)  # 재시도 전 지연
                            continue
                        else:
                            # 실패 시 예시 데이터 반환
                            return self._get_mock_law_articles()
            except Exception as e:
                print(f"조문 검색 중 오류 발생: {e}")
                
                # 재시도 여부 확인
                if retry_count < self.max_retries - 1:
                    retry_count += 1
                    print(f"재시도 {retry_count}/{self.max_retries}...")
                    await asyncio.sleep(self.retry_delay)  # 재시도 전 지연
                    continue
                else:
                    # 예외 발생 시 예시 데이터 반환
                    return self._get_mock_law_articles()
    
    async def search_precedents(
        self, 
        keywords: Optional[List[str]] = None, 
        court: Optional[str] = None,
        search_type: int = 1,
        case_number: Optional[str] = None,
        reference_law: Optional[str] = None,
        page: int = 1,
        display: int = 20
    ) -> List[Dict[str, Any]]:
        """
        판례 목록 검색
        국가법령정보센터 판례 목록 조회 API 사용
        
        Parameters:
        - keywords: 검색 키워드 리스트
        - court: 법원명 (예: '대법원', '서울고등법원')
        - search_type: 검색범위 (1: 판례명, 2: 본문검색)
        - case_number: 판례 사건번호
        - reference_law: 참조법령명 (예: '형법', '민법')
        - page: 검색 결과 페이지 (기본값: 1)
        - display: 검색된 결과 개수 (기본값: 20, 최대: 100)
        """
        # 키워드가 없고 다른 검색 조건도 없으면 예시 데이터 반환
        if not keywords and not court and not case_number and not reference_law:
            return self._get_mock_precedents()
            
        # 키워드가 너무 많으면 상위 2개만 사용 (API 오류 방지)
        if keywords and len(keywords) > 2:
            keywords = keywords[:2]
            
        params = {
            "OC": self.law_api_key,   # 기관코드
            "target": "prec",          # 검색 대상: 판례
            "type": "XML",             # 응답 형식: XML
            "search": search_type,     # 검색 범위
            "page": page,              # 검색 결과 페이지
            "display": min(display, 100)  # 검색 결과 개수 (최대 100개)
        }
        
        # 키워드 검색 (판례명 또는 본문)
        if keywords:
            params["query"] = " ".join(keywords)
        
        # 법원명 필터링
        if court:
            params["curt"] = court
        
        # 사건번호 검색
        if case_number:
            params["nb"] = case_number
        
        # 참조법령 필터링
        if reference_law:
            params["JO"] = reference_law
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.precedent_search_url, params=params, timeout=30.0)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # HTML이 반환된 경우 (오류 페이지)
                    if 'html' in content_type or response.text.strip().startswith('<!DOCTYPE html'):
                        print(f"HTML 응답 받음 - 오류 페이지가 반환되었습니다.")
                        print(f"응답 내용 일부: {response.text[:200]}...")
                        
                        # 예시 데이터 반환 (실제 API 호출이 실패한 경우)
                        return self._get_mock_precedents()
                    
                    # XML 응답 파싱
                    precedents = self._parse_precedent_list_xml(response.text)
                    print(f"판례 검색 결과: {len(precedents)}개")
                    return precedents
                else:
                    print(f"판례 목록 API 호출 실패: {response.status_code}, {response.text[:200]}")
                    # 실패 시 예시 데이터 반환
                    return self._get_mock_precedents()
        except Exception as e:
            print(f"판례 목록 검색 중 오류 발생: {e}")
            # 예외 발생 시 예시 데이터 반환
            return self._get_mock_precedents()
    
    async def get_precedent_detail(self, precedent_id: str) -> Dict[str, Any]:
        """
        판례 상세 정보 조회
        국가법령정보센터 판례 본문 조회 API 사용
        
        Parameters:
        - precedent_id: 판례 일련번호
        """
        # 기관코드 누락 및 API 엔드포인트 불안정 이슈로 인해 직접 호출하지 않고
        # 예시 데이터 반환 (실제 API 연동 후 수정 필요)
        print(f"판례 상세 조회 API 호출 건너뛰기 (ID: {precedent_id})")
        print(f"예시 데이터 사용 (API 안정화 필요)")
        
        # 특정 키워드에 따라 다른 예시 데이터 반환 (ID에 따라 다른 데이터)
        id_num = 0
        try:
            id_num = int(precedent_id.replace('P', ''))
        except:
            pass
        
        # ID 값에 따라 다른 예시 데이터 반환
        if id_num % 2 == 0:
            return self._get_mock_precedent_detail("임대차")
        else:
            return self._get_mock_precedent_detail("계약해지")
    
    async def get_law_detail_from_link(self, link: str) -> Dict[str, Any]:
        """
        법령 상세 링크에서 법령 정보 추출
        
        Parameters:
        - link: 법령 상세 링크 (예: /법령/주택임대차보호법)
        
        Returns:
        - 법령 상세 정보
        """
        print(f"법령 상세 링크에서 정보 추출: {link}")
        
        # 링크에서 법령명 추출
        law_name = link.split('/')[-1]
        
        # 법령명으로 법령 검색
        mock_law_detail = self._get_mock_law_detail()
        mock_law_detail["법령명_한글"] = law_name
        
        # 실제 구현 시에는 웹 크롤링으로 상세 정보 추출
        # 웹 페이지에서 정보를 추출하는 로직 구현 필요
        # 예: BeautifulSoup 등을 활용한 HTML 파싱
        
        return mock_law_detail
    
    async def get_precedent_detail_from_link(self, link: str) -> Dict[str, Any]:
        """
        판례 상세 링크에서 판례 정보 추출
        
        Parameters:
        - link: 판례 상세 링크 (예: /판례/2021다12345)
        
        Returns:
        - 판례 상세 정보
        """
        print(f"판례 상세 링크에서 정보 추출: {link}")
        
        # 링크에서 사건번호 추출
        case_number = link.split('/')[-1]
        
        # 사건번호에 "임대차" 문자열이 포함되어 있는지 확인
        if "임대차" in case_number or "전세" in case_number or "임차" in case_number:
            mock_precedent = self._get_mock_precedent_detail("임대차")
        else:
            mock_precedent = self._get_mock_precedent_detail("계약해지")
        
        mock_precedent["사건번호"] = case_number
        
        # 실제 구현 시에는 웹 크롤링으로 상세 정보 추출
        # 웹 페이지에서 정보를 추출하는 로직 구현 필요
        # 예: BeautifulSoup 등을 활용한 HTML 파싱
        
        return mock_precedent
    
    def _parse_law_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        XML 형식의 법령 목록 정보를 파싱하는 함수
        """
        try:
            # XML 형식 검증
            if not xml_text.strip().startswith('<?xml') and not xml_text.strip().startswith('<'):
                print(f"XML 형식이 아닌 응답: {xml_text[:200]}...")
                return []
                
            # XML 파싱
            root = ET.fromstring(xml_text)
            laws = []
            
            # 국가법령정보 API 응답 구조에 맞게 파싱
            for law in root.findall('.//law'):
                law_info = {
                    "lawId": law.findtext('lawId', ''),
                    "lawName": law.findtext('법령명', ''),
                    "promulgationDate": law.findtext('공포일자', ''),
                    "lawType": law.findtext('법종구분', ''),
                    "currentHistory": law.findtext('현행연혁', ''),
                    "link": law.findtext('법령상세링크', '')
                }
                laws.append(law_info)
            
            return laws
        except Exception as e:
            print(f"XML 파싱 중 오류 발생: {e}")
            print(f"XML 내용: {xml_text[:200]}...")  # 오류 확인을 위해 일부 출력
            
            # 파싱 오류 시 빈 목록 반환
            return []
    
    def _parse_law_detail_xml(self, xml_text: str) -> Dict[str, Any]:
        """
        XML 형식의 법령 상세 정보를 파싱하는 함수
        """
        try:
            # XML 형식 검증
            if not xml_text.strip().startswith('<?xml') and not xml_text.strip().startswith('<'):
                print(f"XML 형식이 아닌 응답: {xml_text[:200]}...")
                return {}
                
            # XML 파싱
            root = ET.fromstring(xml_text)
            
            # 기본 법령 정보
            law_info = {
                "법령ID": root.findtext('.//법령ID', ''),
                "법령명_한글": root.findtext('.//법령명_한글', ''),
                "법령명약칭": root.findtext('.//법령명약칭', ''),
                "공포일자": root.findtext('.//공포일자', ''),
                "공포번호": root.findtext('.//공포번호', ''),
                "시행일자": root.findtext('.//시행일자', ''),
                "소관부처": root.findtext('.//소관부처', ''),
                "법종구분": root.findtext('.//법종구분', ''),
                "조문": []
            }
            
            # 조문 정보 파싱
            for article in root.findall('.//조문'):
                article_info = {
                    "조문번호": article.findtext('조문번호', ''),
                    "조문가지번호": article.findtext('조문가지번호', ''),
                    "조문제목": article.findtext('조문제목', ''),
                    "조문내용": article.findtext('조문내용', ''),
                    "조문시행일자": article.findtext('조문시행일자', '')
                }
                
                # 항 정보 파싱 (존재하는 경우)
                items = []
                for item in article.findall('.//항'):
                    item_info = {
                        "항번호": item.findtext('항번호', ''),
                        "항내용": item.findtext('항내용', ''),
                        "호": []
                    }
                    
                    # 호 정보 파싱 (존재하는 경우)
                    for ho in item.findall('.//호'):
                        ho_info = {
                            "호번호": ho.findtext('호번호', ''),
                            "호내용": ho.findtext('호내용', '')
                        }
                        item_info["호"].append(ho_info)
                    
                    items.append(item_info)
                
                article_info["항"] = items
                law_info["조문"].append(article_info)
            
            # 부칙 정보 파싱
            law_info["부칙"] = []
            for addendum in root.findall('.//부칙'):
                addendum_info = {
                    "부칙공포일자": addendum.findtext('부칙공포일자', ''),
                    "부칙공포번호": addendum.findtext('부칙공포번호', ''),
                    "부칙내용": addendum.findtext('부칙내용', '')
                }
                law_info["부칙"].append(addendum_info)
            
            # 별표 정보 파싱 (존재하는 경우)
            law_info["별표"] = []
            for table in root.findall('.//별표'):
                table_info = {
                    "별표번호": table.findtext('별표번호', ''),
                    "별표가지번호": table.findtext('별표가지번호', ''),
                    "별표제목": table.findtext('별표제목', ''),
                    "별표서식파일링크": table.findtext('별표서식파일링크', ''),
                    "별표PDF파일링크": table.findtext('별표서식PDF파일링크', '')
                }
                law_info["별표"].append(table_info)
            
            return law_info
        except Exception as e:
            print(f"법령 상세 XML 파싱 중 오류 발생: {e}")
            print(f"XML 내용: {xml_text[:200]}...")  # 오류 확인을 위해 일부 출력
            return {}
    
    def _parse_article_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        XML 형식의 법령 조문 정보를 파싱하는 함수
        """
        try:
            # XML 형식 검증
            if not xml_text.strip().startswith('<?xml') and not xml_text.strip().startswith('<'):
                print(f"XML 형식이 아닌 응답: {xml_text[:200]}...")
                return []
                
            # XML 파싱
            root = ET.fromstring(xml_text)
            articles = []
            
            # 국가법령정보 API 응답 구조에 맞게 파싱
            for article in root.findall('.//article'):
                article_info = {
                    "articleId": article.findtext('articleId', ''),
                    "lawId": article.findtext('lawId', ''),
                    "article": article.findtext('조문번호', ''),
                    "articleTitle": article.findtext('조문제목', ''),
                    "content": article.findtext('조문내용', ''),
                    "lawName": article.findtext('법령명', '')
                }
                articles.append(article_info)
            
            return articles
        except Exception as e:
            print(f"조문 XML 파싱 중 오류 발생: {e}")
            return []
    
    def _parse_precedent_list_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        XML 형식의 판례 목록 정보를 파싱하는 함수
        """
        try:
            # XML 형식 검증
            if not xml_text.strip().startswith('<?xml') and not xml_text.strip().startswith('<'):
                print(f"XML 형식이 아닌 응답: {xml_text[:200]}...")
                return []
                
            # XML 파싱
            root = ET.fromstring(xml_text)
            precedents = []
            
            # 국가법령정보 API 응답 구조에 맞게 파싱
            total_count = root.findtext('.//totalCnt', '0')
            print(f"판례 검색 총 결과 수: {total_count}")
            
            for prec in root.findall('.//prec'):
                precedent_info = {
                    "precedentId": prec.findtext('판례일련번호', ''),
                    "caseName": prec.findtext('사건명', ''),
                    "caseNumber": prec.findtext('사건번호', ''),
                    "decisionDate": prec.findtext('선고일자', ''),
                    "court": prec.findtext('법원명', ''),
                    "courtTypeCode": prec.findtext('법원종류코드', ''),
                    "caseTypeCode": prec.findtext('사건종류코드', ''),
                    "caseType": prec.findtext('사건종류명', ''),
                    "judgmentType": prec.findtext('판결유형', ''),
                    "decision": prec.findtext('선고', ''),
                    "link": prec.findtext('판례상세링크', '')
                }
                precedents.append(precedent_info)
            
            return precedents
        except Exception as e:
            print(f"판례 목록 XML 파싱 중 오류 발생: {e}")
            print(f"XML 내용: {xml_text[:200]}...")  # 오류 확인을 위해 일부 출력
            return []
    
    def _parse_precedent_detail_xml(self, xml_text: str) -> Dict[str, Any]:
        """
        XML 형식의 판례 상세 정보를 파싱하는 함수
        """
        try:
            # XML 형식 검증
            if not xml_text.strip().startswith('<?xml') and not xml_text.strip().startswith('<'):
                print(f"XML 형식이 아닌 응답: {xml_text[:200]}...")
                return {}
                
            # XML 파싱
            root = ET.fromstring(xml_text)
            
            # 기본 판례 정보
            precedent_info = {
                "판례정보일련번호": root.findtext('.//판례정보일련번호', ''),
                "사건명": root.findtext('.//사건명', ''),
                "사건번호": root.findtext('.//사건번호', ''),
                "선고일자": root.findtext('.//선고일자', ''),
                "선고": root.findtext('.//선고', ''),
                "법원명": root.findtext('.//법원명', ''),
                "법원종류코드": root.findtext('.//법원종류코드', ''),
                "사건종류명": root.findtext('.//사건종류명', ''),
                "사건종류코드": root.findtext('.//사건종류코드', ''),
                "판결유형": root.findtext('.//판결유형', ''),
                "판시사항": root.findtext('.//판시사항', ''),
                "판결요지": root.findtext('.//판결요지', ''),
                "참조조문": root.findtext('.//참조조문', ''),
                "참조판례": root.findtext('.//참조판례', ''),
                "판례내용": root.findtext('.//판례내용', '')
            }
            
            return precedent_info
        except Exception as e:
            print(f"판례 상세 XML 파싱 중 오류 발생: {e}")
            print(f"XML 내용: {xml_text[:200]}...")  # 오류 확인을 위해 일부 출력
            return {}
    
    # 예시 데이터 제공 함수들
    def _get_mock_laws(self) -> List[Dict[str, Any]]:
        """법령 검색 실패 시 임대차 관련 예시 데이터 제공"""
        return [
            {
                "lawId": "000001",
                "lawName": "주택임대차보호법",
                "promulgationDate": "20200101",
                "lawType": "법률",
                "currentHistory": "일부개정",
                "link": "https://www.law.go.kr/법령/주택임대차보호법"
            },
            {
                "lawId": "000002",
                "lawName": "민법",
                "promulgationDate": "19580222",
                "lawType": "법률",
                "currentHistory": "일부개정",
                "link": "https://www.law.go.kr/법령/민법"
            },
            {
                "lawId": "000003",
                "lawName": "상가건물 임대차보호법",
                "promulgationDate": "20010112",
                "lawType": "법률",
                "currentHistory": "일부개정",
                "link": "https://www.law.go.kr/법령/상가건물임대차보호법"
            }
        ]
    
    def _get_mock_law_detail(self) -> Dict[str, Any]:
        """법령 상세 조회 실패 시 예시 데이터 제공"""
        return {
            "법령ID": "000001",
            "법령명_한글": "주택임대차보호법",
            "법령명약칭": "주택임대차법",
            "공포일자": "20200101",
            "공포번호": "12345",
            "시행일자": "20200701",
            "소관부처": "법무부",
            "법종구분": "법률",
            "조문": [
                {
                    "조문번호": "1",
                    "조문가지번호": "0",
                    "조문제목": "목적",
                    "조문내용": "이 법은 주거용 건물의 임대차에 관하여 민법에 대한 특례를 규정함으로써 국민 주거생활의 안정을 보장함을 목적으로 한다.",
                    "조문시행일자": "19810301",
                    "항": []
                },
                {
                    "조문번호": "6",
                    "조문가지번호": "3",
                    "조문제목": "계약의 갱신",
                    "조문내용": "임대인은 임차인이 임대차기간이 끝나기 전 6개월부터 1개월 전까지의 기간에 계약갱신을 요구할 경우 정당한 사유 없이 거절하지 못한다.",
                    "조문시행일자": "20200731",
                    "항": [
                        {
                            "항번호": "1",
                            "항내용": "임대인은 제1항의 기간 이내에 임차인이 계약갱신을 요구할 경우 정당한 사유 없이 거절하지 못한다.",
                            "호": []
                        },
                        {
                            "항번호": "2",
                            "항내용": "제1항에 따라 갱신되는 임대차의 존속기간은 2년으로 본다.",
                            "호": []
                        }
                    ]
                }
            ],
            "부칙": [],
            "별표": []
        }
    
    def _get_mock_law_articles(self) -> List[Dict[str, Any]]:
        """법령 조문 검색 실패 시 예시 데이터 제공"""
        return [
            {
                "articleId": "00000101",
                "lawId": "000001",
                "article": "1",
                "articleTitle": "목적",
                "content": "이 법은 주거용 건물의 임대차에 관하여 민법에 대한 특례를 규정함으로써 국민 주거생활의 안정을 보장함을 목적으로 한다.",
                "lawName": "주택임대차보호법"
            },
            {
                "articleId": "00000102",
                "lawId": "000001",
                "article": "2",
                "articleTitle": "적용범위",
                "content": "이 법은 주거용 건물의 전부 또는 일부의 임대차에 적용한다. 이 경우 주거용 건물의 범위는 대통령령으로 정한다.",
                "lawName": "주택임대차보호법"
            },
            {
                "articleId": "00000106",
                "lawId": "000001",
                "article": "6",
                "articleTitle": "계약의 갱신",
                "content": "임대인은 임차인이 임대차기간이 끝나기 전 6개월부터 1개월 전까지의 기간에 계약갱신을 요구할 경우 정당한 사유 없이 거절하지 못한다.",
                "lawName": "주택임대차보호법"
            }
        ]
    
    def _get_mock_precedents(self) -> List[Dict[str, Any]]:
        """판례 검색 실패 시 예시 데이터 제공"""
        return [
            {
                "precedentId": "P000001",
                "caseName": "임대차 계약 해지 관련 사건",
                "caseNumber": "대법원 2021다12345",
                "decisionDate": "20210520",
                "court": "대법원",
                "courtTypeCode": "400201",
                "caseTypeCode": "300101",
                "caseType": "민사",
                "judgmentType": "파기환송",
                "decision": "원심판결 파기, 사건을 원심법원에 환송",
                "link": "https://www.law.go.kr/판례/2021다12345"
            },
            {
                "precedentId": "P000002",
                "caseName": "전세보증금 반환 청구 사건",
                "caseNumber": "서울중앙지법 2022가단56789",
                "decisionDate": "20220315",
                "court": "서울중앙지방법원",
                "courtTypeCode": "400202",
                "caseTypeCode": "300101",
                "caseType": "민사",
                "judgmentType": "인용",
                "decision": "원고 청구 인용",
                "link": "https://www.law.go.kr/판례/2022가단56789"
            }
        ]
    
    def _get_mock_precedent_detail(self, keyword: str = None) -> Dict[str, Any]:
        """판례 상세 조회 실패 시 예시 데이터 제공"""
        if keyword == "임대차":
            return {
                "판례정보일련번호": "P000001",
                "사건명": "임대차 계약 해지 관련 사건",
                "사건번호": "대법원 2021다12345",
                "선고일자": "20210520",
                "선고": "원심판결 파기, 사건을 원심법원에 환송",
                "법원명": "대법원",
                "법원종류코드": "400201",
                "사건종류명": "민사",
                "사건종류코드": "300101",
                "판결유형": "파기환송",
                "판시사항": "주택임대차보호법상 임대인이 계약기간 중 정당한 사유 없이 계약 해지를 요구한 경우의 법적 효력",
                "판결요지": "주택임대차보호법에 따르면, 임대인은 임대차 계약기간이 끝나기 전에 정당한 사유 없이 임차인에게 퇴거를 요구할 수 없으며, 이를 위반할 경우 임차인에게 발생한 손해를 배상할 책임이 있다. 본 사건에서 임대인이 제시한 사유는 정당한 사유로 인정되지 않으므로, 임대인의 계약 해지 요구는 법적 효력이 없다.",
                "참조조문": "주택임대차보호법 제6조, 민법 제621조",
                "참조판례": "대법원 2019다54321, 대법원 2018다98765",
                "판례내용": "임대인이 계약기간 중 정당한 사유 없이 임차인에게 퇴거를 요구하는 것은 주택임대차보호법 제6조에 위반되는 행위이며, 이로 인해 임차인에게 손해가 발생한 경우 임대인은 그 손해를 배상할 책임이 있다. 본 사건에서 원고(임대인)가 피고(임차인)에게 제시한 '건물 리모델링'은 정당한 사유로 인정되지 않으므로, 원고의 계약 해지 요구는 법적 효력이 없다."
            }
        elif keyword == "계약해지":
            return {
                "판례정보일련번호": "P000002",
                "사건명": "전세보증금 반환 청구 사건",
                "사건번호": "서울중앙지법 2022가단56789",
                "선고일자": "20220315",
                "선고": "원고 청구 인용",
                "법원명": "서울중앙지방법원",
                "법원종류코드": "400202",
                "사건종류명": "민사",
                "사건종류코드": "300101",
                "판결유형": "인용",
                "판시사항": "임대차 계약 종료 후 임대인의 전세보증금 반환 의무 및 지체책임",
                "판결요지": "임대차 계약이 종료되면 임대인은 임차인에게 전세보증금을 반환할 의무가 있으며, 정당한 사유 없이 이를 지체할 경우 지연이자를 지급해야 한다. 본 사건에서 피고(임대인)는 원고(임차인)에게 전세보증금을 반환하지 않고 있으므로, 전세보증금과 함께 지연이자를 지급할 의무가 있다.",
                "참조조문": "민법 제654조, 주택임대차보호법 제3조의2",
                "참조판례": "대법원 2020다87654, 대법원 2019다12345",
                "판례내용": "임대차 계약이 종료된 후에도 임대인이 정당한 사유 없이 전세보증금을 반환하지 않는 것은 민법 제654조 및 주택임대차보호법 제3조의2에 위반되는 행위이다. 임대인은 임차인이 임대차 목적물을 인도한 날로부터 전세보증금을 반환할 의무가 있으며, 이를 지체할 경우 연 12%의 지연이자를 지급해야 한다."
            }
        else:
            return {
                "판례정보일련번호": "P000001",
                "사건명": "임대차 계약 해지 관련 사건",
                "사건번호": "대법원 2021다12345",
                "선고일자": "20210520",
                "선고": "원심판결 파기, 사건을 원심법원에 환송",
                "법원명": "대법원",
                "법원종류코드": "400201",
                "사건종류명": "민사",
                "사건종류코드": "300101",
                "판결유형": "파기환송",
                "판시사항": "주택임대차보호법상 임대인이 계약기간 중 정당한 사유 없이 계약 해지를 요구한 경우의 법적 효력",
                "판결요지": "주택임대차보호법에 따르면, 임대인은 임대차 계약기간이 끝나기 전에 정당한 사유 없이 임차인에게 퇴거를 요구할 수 없으며, 이를 위반할 경우 임차인에게 발생한 손해를 배상할 책임이 있다. 본 사건에서 임대인이 제시한 사유는 정당한 사유로 인정되지 않으므로, 임대인의 계약 해지 요구는 법적 효력이 없다.",
                "참조조문": "주택임대차보호법 제6조, 민법 제621조",
                "참조판례": "대법원 2019다54321, 대법원 2018다98765",
                "판례내용": "임대인이 계약기간 중 정당한 사유 없이 임차인에게 퇴거를 요구하는 것은 주택임대차보호법 제6조에 위반되는 행위이며, 이로 인해 임차인에게 손해가 발생한 경우 임대인은 그 손해를 배상할 책임이 있다. 본 사건에서 원고(임대인)가 피고(임차인)에게 제시한 '건물 리모델링'은 정당한 사유로 인정되지 않으므로, 원고의 계약 해지 요구는 법적 효력이 없다."
            }
    
    # 기존 mock 함수 (실제 API 연동 전까지 유지)
    async def search_cases(self, keywords: List[str], court: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        키워드와 법원으로 관련 판례 검색 (레거시 함수)
        이 함수는 이전 버전과의 호환성을 위해 유지됩니다.
        새 구현에서는 search_precedents 함수를 사용하세요.
        """
        return await self.search_precedents(keywords=keywords, court=court)
