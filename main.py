import os
import asyncio
from bot.client import AkariBot
from bot.config import TOKEN
from web.app import start_web_server
from bot.database import init_db

def main():
    # 1. 데이터베이스 테이블 초기화 (Supabase)
    init_db()

    # 2. Flask 웹 서버를 별도 스레드에서 실행 (UptimeRobot용)
    print("🌍 [Web] Flask 서버 시작 중...")
    start_web_server()

    # 3. 디스코드 봇 실행
    if not TOKEN:
        print("❌ [Error] DISCORD_TOKEN이 설정되지 않았습니다.")
        return

    bot = AkariBot()
    print("🚀 [Bot] 아카리 기동 시퀀스 시작...")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()