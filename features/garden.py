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
# 데이터 관리 (JSON 로드 및 에러 방지)
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
            except Exception as e:
                # print(f"⚠️ {filename} 로드 실패: {e}") # 로그 너무 많으면 주석 처리
                self.data[key] = {} if key != "levels" else []

    def get_item(self, item_id: str):
        return self.data["items"].get(str(item_id))

    def get_level_info(self, rank_idx: int):
        levels = self.data.get("levels", [])
        if not levels: return {}
        if rank_idx >= len(levels): return levels[-1]
        return levels[rank_idx]

    def get_config(self, key, default=None):
        return self.data.get("config", {}).get(key, default)

# ---------------------------------------------------------
# [View 1] 탐사 세션
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
        if len(self.logs) > 5: self.logs.pop(0)

    def _get_embed(self):
        ap_bar = "🟩" * self.current_ap + "⬛" * (self.max_ap - self.current_ap)
        desc = f"📍 **{self.location['name']}**\n"
        desc += f"체력: {ap_bar} ({self.current_ap}/{self.max_ap})\n\n"
        desc += "📜 **탐사 로그**\n" + ("\n".join(self.logs) if self.logs else "탐사를 시작해주세요.")
        return discord.Embed(title="🌲 탐사 진행 중", description=desc, color=discord.Color.green())

    async def on_timeout(self):
        if not self.active: return
        if self.current_ap == self.max_ap:
            await db.execute("UPDATE users SET money = money + $1 WHERE user_id = $2", self.cost, self.user_id)
        if self.message:
            try: await self.message.edit(content="💤 탐사가 종료되었습니다.", view=None, embed=None)
            except: pass

    @discord.ui.button(label="수색하기", style=discord.ButtonStyle.primary, emoji="🔍")
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        if self.current_ap <= 0: return await interaction.response.send_message("체력이 부족합니다.", ephemeral=True)

        self.current_ap -= 1
        probs = self.location.get("probabilities", {})
        
        # 함정 확률 체크
        if random.uniform(0, 100) < probs.get("trap", 0):
            msg = self.location.get("trap_msg", "함정에 걸렸습니다!")
            self._update_log(f"💥 {msg}")
            self.current_ap = max(0, self.current_ap - 1)
        else:
            drop_items = self.location.get("drop_items", [])
            if drop_items:
                item_id = random.choice(drop_items)
                
                # [중첩 로직 적용]
                await self.cog.add_item_to_inventory(self.user_id, item_id)
                
                item = self.cog.am.get_item(item_id)
                name = item['name'] if item else "미확인 물체"
                self._update_log(f"📦 **{name}** 획득!")
            else:
                self._update_log("💨 허탕을 쳤습니다.")

        if self.current_ap <= 0:
            button.disabled = True
            button.label = "체력 소진"
            self.active = False
        
        await interaction.response.edit_message(embed=self._get_embed(), view=self)

    @discord.ui.button(label="돌아가기", style=discord.ButtonStyle.danger, emoji="🏠")
    async def abort(self, interaction, button):
        if interaction.user.id == self.user_id:
            self.active = False
            self.stop()
            await interaction.response.edit_message(content="🏠 마을로 귀환했습니다.", embed=None, view=None)

# ---------------------------------------------------------
# [View 2] 지도 선택
# ---------------------------------------------------------
class MapSelectionView(discord.ui.View):
    def __init__(self, cog, interaction, user_money):
        super().__init__(timeout=30)
        self.cog = cog
        self.user_id = interaction.user.id
        
        for loc_id, data in self.cog.am.data["locations"].items():
            cost = data.get("cost", 0)
            disabled = user_money < cost
            emoji = "🔒" if disabled else "🌲"
            label = f"{data['name']} ({cost:,}원)"
            
            btn = discord.ui.Button(label=label, custom_id=loc_id, disabled=disabled, emoji=emoji, style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(loc_id, data)
            self.add_item(btn)

    def make_callback(self, loc_id, loc_data):
        async def callback(interaction):
            if interaction.user.id != self.user_id: return
            user = await self.cog.get_user_stats(self.user_id)
            if user["money"] < loc_data["cost"]: 
                return await interaction.response.send_message("돈이 부족합니다.", ephemeral=True)
            
            await db.execute("UPDATE users SET money = money - $1 WHERE user_id = $2", loc_data["cost"], self.user_id)
            max_bag = await self.cog.get_bag_capacity(user["rank_id"])
            
            view = ExplorationSessionView(self.cog, interaction, loc_data, max_bag, loc_data["cost"])
            await interaction.response.edit_message(embed=view._get_embed(), view=view)
            view.message = interaction.message
        return callback

# ---------------------------------------------------------
# [View 3] 수확 선택지
# ---------------------------------------------------------
class HarvestChoiceView(discord.ui.View):
    def __init__(self, cog, user_id, harvested_items):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.items = harvested_items
        self.message = None

    async def on_timeout(self):
        if self.message:
            try: await self.message.edit(content="⏳ 시간 초과! 아이템이 가방으로 이동했습니다.", view=None, embed=None)
            except: pass
            for item in self.items:
                # [중첩 로직 적용]
                await self.cog.add_item_to_inventory(self.user_id, item['item_id'], item['multiplier'])

    @discord.ui.button(label="💰 모두 판매", style=discord.ButtonStyle.success)
    async def sell_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        total_price = 0
        details = []
        for item in self.items:
            info = self.cog.am.get_item(item['item_id'])
            base_price = info.get('price', 0) if info else 0
            final_price = int(base_price * item['multiplier'])
            total_price += final_price
            details.append(f"{item['name']} (x{item['multiplier']:.2f}) : +{final_price}원")

        await db.execute("UPDATE users SET money = money + $1 WHERE user_id = $2", total_price, self.user_id)
        
        embed = discord.Embed(title="💰 정산 완료", description="\n".join(details), color=discord.Color.gold())
        embed.set_footer(text=f"총 수익: {total_price:,}원")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="🌱 다시 심기", style=discord.ButtonStyle.primary)
    async def replant_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        user_stats = await self.cog.get_user_stats(self.user_id)
        current_plots = await db.fetchval("SELECT COUNT(*) FROM farm WHERE user_id = $1", self.user_id)
        
        if current_plots + len(self.items) > user_stats['unlocked_plots']:
            return await interaction.response.send_message("❌ 텃밭이 부족합니다. 나머지는 가방으로 갑니다.", ephemeral=True)

        for item in self.items:
            await db.execute("INSERT INTO farm (user_id, item_id, multiplier, plant_time) VALUES ($1, $2, $3, NOW())",
                             self.user_id, item['item_id'], item['multiplier'])
        
        embed = discord.Embed(title="🌱 재배 시작", description="다시 심었습니다. (10분 소요)", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

# ---------------------------------------------------------
# 메인 코어 기능
# ---------------------------------------------------------
class AlchemyRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.am = AlchemyManager()

    # -----------------------------------------------------
    # [핵심] 아이템 추가/감소 (중첩 제한 적용)
    # -----------------------------------------------------
    async def add_item_to_inventory(self, user_id, item_id, multiplier=1.0, amount=1):
        """
        아이템을 추가할 때, 최대 스택 크기(30)를 고려하여
        빈 공간을 채우거나 새 슬롯을 생성합니다.
        """
        # 설정에서 최대 스택 크기 가져오기 (기본값 30)
        config = self.am.get_config("inventory_rules", {})
        max_stack = config.get("max_stack_size", 30)

        # 1. '꽉 차지 않은' 기존 스택 찾기 (같은 아이템, 같은 배율)
        #    id 순으로 정렬하여 앞에서부터 채움
        existing_stacks = await db.fetch(
            """
            SELECT id, count FROM inventory 
            WHERE user_id=$1 AND item_id=$2 AND multiplier=$3 AND count < $4
            ORDER BY id
            """,
            user_id, item_id, multiplier, max_stack
        )

        for stack in existing_stacks:
            if amount <= 0: break
            
            current_count = stack['count']
            space = max_stack - current_count  # 남은 공간
            
            to_add = min(amount, space)  # 추가할 양
            
            await db.execute("UPDATE inventory SET count = count + $1 WHERE id = $2", to_add, stack['id'])
            amount -= to_add

        # 2. 남은 수량이 있다면 새 슬롯 생성 (30개씩 끊어서)
        while amount > 0:
            to_add = min(amount, max_stack)
            await db.execute(
                "INSERT INTO inventory (user_id, item_id, multiplier, count) VALUES ($1, $2, $3, $4)",
                user_id, item_id, multiplier, to_add
            )
            amount -= to_add

    async def remove_item_from_inventory(self, row_id, amount=1):
        """특정 슬롯(row_id)에서 아이템 개수 차감 또는 삭제"""
        await db.execute("UPDATE inventory SET count = count - $1 WHERE id = $2", amount, row_id)
        await db.execute("DELETE FROM inventory WHERE id = $1 AND count <= 0", row_id)

    async def get_user_stats(self, user_id: int):
        user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user:
            await db.execute("INSERT INTO users (user_id, unlocked_plots) VALUES ($1, 1)", user_id)
            user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return user

    async def get_bag_capacity(self, rank_idx: int):
        level_info = self.am.get_level_info(rank_idx)
        base = self.am.data.get("config", {}).get("inventory_rules", {}).get("base_bag_slots", 10)
        bonus = level_info.get("bagSlotBonus", 0)
        return base + bonus

    # -----------------------------------------------------
    # 명령어
    # -----------------------------------------------------
    @app_commands.command(name="판매", description="가방의 아이템을 판매합니다.")
    @app_commands.describe(index="아이템 번호", count="판매 개수")
    async def sell_item(self, interaction: discord.Interaction, index: int, count: int = 1):
        if index < 1 or count < 1: return await interaction.response.send_message("1 이상의 숫자를 입력하세요.", ephemeral=True)

        target_item = await db.fetchrow(
            "SELECT * FROM inventory WHERE user_id = $1 ORDER BY id LIMIT 1 OFFSET $2",
            interaction.user.id, index - 1
        )

        if not target_item: return await interaction.response.send_message("해당 번호에 아이템이 없습니다.", ephemeral=True)

        # 현재 슬롯의 보유량 확인
        current_count = target_item['count'] if target_item['count'] else 1
        
        # 요청 개수가 보유량보다 많으면 보유량만큼만 판매
        sell_amount = min(current_count, count)
        
        info = self.am.get_item(target_item['item_id'])
        base_price = info.get('price', 0) if info else 0
        total_price = int(base_price * float(target_item['multiplier']) * sell_amount)
        
        # 개수 차감
        await self.remove_item_from_inventory(target_item['id'], sell_amount)
        
        # 돈 지급
        await db.execute("UPDATE users SET money = money + $1 WHERE user_id = $2", total_price, interaction.user.id)

        item_name = info.get('name', '알 수 없음') if info else '알 수 없음'
        
        msg = f"💰 **{item_name}** {sell_amount}개를 팔아 **{total_price:,}원**을 벌었습니다."
        if count > current_count:
            msg += f"\n(해당 슬롯에 {current_count}개밖에 없어 모두 팔았습니다.)"
            
        await interaction.response.send_message(msg)

    @app_commands.command(name="탐사", description="탐사할 지역을 선택합니다.")
    async def explore(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        view = MapSelectionView(self, interaction, user["money"])
        embed = discord.Embed(title="🗺️ 탐사 지도", description=f"보유 자금: {user['money']:,}원", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="텃밭", description="작물을 관리합니다.")
    async def farm_status(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        plots = await db.fetch("SELECT * FROM farm WHERE user_id = $1 ORDER BY plant_time", interaction.user.id)
        
        embed = discord.Embed(title="🌿 텃밭", color=discord.Color.green())
        desc = f"**슬롯:** {user['unlocked_plots']}개\n\n"
        
        now = datetime.utcnow()
        can_harvest = False
        
        if not plots: desc += "비어있음. `/심기`를 해보세요."
        else:
            for i, plot in enumerate(plots):
                item = self.am.get_item(plot['item_id'])
                name = item['name'] if item else "???"
                mult = float(plot['multiplier'])
                
                plant_time = plot['plant_time'].replace(tzinfo=None) if plot['plant_time'].tzinfo else plot['plant_time']
                elapsed = (now - plant_time).total_seconds()
                remain = 600 - elapsed
                
                if remain <= 0:
                    status = "✅ **수확 가능**"
                    can_harvest = True
                else:
                    m, s = divmod(int(remain), 60)
                    status = f"⏳ {m}분 {s}초"
                desc += f"**{i+1}. {name}** (x{mult:.2f}) ➔ {status}\n"

        embed.description = desc
        view = discord.ui.View()
        
        btn = discord.ui.Button(label="수확", style=discord.ButtonStyle.success if can_harvest else discord.ButtonStyle.secondary, disabled=(not can_harvest), emoji="🚜")
        btn.callback = self.harvest_callback
        view.add_item(btn)

        # 확장 비용 (JSON 연동)
        current = user['unlocked_plots']
        farm_levels = self.am.data.get("facilities", {}).get("farm", {}).get("levels", [])
        next_info = next((l for l in farm_levels if l["level"] == current + 1), None)
        
        if next_info:
            cost = next_info.get("cost", 999999)
            btn_exp = discord.ui.Button(label=f"확장 ({cost:,}원)", style=discord.ButtonStyle.secondary)
            async def exp_cb(inter):
                u = await self.get_user_stats(inter.user.id)
                if u["money"] < cost: return await inter.response.send_message("돈 부족", ephemeral=True)
                await db.execute("UPDATE users SET money = money - $1, unlocked_plots = unlocked_plots + 1 WHERE user_id = $2", cost, inter.user.id)
                await inter.response.send_message(f"🎉 확장 완료! ({u['unlocked_plots']+1}칸)", ephemeral=True)
            btn_exp.callback = exp_cb
            view.add_item(btn_exp)

        await interaction.response.send_message(embed=embed, view=view)

    async def harvest_callback(self, interaction: discord.Interaction):
        plots = await db.fetch("SELECT * FROM farm WHERE user_id = $1", interaction.user.id)
        now = datetime.utcnow()
        harvested = []
        total_exp = 0
        
        for plot in plots:
            plant_time = plot['plant_time'].replace(tzinfo=None) if plot['plant_time'].tzinfo else plot['plant_time']
            if (now - plant_time).total_seconds() < 600: continue

            await db.execute("DELETE FROM farm WHERE id = $1", plot['id'])
            
            item_info = self.am.get_item(plot['item_id'])
            name = item_info['name'] if item_info else "작물"
            
            rand = random.random() * 100
            mult = float(plot['multiplier'])
            if rand < 30: mult += 0.5 
            elif rand >= 95: continue 
            
            harvested.append({'item_id': plot['item_id'], 'multiplier': mult, 'name': name})
            total_exp += 5

        if not harvested: return await interaction.response.send_message("수확할 게 없습니다.", ephemeral=True)
        await db.execute("UPDATE users SET exp = exp + $1 WHERE user_id = $2", total_exp, interaction.user.id)
        
        embed = discord.Embed(title="🚜 수확 성공", description="선택해주세요.", color=discord.Color.green())
        for item in harvested: embed.add_field(name=item['name'], value=f"x{item['multiplier']:.2f}", inline=False)
        view = HarvestChoiceView(self, interaction.user.id, harvested)
        await interaction.response.edit_message(content=None, embed=embed, view=view)
        view.message = interaction.message

    @app_commands.command(name="심기", description="작물을 심습니다.")
    async def plant(self, interaction: discord.Interaction, index: int):
        user = await self.get_user_stats(interaction.user.id)
        current = await db.fetchval("SELECT COUNT(*) FROM farm WHERE user_id = $1", interaction.user.id)
        if current >= user['unlocked_plots']: return await interaction.response.send_message("텃밭 꽉 참", ephemeral=True)
            
        item = await db.fetchrow("SELECT * FROM inventory WHERE user_id = $1 ORDER BY id LIMIT 1 OFFSET $2", interaction.user.id, index - 1)
        if not item: return await interaction.response.send_message("아이템 없음", ephemeral=True)
        
        # 개수 1개 차감
        await self.remove_item_from_inventory(item['id'], 1)
        
        await db.execute("INSERT INTO farm (user_id, item_id, multiplier, plant_time) VALUES ($1, $2, $3, NOW())", 
                         interaction.user.id, item['item_id'], item['multiplier'])
        
        info = self.am.get_item(item['item_id'])
        await interaction.response.send_message(f"🌱 **{info['name'] if info else '작물'}** 심기 완료!")

    @app_commands.command(name="가방", description="가방을 확인합니다.")
    async def inventory(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        max_slots = await self.get_bag_capacity(user['rank_id'])
        items = await db.fetch("SELECT * FROM inventory WHERE user_id = $1 ORDER BY id", interaction.user.id)
        
        embed = discord.Embed(title=f"🎒 {interaction.user.display_name}의 가방", color=discord.Color.gold())
        if not items: embed.description = "비어있음"
        else:
            lines = []
            for i, item in enumerate(items):
                info = self.am.get_item(item['item_id'])
                name = info['name'] if info else f"Item({item['item_id']})"
                price = info.get('price', 0) if info else 0
                mult = float(item['multiplier'])
                count = item['count'] if item['count'] else 1
                calc_price = int(price * mult)
                
                # 최대 중첩량 표시 (30개 넘으면 다음 칸으로)
                max_stack = self.am.get_config("inventory_rules", {}).get("max_stack_size", 30)
                
                lines.append(f"`{i+1}.` **{name}** (x{mult:.2f}) x**{count}**/{max_stack} | 개당 {calc_price}원")
            embed.description = "\n".join(lines)
            
        embed.set_footer(text=f"사용 중: {len(items)}슬롯 / 전체: {max_slots}슬롯 | 자산: {user['money']:,}원")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="프로필", description="내 정보")
    async def profile(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        rank = user['rank_id']
        lv_info = self.am.get_level_info(rank)
        title = lv_info.get("title", f"Rank {rank}")
        
        embed = discord.Embed(title=f"👤 {interaction.user.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="등급", value=f"{title}", inline=True)
        embed.add_field(name="돈", value=f"{user['money']:,}원", inline=True)
        embed.add_field(name="텃밭", value=f"{user['unlocked_plots']}칸", inline=True)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AlchemyRPG(bot))