import discord
from discord import app_commands
from discord.ext import commands

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @app_commands.command 데코레이터를 사용합니다.
    @app_commands.command(name="ping", description="아카리의 응답 속도를 확인합니다.")
    async def ping(self, interaction: discord.Interaction):
        # ctx.send 대신 interaction.response.send_message를 사용합니다.
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 퐁! 아카리는 깨어있어요! ({latency}ms)")

async def setup(bot):
    await bot.add_cog(Ping(bot))