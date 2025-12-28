import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
import asyncio
from datetime import datetime
from bot.database import db

# ---------------------------------------------------------
# 데이터 관리 클래스
# ---------------------------------------------------------
class AlchemyManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlchemyManager, cls).__new__(cls)
            cls._instance.data = {}
            cls._instance.load_all_data()
        return cls._instance

    def load_all_data(self):
        files = {
            "items": "items.json",
            "locations": "locations.json",
            "levels": "levels.json",
            "config": "game_config.json",
            "facilities": "facilities.json"
        }
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        data_dir = os.path.join(root_dir, "data")

        for key, filename in files.items():
            file_path = os.path.join(data_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.data[key] = json.load(f)
                print(f"✅ 데이터 로드 성공: data/{filename}")
            except FileNotFoundError:
                print(f"❌ [Error] 파일을 찾을 수 없음: {file_path}")
                self.data[key] = {} 
            except json.JSONDecodeError:
                print(f"❌ [Error] JSON 형식이 잘못됨: {filename}")
                self.data[key] = {}

    def get_item(self, item_id: str):
        return self.data["items"].get(str(item_id))

    def get_location(self, loc_id: str):
        return self.data["locations"].get(loc_id)

# ---------------------------------------------------------
# 2. 탐사 세션 View (실제 게임 화면)
# ---------------------------------------------------------
class ExplorationSessionView(discord.ui.View):
    def __init__(self, cog, interaction, location, max_slots, cost):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = interaction.user.id
        self.location = location
        self.max_slots = max_slots
        self.cost = cost
        self.max_ap = 10
        self.current_ap = 10
        self.logs = []
        self.message = None
        self.active = True

    def _update_log(self, message):
        self.logs.append(message)
        if len(self.logs) > 5:
            self.logs.pop(0)

    def _get_embed(self):
        desc = f"📍 **{self.location['name']}** 탐사 중...\n(1분간 조작이 없으면 자동 환불됩니다)\n\n"
        if self.logs:
            desc += "📜 **탐사 로그**\n" + "\n".join(self.logs)
        else:
            desc += "탐사 버튼을 눌러 주변을 살펴보세요."
        
        embed = discord.Embed(title="🌲 탐사 모드", description=desc, color=discord.Color.green())
        embed.set_footer(text=f"⚡ 남은 행동력: {self.current_ap} / {self.max_ap}")
        return embed

    async def on_timeout(self):
        if not self.active: return

        if self.current_ap == self.max_ap:
            # AP를 안 썼으면 환불
            await db.execute("UPDATE users SET money = money + $1 WHERE user_id = $2", self.cost, self.user_id)
            
            refund_embed = discord.Embed(
                title="↩️ 탐사 비용 환불", 
                description=f"1분간 활동이 없어 취소되었습니다.\n입장료 **{self.cost}원**이 환불되었습니다.",
                color=discord.Color.gold()
            )
            if self.message:
                try: await self.message.edit(embed=refund_embed, view=None)
                except: pass
        else:
            if self.message:
                try: 
                    embed = discord.Embed(description="탐사 세션이 종료되었습니다.", color=discord.Color.dark_grey())
                    await self.message.edit(embed=embed, view=None)
                except: pass

    @discord.ui.button(label="🔍 탐사하기 (-1 AP)", style=discord.ButtonStyle.primary)
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("본인의 세션이 아닙니다.", ephemeral=True)
        
        if self.current_ap <= 0:
            return await interaction.response.send_message("행동력이 부족합니다.", ephemeral=True)

        self.current_ap -= 1
        
        probs = self.location.get("probabilities", {})
        
        # 함정 체크
        if random.uniform(0, 100) < probs.get("trap", 0):
            trap_msg = self.location.get("trap_msg", "함정에 걸려 시간을 허비했습니다.")
            self._update_log(f"🛑 **[함정]** {trap_msg}")
            self.current_ap = max(0, self.current_ap - 1)
        else:
            drop_items = self.location.get("drop_items", [])
            if drop_items:
                item_id = random.choice(drop_items)
                
                current_inv = await db.fetchval("SELECT COUNT(*) FROM inventory WHERE user_id = $1", self.user_id)
                
                if current_inv >= self.max_slots:
                    self._update_log("🎒 **[가방 가득 참]** 아이템을 발견했지만 버리고 왔습니다.")
                else:
                    await db.execute(
                        "INSERT INTO inventory (user_id, item_id, multiplier) VALUES ($1, $2, 1.0)",
                        self.user_id, item_id
                    )
                    item_info = self.cog.am.get_item(item_id)
                    name = item_info['name'] if item_info else f"알 수 없는 물건({item_id})"
                    self._update_log(f"📦 **획득:** {name}")
            else:
                self._update_log("💨 아무것도 찾지 못했습니다.")

        if self.current_ap <= 0:
            button.disabled = True
            button.label = "행동력 소진"
            self.active = False

        await interaction.response.edit_message(embed=self._get_embed(), view=self)

    @discord.ui.button(label="🏠 탐사 종료", style=discord.ButtonStyle.danger)
    async def abort_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        self.active = False
        self.stop()
        await interaction.response.edit_message(content="탐사를 마치고 돌아왔습니다.", embed=None, view=None)


# ---------------------------------------------------------
# 1. 지도 선택 View (여기서 지역을 고르고 입장료를 냅니다)
# ---------------------------------------------------------
class MapSelectionView(discord.ui.View):
    def __init__(self, cog, interaction):
        super().__init__(timeout=30)
        self.cog = cog
        self.user_id = interaction.user.id
        self.message = None
        
        # locations.json에 있는 모든 지역을 버튼으로 생성
        for loc_id, data in self.cog.am.data["locations"].items():
            cost = data.get("cost", 0)
            btn = discord.ui.Button(label=f"{data['name']} ({cost}원)", custom_id=loc_id, style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(loc_id, data) # 콜백 함수 연결
            self.add_item(btn)

    def make_callback(self, loc_id, loc_data):
        """버튼마다 고유한 동작을 심어주는 함수"""
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("본인의 명령어가 아닙니다.", ephemeral=True)

            # 1. 유저 정보 최신화
            user = await self.cog.get_user_stats(self.user_id)
            cost = loc_data.get("cost", 0)

            # 2. 돈 체크
            if user["money"] < cost:
                return await interaction.response.send_message(f"💸 돈이 부족합니다! ({cost}원 필요)", ephemeral=True)

            # 3. 결제 및 위치 업데이트 (DB)
            await db.execute("UPDATE users SET money = money - $1, location = $2 WHERE user_id = $3", cost, loc_id, self.user_id)
            
            # 4. 탐사 세션 시작 (화면 전환)
            max_bag = await self.cog.get_bag_capacity(user["rank_id"])
            session_view = ExplorationSessionView(self.cog, interaction, loc_data, max_bag, cost)
            
            # 5. 기존 '지도 선택' 메시지를 '탐사 화면'으로 수정
            await interaction.response.edit_message(embed=session_view._get_embed(), view=session_view)
            session_view.message = interaction.message # 타임아웃 처리를 위해 메시지 저장
            
            self.stop() # 지도 선택 View는 이제 종료
            
        return callback


# ---------------------------------------------------------
# 메인 코어
# ---------------------------------------------------------
class AlchemyRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.am = AlchemyManager()

    async def get_user_stats(self, user_id: int):
        user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user:
            await db.execute("INSERT INTO users (user_id) VALUES ($1)", user_id)
            user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return user

    async def get_bag_capacity(self, rank_idx: int):
        levels = self.am.data["levels"]
        if rank_idx >= len(levels): rank_idx = len(levels) - 1
        base = self.am.data["config"]["inventory_rules"]["base_bag_slots"]
        bonus = levels[rank_idx].get("bagSlotBonus", 0)
        return base + bonus

    # ------------------------------------------------------------------
    # [명령어] 탐사 (통합됨)
    # ------------------------------------------------------------------
    @app_commands.command(name="탐사", description="탐사할 지역을 선택하고 출발합니다.")
    async def explore(self, interaction: discord.Interaction):
        # 1. 먼저 지도(지역 선택 버튼들)를 보여줌
        view = MapSelectionView(self, interaction)
        
        embed = discord.Embed(title="🗺️ 탐사 지역 선택", description="어디로 떠나시겠습니까?\n지역마다 입장료와 나오는 아이템이 다릅니다.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view)

    # ------------------------------------------------------------------
    # [명령어] 텃밭 등 나머지 기능은 동일
    # ------------------------------------------------------------------
    @app_commands.command(name="텃밭", description="작물 현황을 확인하고 관리합니다.")
    async def farm_status(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        plots = await db.fetch("SELECT * FROM farm WHERE user_id = $1 ORDER BY plant_time", interaction.user.id)
        
        embed = discord.Embed(title="🌿 나의 텃밭", color=discord.Color.green())
        desc = f"보유 슬롯: {user['unlocked_plots']}개 (최대 3개)\n\n"
        
        now = datetime.now()
        can_harvest = False
        
        if not plots:
            desc += "🌱 현재 심겨진 작물이 없습니다.\n`/심기` 명령어로 작물을 심어보세요."
        else:
            for i, plot in enumerate(plots):
                item = self.am.get_item(plot['item_id'])
                name = item['name'] if item else "???"
                mult = float(plot['multiplier'])
                
                elapsed = (now - plot['plant_time']).total_seconds()
                remain = 600 - elapsed 
                
                if remain <= 0:
                    status = "✅ **수확 가능**"
                    can_harvest = True
                else:
                    status = f"⏳ {int(remain)}초 남음"
                
                desc += f"**[{i+1}] {name} (x{mult:.2f})** : {status}\n"

        embed.description = desc
        view = discord.ui.View()

        harvest_btn = discord.ui.Button(label="모두 수확", style=discord.ButtonStyle.success, disabled=(not can_harvest))
        harvest_btn.callback = self.harvest_callback
        view.add_item(harvest_btn)

        if user['unlocked_plots'] < 3:
            cost_map = {1: 3000, 2: 30000}
            next_cost = cost_map.get(user['unlocked_plots'], 999999)
            
            expand_btn = discord.ui.Button(label=f"슬롯 확장 ({next_cost}원)", style=discord.ButtonStyle.secondary)
            
            async def expand_callback(interaction: discord.Interaction):
                u = await self.get_user_stats(interaction.user.id)
                if u["money"] < next_cost:
                    return await interaction.response.send_message("돈이 부족합니다.", ephemeral=True)
                
                await db.execute("UPDATE users SET money = money - $1, unlocked_plots = unlocked_plots + 1 WHERE user_id = $2", next_cost, interaction.user.id)
                await interaction.response.send_message(f"🎉 텃밭을 확장했습니다! (현재 {u['unlocked_plots']+1}칸)", ephemeral=True)
            
            expand_btn.callback = expand_callback
            view.add_item(expand_btn)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="심기", description="가방에 있는 아이템을 텃밭에 심습니다.")
    @app_commands.describe(index="가방 몇 번째 아이템을 심을까요? (1번부터)")
    async def plant(self, interaction: discord.Interaction, index: int):
        user = await self.get_user_stats(interaction.user.id)
        
        current_plots = await db.fetchval("SELECT COUNT(*) FROM farm WHERE user_id = $1", interaction.user.id)
        if current_plots >= user['unlocked_plots']:
            return await interaction.response.send_message("텃밭 슬롯이 꽉 찼습니다.", ephemeral=True)

        real_index = index - 1
        if real_index < 0: return await interaction.response.send_message("1 이상의 숫자를 입력하세요.", ephemeral=True)
        
        item_row = await db.fetchrow(
            "SELECT * FROM inventory WHERE user_id = $1 ORDER BY id LIMIT 1 OFFSET $2", 
            interaction.user.id, real_index
        )
        
        if not item_row:
            return await interaction.response.send_message("해당 번호의 아이템이 없습니다.", ephemeral=True)

        await db.execute("DELETE FROM inventory WHERE id = $1", item_row['id'])
        await db.execute(
            "INSERT INTO farm (user_id, item_id, multiplier, plant_time) VALUES ($1, $2, $3, NOW())",
            interaction.user.id, item_row['item_id'], item_row['multiplier']
        )
        
        item_info = self.am.get_item(item_row['item_id'])
        name = item_info['name'] if item_info else "작물"
        
        await interaction.response.send_message(f"🌱 **{name}**을(를) 심었습니다. 10분 뒤 수확하세요.")

    async def harvest_callback(self, interaction: discord.Interaction):
        plots = await db.fetch("SELECT * FROM farm WHERE user_id = $1", interaction.user.id)
        now = datetime.now()
        
        logs = []
        total_exp = 0
        
        for plot in plots:
            elapsed = (now - plot['plant_time']).total_seconds()
            if elapsed < 600: continue

            item_info = self.am.get_item(plot['item_id'])
            name = item_info['name'] if item_info else "???"
            old_mult = float(plot['multiplier'])
            
            rand = random.random() * 100
            new_mult = old_mult
            status_msg = ""
            destroyed = False
            
            if rand < 50: 
                new_mult += 0.5
                status_msg = "📈 **상승!**"
            elif rand < 85: 
                status_msg = "➖ **유지**"
            elif rand < 95:
                new_mult = max(0.1, new_mult - 0.35)
                status_msg = "🔻 **하락**"
            else:
                destroyed = True
                status_msg = "💥 **파괴됨**"

            await db.execute("DELETE FROM farm WHERE id = $1", plot['id'])
            
            if not destroyed:
                await db.execute(
                    "INSERT INTO inventory (user_id, item_id, multiplier) VALUES ($1, $2, $3)",
                    interaction.user.id, plot['item_id'], new_mult
                )
                logs.append(f"{name}: {old_mult:.2f} -> {new_mult:.2f} ({status_msg})")
                total_exp += 2
            else:
                logs.append(f"{name}: ({status_msg})")

        if total_exp > 0:
            await db.execute("UPDATE users SET exp = exp + $1 WHERE user_id = $2", total_exp, interaction.user.id)

        if not logs:
            await interaction.response.send_message("수확할 작물이 없습니다.", ephemeral=True)
        else:
            await interaction.response.edit_message(content=f"🚜 **수확 완료** (EXP +{total_exp})\n" + "\n".join(logs), view=None, embed=None)

    @app_commands.command(name="가방", description="보유 아이템을 확인합니다.")
    async def inventory(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        max_bag = await self.get_bag_capacity(user["rank_id"])
        items = await db.fetch("SELECT * FROM inventory WHERE user_id = $1 ORDER BY id", interaction.user.id)
        
        embed = discord.Embed(title=f"🎒 {interaction.user.display_name}의 가방", color=discord.Color.blue())
        
        if not items:
            embed.description = "가방이 비어있습니다."
        else:
            lines = []
            for i, item in enumerate(items):
                info = self.am.get_item(item['item_id'])
                name = info['name'] if info else "???"
                price = info['price'] if info else 0
                mult = float(item['multiplier'])
                final_price = int(price * mult)
                
                lines.append(f"`{i+1}.` {name} (x{mult:.2f}) - 💰 {final_price}원")
            embed.description = "\n".join(lines)
            
        embed.set_footer(text=f"슬롯: {len(items)} / {max_bag} | 💰 {user['money']:,}원")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="판매", description="특정 아이템을 판매합니다.")
    async def sell(self, interaction: discord.Interaction, index: int):
        real_index = index - 1
        if real_index < 0: return await interaction.response.send_message("올바른 번호를 입력하세요.", ephemeral=True)

        item_row = await db.fetchrow(
            "SELECT * FROM inventory WHERE user_id = $1 ORDER BY id LIMIT 1 OFFSET $2",
            interaction.user.id, real_index
        )
        
        if not item_row:
            return await interaction.response.send_message("해당 번호의 아이템이 없습니다.", ephemeral=True)
            
        info = self.am.get_item(item_row['item_id'])
        base_price = info['price'] if info else 0
        final_price = int(base_price * float(item_row['multiplier']))
        
        await db.execute("DELETE FROM inventory WHERE id = $1", item_row['id'])
        await db.execute("UPDATE users SET money = money + $1 WHERE user_id = $2", final_price, interaction.user.id)
        
        name = info['name'] if info else "아이템"
        await interaction.response.send_message(f"💰 **{name}** 판매 완료! (+{final_price}원)")

async def setup(bot):
    await bot.add_cog(AlchemyRPG(bot))