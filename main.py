import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from bot.database import db  # 우리가 만든 database.py 불러오기

# 1. 환경 변수 로드
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 2. 봇 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class AkariBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # (1) DB 연결
        await db.connect()
        
        # (2) 기능(Extension) 로드
        initial_extensions = [
            'features.garden', # RPG 게임
            'bot.commands.ping', # 핑
            'bot.commands.tts' # TTS
        ]

        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ 기능 로드 완료: {ext}")
            except Exception as e:
                print(f"❌ 기능 로드 실패 ({ext}): {e}")

        # (3) 명령어 동기화
        await self.tree.sync()
        print("✅ 슬래시 커맨드 동기화 완료")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

async def main():
    bot = AkariBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ .env 파일에 DISCORD_TOKEN이 없습니다!")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            # 강제 종료 시(Ctrl+C) 깔끔하게 닫기
            pass