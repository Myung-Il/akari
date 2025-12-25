import discord
from discord import app_commands
from discord.ext import commands
from features.voice_service import text_to_mp3, delete_file
import os
import platform

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. 봇 접속 (기존 동일)
    @app_commands.command(name="join", description="아카리를 현재 음성 채널로 부릅니다.")
    async def join(self, interaction: discord.Interaction):
        if interaction.user.voice:
            channel = interaction.user.voice.channel
            voice_client = interaction.guild.voice_client

            if voice_client:
                await voice_client.move_to(channel)
            else:
                await channel.connect()
            
            await interaction.response.send_message(f"🔊 **{channel.name}**에 도착했습니다! 이제 채팅을 읽어드릴게요.")
        else:
            await interaction.response.send_message("❌ 먼저 음성 채널에 들어가주세요.", ephemeral=True)

    # 2. 봇 퇴장 (기존 동일)
    @app_commands.command(name="leave", description="아카리를 음성 채널에서 내보냅니다.")
    async def leave(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client:
            await voice_client.disconnect()
            await interaction.response.send_message("👋 안녕히 계세요!")
        else:
            await interaction.response.send_message("❌ 저는 지금 아무 곳에도 없어요.", ephemeral=True)

    # ==========================================
    # 🌟 [핵심 기능] 채팅 자동 감지 및 읽기
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message):
        # 1. 봇 자신의 메시지는 무시
        if message.author.bot:
            return

        # 2. 봇이 이 서버의 음성 채널에 들어가 있는지 확인
        voice_client = message.guild.voice_client
        if not voice_client or not voice_client.is_connected():
            return  # 봇이 음성방에 없으면 그냥 무시 (아무것도 안 함)

        # 3. 메시지 내용이 있는지 확인 (이미지만 보낸 경우 제외)
        if not message.content:
            return

        # 4. 명령어가 아닌 경우에만 읽기 (!ping 같은 거 읽으면 이상하니까)
        if message.content.startswith("!") or message.content.startswith("/"):
            return

        # 5. TTS 재생 함수 호출
        # (채팅 채널에는 별도 반응 없이 소리만 냅니다)
        await self.play_tts(voice_client, message.content, None)

    # ==========================================
    # 🔊 공통 재생 함수
    # ==========================================
    async def play_tts(self, voice_client, text, interaction=None):
        mp3_path = None
        try:
            if voice_client.is_playing():
                voice_client.stop()

            mp3_path = text_to_mp3(text)
            
            # [수정됨] OS에 따라 알맞은 FFmpeg 선택
            if platform.system() == "Windows":
                ffmpeg_executable = os.path.abspath("bin/ffmpeg.exe")
            else:
                # Render(Linux) 환경
                ffmpeg_executable = os.path.abspath("bin/ffmpeg")
            
            # 파일이 진짜 있는지 확인
            if not os.path.exists(ffmpeg_executable):
                raise FileNotFoundError(f"FFmpeg 파일을 찾을 수 없습니다: {ffmpeg_executable}")

            source = discord.FFmpegPCMAudio(mp3_path, executable=ffmpeg_executable)
            voice_client.play(source, after=lambda e: delete_file(mp3_path))
            
            if interaction:
                await interaction.followup.send(f"🗣️ **말하는 중:** {text}")

        except Exception as e:
            print(f"TTS 오류: {e}")
            if interaction:
                await interaction.followup.send(f"❌ 오류: {e}")
            if mp3_path:
                delete_file(mp3_path)

async def setup(bot):
    await bot.add_cog(TTS(bot))