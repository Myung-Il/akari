import os
import psycopg2
from dotenv import load_dotenv

load_dotenv() # 로컬에서 .env 로드용

def get_db_connection():
    """데이터베이스 연결 객체를 반환합니다."""
    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL 환경변수가 없습니다!")
        return None
    
    try:
        conn = psycopg2.connect(url)
        return conn
    except Exception as e:
        print(f"❌ DB 연결 실패: {e}")
        return None

def init_db():
    """테이블이 없으면 생성합니다 (봇 켜질 때 실행)."""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        
        # [MySQL 지식 활용] SQL 문법은 99% 똑같습니다!
        # 예시: 유저의 레벨을 저장하는 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_levels (
                user_id BIGINT PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            );
        """)
        
        conn.commit()
        print("✅ 데이터베이스 초기화 완료 (Supabase)")
        
    except Exception as e:
        print(f"❌ 테이블 생성 오류: {e}")
    finally:
        conn.close()