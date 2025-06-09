@echo off
REM 법령 및 판례 테이블 마이그레이션 실행 스크립트 (Windows용)

echo 법령 및 판례 테이블 마이그레이션을 시작합니다...

REM 마이그레이션 스크립트 실행
python -m app.db.run_migration app/db/migrations/add_law_and_precedent_tables.sql

echo 마이그레이션이 완료되었습니다.
pause
