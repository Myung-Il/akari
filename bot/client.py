import discord
from discord.ext import commands
from bot.config import INTENTS_FLAGS

class AkariBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = INTENTS_FLAGS["members"]
        intents.message_content = INTENTS_FLAGS["message_content"]
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # 기존 Cog
        await self.load_extension("bot.commands.ping")
        
        # [NEW] TTS 기능 추가!
        await self.load_extension("bot.commands.tts")
        
        print(f"✨ [Bot] {self.user} (Akari) 설정 완료!")

    async def on_ready(self):
        print(f"✅ [Bot] {self.user} 온라인! ID: {self.user.id}")
        await self.change_presence(activity=discord.Game(name="Render에서 호스팅 중 ☁️"))