#!/bin/bash
echo "판례 테이블에 링크 필드 추가 마이그레이션 실행 중..."

# 현재 스크립트 경로 확인
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 마이그레이션 파일 경로 지정
MIGRATION_FILE="$SCRIPT_DIR/app/db/migrations/add_link_to_precedent.sql"

python -m app.db.run_migration "$MIGRATION_FILE"

echo "마이그레이션 완료!"
