-- DB 마이그레이션 스크립트: aCase 테이블 필드 추가

-- 1. 기존 테이블 백업
CREATE TABLE IF NOT EXISTS aCase_backup AS SELECT * FROM aCase;

-- 2. 컬럼 존재 여부 체크 및 추가 (각 명령을 개별적으로 처리할 수 있도록 별도의 BEGIN/END 블록으로 구성)

-- title 컬럼 추가
ALTER TABLE aCase ADD COLUMN title VARCHAR(200) NULL;

-- claude_analysis 컬럼 추가
ALTER TABLE aCase ADD COLUMN claude_analysis TEXT NULL;

-- legal_category 컬럼 추가
ALTER TABLE aCase ADD COLUMN legal_category VARCHAR(100) NULL;

-- keywords 컬럼 추가
ALTER TABLE aCase ADD COLUMN keywords VARCHAR(500) NULL;

-- 3. 기존 데이터 업데이트 (필요한 경우)
-- UPDATE aCase SET title = '제목 없음' WHERE title IS NULL;
