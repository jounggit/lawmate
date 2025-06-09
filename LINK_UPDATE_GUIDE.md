# 법률 상담 서비스 업데이트: 상세 링크 추가

이 업데이트는 법률 상담 서비스에 상세 링크 기능을 추가하여 사용자가 법령과 판례의 원문을 쉽게 찾아볼 수 있도록 개선합니다.

## 업데이트 내용

1. **데이터베이스 업데이트**
   - `Precedent` 테이블에 `link` 필드 추가
   - `LawArticle` 모델에 `Law`와의 관계 설정 추가

2. **법률 상담 서비스 개선**
   - `_save_law` 메서드: 법령 링크 저장 기능 개선
   - `_save_precedent` 메서드: 판례 링크 저장 기능 추가
   - `_generate_detailed_consultation` 메서드: 링크 정보 포함하여 상담 답변 생성

3. **Claude API 프롬프트 개선**
   - 법령 및 판례 링크 정보를 포함하여 더 풍부한 정보 제공
   - 상담 답변에 참고 자료 섹션 추가
   - 원문 링크 안내 문구 추가

## 적용 방법

1. 코드 업데이트 후 데이터베이스 마이그레이션 실행:
   ```
   python -m app.db.run_migration app/db/migrations/add_link_to_precedent.sql
   ```
   또는 제공된 배치 파일/쉘 스크립트 실행:
   - Windows: `run_link_migration.bat`
   - Linux/Mac: `sh run_link_migration.sh`

2. 서버 재시작

## 기대 효과

- 사용자가 법령 및 판례 원문을 직접 확인할 수 있어 정보의 신뢰성 향상
- 상담 답변의 품질 개선 및 정보 제공 범위 확대
- 법률 상담의 투명성 및 접근성 향상
