import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        url = os.getenv("DATABASE_URL")
        if not url:
            print("❌ DATABASE_URL 환경변수가 없습니다.")
            return

        try:
            self.pool = await asyncpg.create_pool(url)
            print("✅ PostgreSQL 연결 성공 (asyncpg)")
            await self.init_tables()
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")

    async def init_tables(self):
        # [수정] inventory 테이블에 count 컬럼 추가 (기존 테이블 호환)
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                money BIGINT DEFAULT 0,
                exp BIGINT DEFAULT 0,
                rank_id INTEGER DEFAULT 0,
                location VARCHAR(50) DEFAULT 'home',
                unlocked_plots INTEGER DEFAULT 1
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                item_id VARCHAR(50),
                multiplier NUMERIC(4, 2) DEFAULT 1.0,
                count INTEGER DEFAULT 1
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS farm (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                item_id VARCHAR(50),
                multiplier NUMERIC(4, 2),
                plant_time TIMESTAMP DEFAULT NOW()
            );
            """
        ]
        async with self.pool.acquire() as conn:
            for q in queries:
                await conn.execute(q)
            
            # [중요] 기존 DB를 쓰는 경우 count 컬럼이 없을 수 있으므로 강제 추가 시도
            try:
                await conn.execute("ALTER TABLE inventory ADD COLUMN IF NOT EXISTS count INTEGER DEFAULT 1;")
            except:
                pass # 이미 있으면 패스
                
        print("✅ 테이블 초기화 및 스키마 업데이트 완료")

    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

db = Database()