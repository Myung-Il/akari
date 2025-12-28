import discord
from discord.ext import commands
from discord import app_commands
import random

# --- 설정 및 상수 (마인크래프트 테마) ---
MAX_SLOTS = 10
START_CHANCE = 75
MIN_CHANCE = 25
MAX_CHANCE = 75

POSITIVE_OPTIONS = [
    "날카로움", "내구성", "강타", "살충", "발화", 
    "수선", "밀치기", "약탈", "행운", "효율"
]
NEGATIVE_OPTIONS = [
    "소실저주", "귀속저주", "무뎌짐", "부식", "약화", 
    "채굴피로", "속도감소", "나약함"
]

class Weapon:
    def __init__(self):
        self.tier = "일반"
        self.lines = [
            {"name": random.choice(POSITIVE_OPTIONS), "slots": ["◇"] * MAX_SLOTS, "success_count": 0, "type": "positive"},
            {"name": random.choice(POSITIVE_OPTIONS), "slots": ["◇"] * MAX_SLOTS, "success_count": 0, "type": "positive"},
            {"name": random.choice(NEGATIVE_OPTIONS), "slots": ["◇"] * MAX_SLOTS, "success_count": 0, "type": "negative"}
        ]
        self.probability = START_CHANCE
        self.attempts = 0
        self.max_attempts = MAX_SLOTS * 3
        self.finished_phase_1 = False

    def try_facet(self, line_idx):
        if self.lines[line_idx]["slots"][-1] != "◇":
            return False, "이미 완료된 옵션입니다!"

        current_idx = self.lines[line_idx]["slots"].index("◇")
        success = False
        roll = random.uniform(0, 100)
        
        # 성공 판정
        if roll < self.probability:
            self.lines[line_idx]["slots"][current_idx] = "◆"
            self.lines[line_idx]["success_count"] += 1
            self.probability = max(MIN_CHANCE, self.probability - 10)
            success = True
            msg = "성공!"
        else:
            self.lines[line_idx]["slots"][current_idx] = "X"
            self.probability = min(MAX_CHANCE, self.probability + 10)
            success = False
            msg = "실패..."
        
        self.attempts += 1
        if self.attempts >= self.max_attempts:
            self.finished_phase_1 = True
            
        return True, msg

# ---------------------------------------------------------
# 게임 UI (View)
# ---------------------------------------------------------
class SmithGameView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.weapon = Weapon()
        self.phase = 1 # 1: 세공, 2: 강화, 3: 종료
        self.log_msg = "아카리: 무기를 올려주세요! 인챈트부터 시작할게요."
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        if self.phase == 1:
            # 세공 단계 버튼
            for i in range(3):
                label = f"{self.weapon.lines[i]['name']} ({self.weapon.probability}%)"
                style = discord.ButtonStyle.primary if self.weapon.lines[i]['type'] == 'positive' else discord.ButtonStyle.danger
                
                # 비활성화 조건: 이미 다 찼거나, 게임이 끝났거나
                disabled = self.weapon.lines[i]["slots"][-1] != "◇"
                
                btn = discord.ui.Button(label=label, style=style, custom_id=str(i), row=i, disabled=disabled)
                btn.callback = self.make_callback(i)
                self.add_item(btn)
            
            # 다음 단계 버튼 (모든 세공이 끝났을 때 활성화)
            if self.weapon.finished_phase_1:
                next_btn = discord.ui.Button(label="강화 단계로 이동", style=discord.ButtonStyle.success, row=3, emoji="🔨")
                next_btn.callback = self.go_to_phase_2
                self.add_item(next_btn)

        elif self.phase == 2:
            # 강화 단계 버튼
            enhance_btn = discord.ui.Button(label="두들기기 (강화)", style=discord.ButtonStyle.danger, emoji="🔥")
            enhance_btn.callback = self.try_enhance
            self.add_item(enhance_btn)
            
            stop_btn = discord.ui.Button(label="여기서 멈추기", style=discord.ButtonStyle.secondary, emoji="🛑")
            stop_btn.callback = self.stop_game
            self.add_item(stop_btn)

    def make_callback(self, idx):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id: return
            
            result, msg = self.weapon.try_facet(idx)
            if result:
                line_name = self.weapon.lines[idx]['name']
                self.log_msg = f"🔨 **{line_name}**: {msg}"
            
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        return callback

    async def go_to_phase_2(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: return
        self.phase = 2
        self.log_msg = "아카리: 이제 모루에서 무기 등급을 올릴 차례예요!"
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def try_enhance(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: return
        
        tiers = ["일반", "희귀", "영웅", "전설"]
        current_idx = tiers.index(self.weapon.tier)
        
        if current_idx >= 3:
            self.log_msg = "이미 전설 등급입니다!"
            return await interaction.response.edit_message(embed=self.get_embed(), view=self)

        next_tier = tiers[current_idx + 1]
        chance_map = {"희귀": 50, "영웅": 40, "전설": 30}
        chance = chance_map[next_tier]
        
        roll = random.uniform(0, 100)
        if roll < chance:
            self.weapon.tier = next_tier
            self.log_msg = f"🎉 **대성공!** {next_tier} 등급이 되었습니다!"
            if next_tier == "전설":
                self.phase = 3 # 게임 종료 (클리어)
                self.clear_items()
                self.log_msg = "🌟 **축하합니다! 전설의 무기가 탄생했습니다!** 🌟"
        else:
            self.phase = 3 # 게임 종료 (파괴)
            self.weapon.tier = "파괴됨"
            self.clear_items()
            self.log_msg = "💔 **콰창!** 무기가 산산조각 났습니다..."

        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def stop_game(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: return
        self.phase = 3
        self.clear_items()
        self.log_msg = "안전하게 작업을 마쳤습니다."
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def get_embed(self):
        color = discord.Color.purple() if self.phase < 3 else (discord.Color.green() if self.weapon.tier != "파괴됨" else discord.Color.red())
        embed = discord.Embed(title="⚒️ 아카리의 대장간", description=self.log_msg, color=color)
        
        # 상단 정보
        info = f"**현재 등급:** {self.weapon.tier}\n"
        if self.phase == 1:
            info += f"**성공 확률:** {self.weapon.probability}%\n"
        elif self.phase == 2:
            info += "**강화 단계 진입! 파괴 주의!**\n"
        embed.add_field(name="상태", value=info, inline=False)

        # 슬롯 렌더링
        msg = ""
        for line in self.weapon.lines:
            # 이모지 매핑 (긍정: 파랑/회색, 부정: 빨강/초록)
            if line['type'] == 'positive':
                slots = "".join(["🟦" if s == "◆" else ("⬛" if s == "X" else "⬜") for s in line['slots']])
            else:
                slots = "".join(["🟥" if s == "◆" else ("🟩" if s == "X" else "⬜") for s in line['slots']])
            
            msg += f"**{line['name']}** (+{line['success_count']})\n{slots}\n\n"
        
        embed.add_field(name="인챈트 현황", value=msg, inline=False)
        return embed

# ---------------------------------------------------------
# Cog 등록
# ---------------------------------------------------------
class Smith(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="무기강화", description="아카리의 대장간에서 무기를 만들고 강화합니다.")
    async def smith_game(self, interaction: discord.Interaction):
        view = SmithGameView(interaction.user.id)
        await interaction.response.send_message(embed=view.get_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Smith(bot))