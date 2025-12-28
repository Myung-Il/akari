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
# 데이터 관리
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
                print(f"⚠️ {filename} 로드 실패: {e}")
                self.data[key] = {} if key != "levels" else []

    def get_item(self, item_id: str):
        return self.data["items"].get(str(item_id))

    def get_level_info(self, rank_idx: int):
        levels = self.data.get("levels", [])
        if not levels: return {}
        if rank_idx >= len(levels): return levels[-1]
        return levels[rank_idx]

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
        
        embed = discord.Embed(title="🌲 탐사 진행 중", description=desc, color=discord.Color.green())
        embed.set_footer(text="1분 동안 활동이 없으면 자동 종료됩니다.")
        return embed

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
        
        if random.uniform(0, 100) < probs.get("trap", 0):
            msg = self.location.get("trap_msg", "함정에 걸렸습니다!")
            self._update_log(f"💥 {msg}")
            self.current_ap = max(0, self.current_ap - 1)
        else:
            drop_items = self.location.get("drop_items", [])
            if drop_items:
                item_id = random.choice(drop_items)
                count = await db.fetchval("SELECT COUNT(*) FROM inventory WHERE user_id = $1", self.user_id)
                if count >= self.max_slots:
                    self._update_log("🎒 가방이 가득 차서 아이템을 버렸습니다.")
                else:
                    await db.execute("INSERT INTO inventory (user_id, item_id) VALUES ($1, $2)", self.user_id, item_id)
                    item = self.cog.am.get_item(item_id)
                    name = item['name'] if item else "미확인 물체"
                    self._update_log(f"📦 **{name}** 획득!")
            else:
                self._update_log("💨 아무것도 찾지 못했습니다.")

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
            try: await self.message.edit(content="⏳ 시간 초과! 아이템이 가방으로 자동 보관되었습니다.", view=None, embed=None)
            except: pass
            for item in self.items:
                await db.execute("INSERT INTO inventory (user_id, item_id, multiplier) VALUES ($1, $2, $3)",
                                 self.user_id, item['item_id'], item['multiplier'])

    @discord.ui.button(label="💰 모두 판매", style=discord.ButtonStyle.success)
    async def sell_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id: return
        total_price = 0
        details = []
        for item in self.items:
            info = self.cog.am.get_item(item['item_id'])
            
            base_price = info.get('price', 0) if info else 0
            name = info.get('name', '알 수 없음') if info else '알 수 없음'
            
            final_price = int(base_price * item['multiplier'])
            total_price += final_price
            details.append(f"{name} (x{item['multiplier']:.2f}) : +{final_price}원")

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
            return await interaction.response.send_message("❌ 텃밭이 부족합니다. 나머지는 가방으로 이동합니다.", ephemeral=True)

        for item in self.items:
            await db.execute("INSERT INTO farm (user_id, item_id, multiplier, plant_time) VALUES ($1, $2, $3, NOW())",
                             self.user_id, item['item_id'], item['multiplier'])
        
        embed = discord.Embed(title="🌱 재배 시작", description="작물을 다시 심었습니다. (소요시간: 10분)", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

# ---------------------------------------------------------
# 메인 코어 기능
# ---------------------------------------------------------
class AlchemyRPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.am = AlchemyManager()

    async def get_user_stats(self, user_id: int):
        user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user:
            await db.execute("INSERT INTO users (user_id, unlocked_plots) VALUES ($1, 1)", user_id)
            user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        return user

    async def get_bag_capacity(self, rank_idx: int):
        level_info = self.am.get_level_info(rank_idx)
        base = self.am.data["config"]["inventory_rules"]["base_bag_slots"]
        bonus = level_info.get("bagSlotBonus", 0)
        return base + bonus

    # ------------------------------------------------------------------
    # [기능 1] 판매
    # ------------------------------------------------------------------
    @app_commands.command(name="판매", description="가방의 특정 아이템을 갯수만큼 판매합니다.")
    @app_commands.describe(index="가방에서의 아이템 번호", count="판매할 개수")
    async def sell_item(self, interaction: discord.Interaction, index: int, count: int = 1):
        if index < 1 or count < 1:
            return await interaction.response.send_message("❌ 번호와 개수는 1 이상이어야 합니다.", ephemeral=True)

        target_item = await db.fetchrow(
            "SELECT * FROM inventory WHERE user_id = $1 ORDER BY id LIMIT 1 OFFSET $2",
            interaction.user.id, index - 1
        )

        if not target_item:
            return await interaction.response.send_message(f"❌ 가방의 {index}번에는 아이템이 없습니다.", ephemeral=True)

        item_id = target_item['item_id']
        
        items_to_sell = await db.fetch(
            "SELECT * FROM inventory WHERE user_id = $1 AND item_id = $2 ORDER BY multiplier ASC LIMIT $3",
            interaction.user.id, item_id, count
        )

        if not items_to_sell:
            return await interaction.response.send_message("❌ 판매할 아이템을 찾을 수 없습니다.", ephemeral=True)

        total_price = 0
        sold_count = 0
        
        item_info = self.am.get_item(item_id)
        base_price = item_info.get('price', 0) if item_info else 0
        item_name = item_info.get('name', '알 수 없음') if item_info else '알 수 없음'

        for item in items_to_sell:
            price = int(base_price * float(item['multiplier']))
            total_price += price
            sold_count += 1
            await db.execute("DELETE FROM inventory WHERE id = $1", item['id'])

        await db.execute("UPDATE users SET money = money + $1 WHERE user_id = $2", total_price, interaction.user.id)

        embed = discord.Embed(title="💰 판매 완료", color=discord.Color.gold())
        embed.add_field(name="아이템", value=item_name, inline=True)
        embed.add_field(name="수량", value=f"{sold_count}개", inline=True)
        embed.add_field(name="획득 금액", value=f"+{total_price:,}원", inline=False)
        
        if sold_count < count:
            embed.set_footer(text=f"요청하신 {count}개보다 적게 보유하여 전량 판매했습니다.")

        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # [기능 2] 탐사
    # ------------------------------------------------------------------
    @app_commands.command(name="탐사", description="탐사할 지역을 선택하고 아이템을 수집합니다.")
    async def explore(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        view = MapSelectionView(self, interaction, user["money"])
        
        embed = discord.Embed(title="🗺️ 탐사 지도", description="어디로 떠나시겠습니까?", color=discord.Color.blue())
        embed.add_field(name="보유 자금", value=f"{user['money']:,}원")
        
        await interaction.response.send_message(embed=embed, view=view)

    # ------------------------------------------------------------------
    # [기능 3] 텃밭 (확장 비용 JSON 연동)
    # ------------------------------------------------------------------
    @app_commands.command(name="텃밭", description="작물의 상태를 확인하고 수확합니다.")
    async def farm_status(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        plots = await db.fetch("SELECT * FROM farm WHERE user_id = $1 ORDER BY plant_time", interaction.user.id)
        
        embed = discord.Embed(title="🌿 약초 텃밭", color=discord.Color.green())
        desc = f"**슬롯:** {user['unlocked_plots']}개 사용 가능\n\n"
        
        now = datetime.utcnow()
        can_harvest = False
        
        if not plots:
            desc += "텅 비어있습니다. `/심기` 명령어로 작물을 심어보세요."
        else:
            for i, plot in enumerate(plots):
                item = self.am.get_item(plot['item_id'])
                name = item['name'] if item else "알 수 없음"
                mult = float(plot['multiplier'])
                
                plant_time = plot['plant_time']
                if plant_time.tzinfo: plant_time = plant_time.replace(tzinfo=None)
                
                elapsed = (now - plant_time).total_seconds()
                remain = 600 - elapsed
                
                if remain <= 0:
                    status = "✅ **수확 가능**"
                    can_harvest = True
                else:
                    mins, secs = divmod(int(remain), 60)
                    status = f"⏳ {mins}분 {secs}초"
                
                desc += f"**{i+1}. {name}** (x{mult:.2f}) ➔ {status}\n"

        embed.description = desc
        view = discord.ui.View()
        
        btn_harvest = discord.ui.Button(label="수확하기", style=discord.ButtonStyle.success if can_harvest else discord.ButtonStyle.secondary, disabled=(not can_harvest), emoji="🚜")
        btn_harvest.callback = self.harvest_callback
        view.add_item(btn_harvest)

        # [수정된 부분] facilities.json의 farm > levels 데이터를 읽어서 확장 비용 결정
        current_plots = user['unlocked_plots']
        next_level = current_plots + 1
        
        # JSON에서 다음 레벨 정보 찾기
        farm_levels = self.am.data.get("facilities", {}).get("farm", {}).get("levels", [])
        next_level_info = next((lvl for lvl in farm_levels if lvl["level"] == next_level), None)
        
        if next_level_info:
            cost = next_level_info.get("cost", 999999)
            
            btn_expand = discord.ui.Button(label=f"확장 ({cost:,}원)", style=discord.ButtonStyle.secondary)
            
            async def expand_callback(inter):
                u = await self.get_user_stats(inter.user.id)
                if u["money"] < cost: 
                    return await inter.response.send_message("자금이 부족합니다.", ephemeral=True)
                
                await db.execute("UPDATE users SET money = money - $1, unlocked_plots = unlocked_plots + 1 WHERE user_id = $2", cost, inter.user.id)
                await inter.response.send_message(f"🎉 텃밭이 확장되었습니다! ({u['unlocked_plots']+1}칸)", ephemeral=True)
            
            btn_expand.callback = expand_callback
            view.add_item(btn_expand)

        await interaction.response.send_message(embed=embed, view=view)

    async def harvest_callback(self, interaction: discord.Interaction):
        plots = await db.fetch("SELECT * FROM farm WHERE user_id = $1", interaction.user.id)
        now = datetime.utcnow()
        
        harvested = []
        total_exp = 0
        
        for plot in plots:
            plant_time = plot['plant_time']
            if plant_time.tzinfo: plant_time = plant_time.replace(tzinfo=None)
            
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

        if not harvested:
            return await interaction.response.send_message("수확할 작물이 없거나, 모두 시들어버렸습니다.", ephemeral=True)

        await db.execute("UPDATE users SET exp = exp + $1 WHERE user_id = $2", total_exp, interaction.user.id)
        
        embed = discord.Embed(title="🚜 수확 성공!", description="작물을 획득했습니다. 선택해주세요.", color=discord.Color.green())
        for item in harvested:
            embed.add_field(name=item['name'], value=f"품질: x{item['multiplier']:.2f}", inline=False)
            
        view = HarvestChoiceView(self, interaction.user.id, harvested)
        await interaction.response.edit_message(content=None, embed=embed, view=view)
        view.message = interaction.message

    @app_commands.command(name="심기", description="가방에 있는 아이템을 심습니다.")
    async def plant(self, interaction: discord.Interaction, index: int):
        user = await self.get_user_stats(interaction.user.id)
        current = await db.fetchval("SELECT COUNT(*) FROM farm WHERE user_id = $1", interaction.user.id)
        if current >= user['unlocked_plots']: return await interaction.response.send_message("텃밭이 가득 찼습니다.", ephemeral=True)
            
        item = await db.fetchrow("SELECT * FROM inventory WHERE user_id = $1 ORDER BY id LIMIT 1 OFFSET $2", interaction.user.id, index - 1)
        if not item: return await interaction.response.send_message("잘못된 아이템 번호입니다.", ephemeral=True)
        
        await db.execute("DELETE FROM inventory WHERE id = $1", item['id'])
        await db.execute("INSERT INTO farm (user_id, item_id, multiplier, plant_time) VALUES ($1, $2, $3, NOW())", 
                         interaction.user.id, item['item_id'], item['multiplier'])
        
        info = self.am.get_item(item['item_id'])
        item_name = info['name'] if info else "알 수 없음"
        await interaction.response.send_message(f"🌱 **{item_name}** 심기 완료! (10분 뒤 수확)")

    # ------------------------------------------------------------------
    # [기능 4] 가방
    # ------------------------------------------------------------------
    @app_commands.command(name="가방", description="보유 중인 아이템을 확인합니다.")
    async def inventory(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        max_slots = await self.get_bag_capacity(user['rank_id'])
        items = await db.fetch("SELECT * FROM inventory WHERE user_id = $1 ORDER BY id", interaction.user.id)
        
        embed = discord.Embed(title=f"🎒 {interaction.user.display_name}의 가방", color=discord.Color.gold())
        
        if not items:
            embed.description = "가방이 비어있습니다."
        else:
            lines = []
            for i, item in enumerate(items):
                info = self.am.get_item(item['item_id'])
                if info:
                    name = info.get('name', "알 수 없는 아이템")
                    price = info.get('price', 0)
                else:
                    name = f"오류 아이템({item['item_id']})"
                    price = 0
                    
                mult = float(item['multiplier'])
                calc_price = int(price * mult)
                
                lines.append(f"`{i+1}.` **{name}** (x{mult:.2f}) | 💰 {calc_price}원")
            embed.description = "\n".join(lines)
            
        embed.set_footer(text=f"슬롯: {len(items)} / {max_slots} | 총 자산: {user['money']:,}원")
        await interaction.response.send_message(embed=embed)

    # ------------------------------------------------------------------
    # [기능 5] 프로필
    # ------------------------------------------------------------------
    @app_commands.command(name="프로필", description="나의 성장 정보를 확인합니다.")
    async def profile(self, interaction: discord.Interaction):
        user = await self.get_user_stats(interaction.user.id)
        
        rank_idx = user['rank_id']
        level_info = self.am.get_level_info(rank_idx)
        rank_title = level_info.get("title", f"Rank {rank_idx}")
        next_exp = level_info.get("requiredExpForNext", 100)
        
        cur_exp = user['exp']
        percent = min(1.0, cur_exp / next_exp) if next_exp > 0 else 1.0
        bar_len = 10
        filled = int(percent * bar_len)
        bar = "🟦" * filled + "⬜" * (bar_len - filled)
        
        embed = discord.Embed(title=f"📜 {interaction.user.display_name}", color=discord.Color.blue())
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        embed.add_field(name="🏅 등급", value=f"**{rank_title}** (Lv.{rank_idx})", inline=True)
        embed.add_field(name="💰 자산", value=f"{user['money']:,}원", inline=True)
        embed.add_field(name="✨ 경험치", value=f"{bar} ({cur_exp}/{next_exp})", inline=False)
        embed.add_field(name="🚜 텃밭 현황", value=f"{user['unlocked_plots']}구획 사용 가능", inline=True)
        embed.add_field(name="🎒 가방 크기", value=f"{await self.get_bag_capacity(rank_idx)}칸", inline=True)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AlchemyRPG(bot))