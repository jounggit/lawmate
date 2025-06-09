import pymysql
import os
import re
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# DATABASE_URL에서 데이터베이스 연결 정보 추출
def parse_database_url(url):
    """
    DATABASE_URL을 파싱하여 연결 정보를 추출합니다.
    예: mysql+pymysql://username:password@hostname/database
    """
    if not url:
        raise ValueError("DATABASE_URL 환경 변수가 설정되어 있지 않습니다.")
    
    # mysql+pymysql:// 부분 제거 (있는 경우)
    if "://" in url:
        url = url.split("://")[1]
    
    # 사용자 이름, 비밀번호, 호스트, 데이터베이스 이름 추출
    pattern = r"(.*?):(.*?)@(.*?)/(.*)"
    match = re.match(pattern, url)
    
    if not match:
        raise ValueError(f"DATABASE_URL 형식이 올바르지 않습니다: {url}")
    
    user, password, host, db_name = match.groups()
    
    return {
        "host": host,
        "user": user,
        "password": password,
        "database": db_name
    }

def execute_migration(sql_file_path):
    """
    SQL 마이그레이션 파일을 실행합니다.
    """
    # DATABASE_URL 환경 변수 사용
    database_url = os.getenv("DATABASE_URL")
    
    # 기존 개별 환경 변수 사용 (fallback)
    if not database_url:
        print("DATABASE_URL 환경 변수가 없습니다. 개별 DB 환경 변수를 사용합니다.")
        db_config = {
            "host": os.getenv("DB_HOST"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        }
    else:
        print(f"DATABASE_URL을 사용하여 데이터베이스에 연결합니다.")
        db_config = parse_database_url(database_url)
    
    conn = None
    cursor = None
    
    try:
        # 데이터베이스 연결 (pymysql 사용)
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print(f"데이터베이스 연결 성공: {db_config['database']}@{db_config['host']}")
        
        # SQL 파일 내용 읽기
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        
        # 세미콜론으로 쿼리 분리
        sql_commands = sql_script.split(';')
        
        # 각 쿼리 실행
        for command in sql_commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                    print(f"성공: {command[:50]}...")
                except pymysql.err.OperationalError as e:
                    # 컬럼이 이미 존재하는 경우 (1060: Duplicate column name) 무시
                    if e.args[0] == 1060:
                        column_name = re.search(r"ADD COLUMN (\w+)", command)
                        if column_name:
                            print(f"정보: 컬럼 '{column_name.group(1)}'이(가) 이미 존재합니다.")
                        else:
                            print(f"정보: 컬럼이 이미 존재합니다.")
                    else:
                        # 다른 오류는 출력
                        print(f"오류: {e}")
                        raise
                except Exception as e:
                    print(f"오류: {e}")
                    raise
        
        # 변경사항 커밋
        conn.commit()
        print(f"마이그레이션 성공: {sql_file_path}")
        
    except Exception as e:
        print(f"마이그레이션 오류: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    import sys
    
    # 커맨드 라인 인자에서 마이그레이션 파일 경로 가져오기
    if len(sys.argv) > 1:
        migration_file = sys.argv[1]
        print(f"지정된 마이그레이션 파일: {migration_file}")
    else:
        # 기본 마이그레이션 파일
        migration_file = "migrations/add_claude_analysis_to_acase.sql"
        print(f"기본 마이그레이션 파일 사용: {migration_file}")
    
    # 현재 스크립트의 경로를 기준으로 마이그레이션 파일 경로 구성
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 상대 경로일 경우 현재 디렉토리와 결합
    if not os.path.isabs(migration_file):
        full_path = os.path.join(current_dir, migration_file)
    else:
        full_path = migration_file
    
    # 파일 존재 확인
    if not os.path.exists(full_path):
        print(f"오류: 마이그레이션 파일을 찾을 수 없습니다: {full_path}")
        sys.exit(1)
    
    # 마이그레이션 실행
    execute_migration(full_path)
