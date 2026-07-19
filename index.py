import os
import asyncio
import threading
from bot.client import AkariBot
from bot.config import TOKEN

# Flask 서버 (기존 web/app.py가 있다면 그대로 import)
# 만약 파일이 없다면 아래 간단한 버전을 사용하세요.
# from web.app import start_web_server 

# ---------------------------------------------------------
# [복구] Flask 웹 서버 (UptimeRobot용)
# ---------------------------------------------------------
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run_flask():
    # Render 등에서는 포트 8080 등을 주로 사용합니다.
    app.run(host='0.0.0.0', port=8080)

def start_web_server():
    t = threading.Thread(target=run_flask)
    t.start()

# ---------------------------------------------------------
# [복구] 메인 실행 함수
# ---------------------------------------------------------
def main():
    # 1. Flask 웹 서버 실행 (별도 스레드)
    print("🌍 [Web] Flask 서버 시작 중...")
    start_web_server()

    # 2. 디스코드 봇 실행 준비
    if not TOKEN:
        print("❌ [Error] DISCORD_TOKEN이 설정되지 않았습니다.")
        return

    # 3. 봇 인스턴스 생성 및 실행
    # (DB 연결은 client.py나 garden.py에서 봇이 켜질 때 자동으로 수행됩니다)
    bot = AkariBot()
    print("🚀 [Bot] 아카리 기동 시퀀스 시작...")
    
    # bot.run()은 내부적으로 asyncio.run()을 호출하므로 
    # 별도의 asyncio.run(main()) 없이 여기서 바로 실행합니다.
    bot.run(TOKEN)

if __name__ == "__main__":
    main()