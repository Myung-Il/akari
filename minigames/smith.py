import discord
from discord.ext import commands
from discord import app_commands
import random

# --- 설정 및 상수 ---
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
        self.tier_multiplier = 1
        # [이름, 슬롯리스트, 성공횟수, 타입]
        self.lines = [
            {"name": random.choice(POSITIVE_OPTIONS), "slots": ["◇"] * MAX_SLOTS, "success_count": 0, "type": "positive_1"}, # 1번줄 (x2점)
            {"name": random.choice(POSITIVE_OPTIONS), "slots": ["◇"] * MAX_SLOTS, "success_count": 0, "type": "positive_2"}, # 2번줄 (x1점)
            {"name": random.choice(NEGATIVE_OPTIONS), "slots": ["◇"] * MAX_SLOTS, "success_count": 0, "type": "negative"}     # 3번줄 (-1점)
        ]
        self.probability = START_CHANCE
        self.attempts = 0
        self.max_attempts = MAX_SLOTS * 3
        self.finished_phase_1 = False

    def get_base_score(self):
        # 공식: (1번성공 * 2) + (2번성공) - (3번성공:실패로 간주)
        s1 = self.lines[0]["success_count"]
        s2 = self.lines[1]["success_count"]
        s3 = self.lines[2]["success_count"] # 부정 옵션이 활성화된 횟수
        return (s1 * 2) + s2 - s3

    def get_total_score(self):
        return self.get_base_score() * self.tier_multiplier

    def try_facet(self, line_idx):
        if self.lines[line_idx]["slots"][-1] != "◇":
            return False, "이미 완료된 옵션입니다!"

        current_idx = self.lines[line_idx]["slots"].index("◇")
        success = False
        roll = random.uniform(0, 100)
        
        # 성공 판정
        if roll < self.probability:
            # 성공 (확률 감소)
            self.lines[line_idx]["slots"][current_idx] = "HIT"
            self.lines[line_idx]["success_count"] += 1
            self.probability = max(MIN_CHANCE, self.probability - 10)
            success = True
            
            if self.lines[line_idx]['type'] == 'negative':
                msg = "저주 활성화! (-1점)"
            else:
                pts = 2 if line_idx == 0 else 1
                msg = f"성공! (+{pts}점)"
        else:
            # 실패 (확률 증가)
            self.lines[line_idx]["slots"][current_idx] = "MISS"
            self.probability = min(MAX_CHANCE, self.probability + 10)
            success = False
            
            if self.lines[line_idx]['type'] == 'negative':
                msg = "저주 회피! (다행이다!)"
            else:
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
        self.log_msg = "아카리: 인챈트(세공)를 시작해볼까요?"
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        
        if self.phase == 1:
            # 세공 버튼
            for i in range(3):
                line = self.weapon.lines[i]
                
                # 라벨에 점수 정보 표시
                if i == 0: info = "(성공시 +2점)"
                elif i == 1: info = "(성공시 +1점)"
                else: info = "(활성시 -1점)"
                
                label = f"{line['name']} {info} [{self.weapon.probability}%]"
                
                # 색상: 긍정=파랑, 부정=빨강
                style = discord.ButtonStyle.primary if i < 2 else discord.ButtonStyle.danger
                
                disabled = line["slots"][-1] != "◇"
                
                btn = discord.ui.Button(label=label, style=style, custom_id=str(i), row=i, disabled=disabled)
                btn.callback = self.make_callback(i)
                self.add_item(btn)
            
            # 다음 단계 버튼
            if self.weapon.finished_phase_1:
                score = self.weapon.get_base_score()
                next_btn = discord.ui.Button(label=f"강화 단계로 이동 (현재 점수: {score})", style=discord.ButtonStyle.success, row=3, emoji="🔨")
                next_btn.callback = self.go_to_phase_2
                self.add_item(next_btn)

        elif self.phase == 2:
            # 현재 등급에 따른 다음 강화 확률과 배율
            tiers_info = {
                "일반": {"next": "희귀", "chance": 50, "mult": 2},
                "희귀": {"next": "영웅", "chance": 40, "mult": 4},
                "영웅": {"next": "전설", "chance": 30, "mult": 8},
                "전설": {"next": "END", "chance": 0, "mult": 8}
            }
            
            current_info = tiers_info.get(self.weapon.tier)
            
            if current_info and current_info["next"] != "END":
                next_tier = current_info["next"]
                chance = current_info["chance"]
                next_mult = current_info["mult"]
                
                btn_label = f"{next_tier} 강화 도전! (확률: {chance}%)"
                enhance_btn = discord.ui.Button(label=btn_label, style=discord.ButtonStyle.danger, emoji="🔥")
                enhance_btn.callback = self.try_enhance
                self.add_item(enhance_btn)
                
                stop_btn = discord.ui.Button(label=f"여기서 멈추기 (현재 {self.weapon.tier_multiplier}배)", style=discord.ButtonStyle.secondary, emoji="🛑")
                stop_btn.callback = self.stop_game
                self.add_item(stop_btn)
            else:
                # 전설 달성 시 종료 버튼만
                finish_btn = discord.ui.Button(label="전설의 무기 완성!", style=discord.ButtonStyle.success)
                finish_btn.callback = self.stop_game
                self.add_item(finish_btn)

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
        self.log_msg = "아카리: 이제 무기를 강화해서 점수를 뻥튀기해봐요!"
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def try_enhance(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: return
        
        tiers_map = ["일반", "희귀", "영웅", "전설"]
        if self.weapon.tier not in tiers_map: return

        idx = tiers_map.index(self.weapon.tier)
        if idx >= 3: return

        # 확률 설정
        chance_map = {"일반": 50, "희귀": 40, "영웅": 30}
        chance = chance_map[self.weapon.tier]
        
        roll = random.uniform(0, 100)
        
        if roll < chance:
            # 성공 로직
            next_tier = tiers_map[idx + 1]
            self.weapon.tier = next_tier
            
            # 배율 설정 (2배씩 증가)
            mult_map = {"희귀": 2, "영웅": 4, "전설": 8}
            self.weapon.tier_multiplier = mult_map[next_tier]
            
            self.log_msg = f"🎉 **강화 성공!** {next_tier} 등급이 되었습니다! (점수 x{self.weapon.tier_multiplier})"
            if next_tier == "전설":
                self.log_msg += "\n🌟 전설의 경지에 도달했습니다!"
                self.phase = 3 # 종료
                self.clear_items()
        else:
            # 실패 로직
            self.phase = 3 # 종료
            self.weapon.tier = "파괴됨"
            self.weapon.tier_multiplier = 0 # 파괴되면 점수 0
            self.clear_items()
            self.log_msg = "💔 **콰창!** 강화에 실패하여 무기가 파괴되었습니다..."

        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def stop_game(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: return
        self.phase = 3
        self.clear_items()
        self.log_msg = "강화를 마쳤습니다. 수고하셨어요!"
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    def get_embed(self):
        # 색상: 파괴됨(빨강), 완료(보라), 진행중(초록)
        if self.weapon.tier == "파괴됨": color = discord.Color.red()
        elif self.phase == 3: color = discord.Color.purple()
        else: color = discord.Color.green()

        embed = discord.Embed(title="⚒️ 아카리의 대장간", description=self.log_msg, color=color)
        
        # 1. 점수 현황판
        base_score = self.weapon.get_base_score()
        total_score = self.weapon.get_total_score()
        
        score_info = f"기본 점수: **{base_score}점**"
        if self.weapon.tier_multiplier > 1:
            score_info += f" × 배율 **{self.weapon.tier_multiplier}** (등급: {self.weapon.tier})"
        score_info += f"\n🏆 **최종 점수: {total_score}점**"
        
        embed.add_field(name="📊 점수 현황", value=score_info, inline=False)

        # 2. 인챈트 슬롯 시각화 (가시성 개선)
        slots_display = ""
        for i, line in enumerate(self.weapon.lines):
            line_str = ""
            for s in line['slots']:
                if i < 2: # 긍정 옵션 (1, 2번줄)
                    if s == "HIT": line_str += "🟦" # 성공 (파랑)
                    elif s == "MISS": line_str += "⬛" # 실패 (검정/회색)
                    else: line_str += "⬜" # 미진행
                else: # 부정 옵션 (3번줄)
                    if s == "HIT": line_str += "🟥" # 저주 활성화 (빨강 - 나쁨)
                    elif s == "MISS": line_str += "⬛" # 저주 회피 (방패 - 좋음)
                    else: line_str += "⬜"
            
            # 줄 이름과 설명
            if i == 0: desc = "**(성공 x2)**"
            elif i == 1: desc = "**(성공 x1)**"
            else: desc = "**(활성 -1)**"
            
            slots_display += f"**{line['name']}** {desc}\n{line_str}\n"

        embed.add_field(name="💎 인챈트 세공", value=slots_display, inline=False)
        
        # 3. 강화 정보 (2단계일 때만 표시)
        if self.phase == 2:
            next_tiers = {"일반": "희귀 (50%)", "희귀": "영웅 (40%)", "영웅": "전설 (30%)"}
            if self.weapon.tier in next_tiers:
                embed.add_field(name="🔥 강화 정보", value=f"다음 단계: **{next_tiers[self.weapon.tier]}**\n성공 시 점수 2배!", inline=False)

        return embed

# ---------------------------------------------------------
# Cog 등록
# ---------------------------------------------------------
class Smith(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="무기강화", description="아카리와 함께 무기를 만들고 점수를 획득하세요!")
    async def smith_game(self, interaction: discord.Interaction):
        view = SmithGameView(interaction.user.id)
        await interaction.response.send_message(embed=view.get_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Smith(bot))