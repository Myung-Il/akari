import os
import asyncio
from bot.client import AkariBot # 경로 주의
from bot.config import TOKEN    # 경로 주의
from bot.database import db     # 방금 만든 database.py import

async def main():
    # 1. 데이터베이스 연결 (비동기)
    await db.connect()

    # 2. 봇 실행
    bot = AkariBot()
    
    if not TOKEN:
        print("❌ 토큰이 없습니다. .env를 확인하세요.")
        return
        
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 강제 종료 시 깔끔하게 끄기
        print("봇을 종료합니다.")