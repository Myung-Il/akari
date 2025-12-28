import discord
from discord.ext import commands
import os
from bot.config import INTENTS_FLAGS

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
        # [복구] 기존 기능 (Ping, TTS) 로드
        # ※ 파일 위치가 bot/commands/ 폴더 안이라고 가정했습니다.
        # ---------------------------------------------------------
        extensions = [
            "bot.commands.ping",  # 핑 기능 복구
            "bot.commands.tts",   # TTS 기능 복구
            "features.garden"     # 텃밭/RPG 기능 (파일명 garden.py)
        ]

        for ext in extensions:
            try:
                await self.load_extension(ext)
                print(f"✅ [Load] {ext} 로드 성공")
            except Exception as e:
                print(f"❌ [Error] {ext} 로드 실패: {e}")
        
        # 2. 슬래시 커맨드 동기화
        try:
            synced = await self.tree.sync()
            print(f"✨ [Sync] 슬래시 커맨드 {len(synced)}개 동기화 완료")
        except Exception as e:
            print(f"❌ [Error] 커맨드 동기화 실패: {e}")

    async def on_ready(self):
        print(f"✅ [Online] {self.user} 로그인 완료 (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="아카리 봇 서비스 중"))