import discord
from discord.ext import commands
from bot.config import INTENTS_FLAGS
from bot.database import db  # <--- [중요] DB 객체 가져오기

class AkariBot(commands.Bot):
    def __init__(self):
        # 1. 권한 설정
        intents = discord.Intents.default()
        intents.members = INTENTS_FLAGS["members"]
        intents.message_content = INTENTS_FLAGS["message_content"]
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # ---------------------------------------------------------
        # [핵심] 봇이 켜질 때 DB에 연결합니다.
        # ---------------------------------------------------------
        print("🔌 [DB] 데이터베이스 연결 시도 중...")
        await db.connect() 

        # 기능(Cog) 로드
        extensions = [
            "bot.commands.ping",
            "bot.commands.tts",
            "features.garden"
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ [Load] {ext} 로드 성공")
            except Exception as e:
                print(f"❌ [Error] {ext} 로드 실패: {e}")
        
        # 슬래시 커맨드 동기화
        try:
            synced = await self.tree.sync()
            print(f"✨ [Sync] 슬래시 커맨드 {len(synced)}개 동기화 완료")
        except Exception as e:
            print(f"❌ [Error] 커맨드 동기화 실패: {e}")

    async def on_ready(self):
        print(f"✅ [Online] {self.user} 로그인 완료 (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="약초 키우기"))