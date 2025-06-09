# 링크 필드 마이그레이션 가이드

이 파일은 판례(Precedent) 테이블에 링크 필드를 추가하는 마이그레이션에 대한 안내입니다.

## 마이그레이션 개요

판례 상세 정보를 확인할 수 있는 링크 정보를 저장하기 위해 `Precedent` 테이블에 `link` 필드를 추가합니다.
이 필드는 판례의 원문을 확인할 수 있는 URL을 저장하여 사용자가 필요시 원본 판례를 직접 확인할 수 있도록 합니다.

## 마이그레이션 방법

다음 명령어를 실행하여 마이그레이션을 적용합니다:

### Windows

```
python -m app.db.run_migration app/db/migrations/add_link_to_precedent.sql
```

또는 배치 파일을 실행:

```
run_link_migration.bat
```

### Linux/Mac

```
python -m app.db.run_migration app/db/migrations/add_link_to_precedent.sql
```

또는 쉘 스크립트 실행:

```
sh run_link_migration.sh
```

## 마이그레이션 내용

마이그레이션은 다음 작업을 수행합니다:

1. `Precedent` 테이블에 `link` 텍스트 필드 추가

## 기대 효과

- 판례 원문 링크 제공으로 사용자의 법률 정보 접근성 향상
- Claude의 상담 답변에 링크 정보 포함하여 정보의 신뢰성 강화
- 법률 상담 시 관련 법령 및 판례의 상세 내용 확인 용이
