import discord
from discord.ext import commands
from bot.config import INTENTS_FLAGS

MY_GUILD = discord.Object(id=1018709014835626125)

class AkariBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = INTENTS_FLAGS["members"]
        intents.message_content = INTENTS_FLAGS["message_content"]
        
        super().__init__(
            command_prefix="!", # 슬래시 커맨드를 써도 prefix는 유지하는 게 좋습니다.
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # 1. Cog(기능) 로드
        await self.load_extension("bot.commands.ping")
        await self.load_extension("bot.commands.tts")
        
        # 2. 슬래시 커맨드 동기화 (전역)
        # 주의: 전역 동기화는 디스코드 서버에 반영되기까지 최대 1시간이 걸릴 수 있습니다.
        # 개발 중에는 특정 서버 ID를 지정해서 동기화하는 것이 빠르지만, 
        # 일단 편의를 위해 전역 동기화로 설정합니다.
        try:
            synced = await self.tree.sync()
            print(f"✨ [Bot] 슬래시 커맨드 {len(synced)}개 동기화 완료!")
        except Exception as e:
            print(f"❌ [Error] 커맨드 동기화 실패: {e}")

        print(f"✨ [Bot] {self.user} (Akari) 설정 완료!")

    async def on_ready(self):
        print(f"✅ [Bot] {self.user} 온라인! ID: {self.user.id}")
        await self.change_presence(activity=discord.Game(name="테스트 중"))