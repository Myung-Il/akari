import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """DB에 연결합니다 (봇 켜질 때 1번 실행)"""
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
        """필요한 테이블을 자동으로 생성합니다. (초기화 버전)"""
        queries = [
            # 1. 유저 테이블
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                money BIGINT DEFAULT 3000,
                rank_id INTEGER DEFAULT 0,
                exp BIGINT DEFAULT 0,
                location VARCHAR(50) DEFAULT 'LOC_001',
                unlocked_plots INTEGER DEFAULT 1
            );
            """,
            # 2. 인벤토리 테이블 (count 컬럼 기본 포함!)
            """
            CREATE TABLE IF NOT EXISTS inventory (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                item_id VARCHAR(50),
                multiplier NUMERIC(4, 2) DEFAULT 1.0,
                count INTEGER DEFAULT 1,
                acquired_at TIMESTAMP DEFAULT NOW()
            );
            """,
            # 3. 텃밭 테이블
            """
            CREATE TABLE IF NOT EXISTS farm (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
                item_id VARCHAR(50),
                multiplier NUMERIC(4, 2),
                plant_time TIMESTAMP DEFAULT NOW()
            );
            """
        ]
        
        async with self.pool.acquire() as conn:
            for q in queries:
                await conn.execute(q)
        
        print("✅ 테이블 초기화/생성 완료 (새로운 설계도)")

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

# 전역 DB 객체 생성
db = Database()