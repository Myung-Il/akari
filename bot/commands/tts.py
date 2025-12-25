import discord
from discord.ext import commands
from features.voice_service import text_to_mp3, delete_file
import os  # os 모듈이 필요합니다!

class TTS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ... (join, leave 명령어는 그대로) ...

    @commands.command(name="say", aliases=["말해"])
    async def say(self, ctx, *, text: str):
        """메시지를 읽어줍니다."""
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("❌ 봇이 음성 채널에 없어요. `!join` 먼저 해주세요.")
                return

        mp3_path = None # 변수 미리 선언 (에러 처리 안전장치)

        try:
            # 1. MP3 파일 생성
            mp3_path = text_to_mp3(text)

            # 2. [수정됨] 로컬 FFmpeg 경로 지정
            # 현재 실행 위치(main.py가 있는 곳) 기준 bin/ffmpeg.exe를 찾습니다.
            ffmpeg_executable = os.path.abspath("bin/ffmpeg.exe")

            # 파일이 진짜 있는지 확인 (디버깅용)
            if not os.path.exists(ffmpeg_executable):
                await ctx.send("❌ 설정 오류: ffmpeg.exe 파일을 찾을 수 없어요!")
                return

            # 3. 재생 (executable 옵션 추가)
            source = discord.FFmpegPCMAudio(mp3_path, executable=ffmpeg_executable)
            
            ctx.voice_client.play(source, after=lambda e: delete_file(mp3_path))
            
            await ctx.message.add_reaction("🗣️")

        except Exception as e:
            await ctx.send(f"❌ 오류가 발생했어요: {e}")
            if mp3_path:
                delete_file(mp3_path)

async def setup(bot):
    await bot.add_cog(TTS(bot))