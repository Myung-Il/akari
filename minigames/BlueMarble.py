import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

# =========================
# 게임 전역 데이터
# =========================
players = {}  # {user_id: Player}
START_MONEY = 3_000_000
SALARY = 200_000

# 주사위 숫자별 이모지 매핑
DICE_EMOJIS = {
    1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 
    4: "4️⃣", 5: "5️⃣", 6: "6️⃣"
}

city = {
    "타이배이": {
        "color": discord.Color.red(),
        "소유자" : None,
        "건설비": {"대지료":50000, "별장":50000, "빌딩":150000, "호텔":250000},
        "통행료": {"대지료":2000, "별장":10000, "빌딩":90000, "호텔":250000}
    },
    "베이징": {
        "color": discord.Color.red(),
        "소유자" : None,
        "건설비": {"대지료":80000, "별장":50000, "빌딩":150000, "호텔":250000},
        "통행료": {"대지료":4000, "별장":20000, "빌딩":180000, "호텔":450000}
    },
    "마닐라": {
        "color": discord.Color.red(),
        "소유자" : None,
        "건설비": {"대지료":80000, "별장":50000, "빌딩":150000, "호텔":250000},
        "통행료": {"대지료":4000, "별장":20000, "빌딩":180000, "호텔":450000}
    },
    "제주도": {
        "color": discord.Color.light_theme(),
        "소유자" : None,
        "건설비": {"대지료":200000},
        "통행료": {"대지료":300000}
    },
    "싱가포르": {
        "color": discord.Color.red(),
        "소유자" : None,
        "건설비": {"대지료":100000, "별장":50000, "빌딩":150000, "호텔":250000},
        "통행료": {"대지료":6000, "별장":30000, "빌딩":270000, "호텔":550000}
    },
    "카이로": {
        "color": discord.Color.red(),
        "소유자" : None,
        "건설비": {"대지료":100000, "별장":50000, "빌딩":150000, "호텔":250000},
        "통행료": {"대지료":6000, "별장":30000, "빌딩":270000, "호텔":550000}
    },
    "이스탄불": {
        "color": discord.Color.red(),
        "소유자" : None,
        "건설비": {"대지료":120000, "별장":50000, "빌딩":150000, "호텔":250000},
        "통행료": {"대지료":8000, "별장":40000, "빌딩":300000, "호텔":600000}
    },



    "아테네": {
        "color": discord.Color.orange(),
        "소유자" : None,
        "건설비": {"대지료":140000, "별장":100000, "빌딩":300000, "호텔":500000},
        "통행료": {"대지료":10000, "별장":50000, "빌딩":450000, "호텔":750000}
    },
    "코펜하겐": {
        "color": discord.Color.orange(),
        "소유자" : None,
        "건설비": {"대지료":160000, "별장":100000, "빌딩":300000, "호텔":500000},
        "통행료": {"대지료":12000, "별장":60000, "빌딩":500000, "호텔":900000}
    },
    "스톡홀름": {
        "color": discord.Color.orange(),
        "소유자" : None,
        "건설비": {"대지료":160000, "별장":100000, "빌딩":300000, "호텔":500000},
        "통행료": {"대지료":12000, "별장":60000, "빌딩":500000, "호텔":900000}
    },
    "콩코드 여객기": {
        "color": discord.Color.light_theme(),
        "소유자" : None,
        "건설비": {"대지료":200000},
        "통행료": {"대지료":300000}
    },
    "베른": {
        "color": discord.Color.orange(),
        "소유자" : None,
        "건설비": {"대지료":180000, "별장":100000, "빌딩":300000, "호텔":500000},
        "통행료": {"대지료":14000, "별장":70000, "빌딩":550000, "호텔":950000}
    },
    "베를린": {
        "color": discord.Color.orange(),
        "소유자" : None,
        "건설비": {"대지료":180000, "별장":100000, "빌딩":300000, "호텔":500000},
        "통행료": {"대지료":14000, "별장":70000, "빌딩":550000, "호텔":950000}
    },
    "오타와": {
        "color": discord.Color.orange(),
        "소유자" : None,
        "건설비": {"대지료":200000, "별장":100000, "빌딩":300000, "호텔":500000},
        "통행료": {"대지료":16000, "별장":80000, "빌딩":600000, "호텔":1000000}
    },



    "부에노스아이레스": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":220000, "별장":150000, "빌딩":400000, "호텔":750000},
        "통행료": {"대지료":18000, "별장":90000, "빌딩":700000, "호텔":1050000}
    },
    "상파울루": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":240000, "별장":150000, "빌딩":450000, "호텔":750000},
        "통행료": {"대지료":20000, "별장":100000, "빌딩":750000, "호텔":1100000}
    },
    "시드니": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":240000, "별장":150000, "빌딩":450000, "호텔":750000},
        "통행료": {"대지료":20000, "별장":100000, "빌딩":750000, "호텔":1100000}
    },
    "부산": {
        "color": discord.Color.light_theme(),
        "소유자" : None,
        "건설비": {"대지료":500000},
        "통행료": {"대지료":600000}
    },
    "하와이": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":260000, "별장":150000, "빌딩":450000, "호텔":750000},
        "통행료": {"대지료":22000, "별장":110000, "빌딩":800000, "호텔":1150000}
    },
    "리스본": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":260000, "별장":150000, "빌딩":450000, "호텔":750000},
        "통행료": {"대지료":22000, "별장":110000, "빌딩":800000, "호텔":1150000}
    },
    "퀸 엘리자베스 호": {
        "color": discord.Color.light_theme(),
        "소유자" : None,
        "건설비": {"대지료":300000},
        "통행료": {"대지료":250000}
    },
    "마드리드": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":280000, "별장":150000, "빌딩":450000, "호텔":750000},
        "통행료": {"대지료":24000, "별장":120000, "빌딩":850000, "호텔":1200000}
    },


    "도쿄": {
        "color": discord.Color.blue(),
        "소유자" : None,
        "건설비": {"대지료":300000, "별장":200000, "빌딩":600000, "호텔":1000000},
        "통행료": {"대지료":26000, "별장":130000, "빌딩":900000, "호텔":1270000}
    },
    "컬럼비아호": {
        "color": discord.Color.light_theme(),
        "소유자" : None,
        "건설비": {"대지료":450000},
        "통행료": {"대지료":300000}
    },
    "파리": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":320000, "별장":200000, "빌딩":600000, "호텔":1000000},
        "통행료": {"대지료":28000, "별장":150000, "빌딩":1000000, "호텔":1400000}
    },
    "로마": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":320000, "별장":200000, "빌딩":600000, "호텔":1000000},
        "통행료": {"대지료":28000, "별장":150000, "빌딩":1000000, "호텔":1400000}
    },
    "런던": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":350000, "별장":200000, "빌딩":600000, "호텔":1000000},
        "통행료": {"대지료":35000, "별장":170000, "빌딩":1100000, "호텔":1500000}
    },
    "뉴욕": {
        "color": discord.Color.green(),
        "소유자" : None,
        "건설비": {"대지료":350000, "별장":200000, "빌딩":600000, "호텔":1000000},
        "통행료": {"대지료":35000, "별장":170000, "빌딩":1100000, "호텔":1500000}
    },
    "서울": {
        "color": discord.Color.blurple(),
        "소유자" : None,
        "건설비": {"대지료":1000000},
        "통행료": {"대지료":2000000}
    }
}

cards = {
    "병원비 지불": {
        "설명": "병원에서 건강진단을 받았습니다.",
        "기능": "병원비 5만 원을 은행에 납부합니다."
    },
    "복권 당첨": {
        "설명": "축하합니다. 복권에 당첨되었습니다.",
        "기능": "당첨금 20만원을 은행에서 받습니다."
    },
    "무인도 탈출": {
        "설명": "특수 무전기",
        "기능": "무인도에 갇혀 있을 때 사용할 수 있습니다, 1회 사용 후 반납합니다, 타인에게 팔 수 있습니다."
    },
    "무인도": {
        "설명": "폭풍을 만났습니다. 무인도로 곧장 가세요",
        "기능": "출발지를 지나더라도 월급을 받을 수 없습니다."
    },
    "파티 초대권": {
        "설명": "대중 앞에서 장기자랑을 하세요",
        "기능": "다른 게임 참가자들이 정한 상금을 은행에서 지불합니다."
    },
    "관광여행1": {
        "설명": "제주도로 가세요",
        "기능": "제주도 소유주에게 통행료를 지불합니다, 출발지를 지나갈 경우, 월급을 받습니다."
    },
    "과속운전 벌금": {
        "설명": "과속운전을 하였습니다.",
        "기능": "벌칙금 5만 원을 은행에 납부합니다."
    },
    "해외 유학": {
        "설명": "학교 등록금을 내세요",
        "기능": "등록금 10만원을 은행에 납부합니다."
    },
    "연금 혜택": {
        "설명": "노후연금을 받으세요",
        "기능": "연금 5만원을 은행에서 받습니다."
    },
    "이사1": {
        "설명": "뒤로 세 칸 옮기세요",
        "기능": ""
    },
    "고속도로": {
        "설명": "출발지까지 곧바로 가세요",
        "기능": "출발지에서 월급을 받습니다."
    },
    "우승": {
        "설명": "자동차 경주에서 챔피언이 되었습니다.",
        "기능": "상금 10만 원을 은행에서 받습니다."
    },
    "우대권1": {
        "설명": "상대방이 소유한 장소에 통행료 없이 머무를 수 있습니다.",
        "기능": "1회 사용 후, 황금 열쇠함에 반납합니다, 중요한 순간에 쓰세요."
    },
    "항공여행": {
        "설명": "콩코드 여객기를 타고 타이베이로 가세요",
        "기능": "콩코드 여객기 소유주에게 탑승료를 지불합니다, 출발지를 지나갈 경우 월급을 받습니다."
    },
    "건물수리비 지불": {
        "설명": "정기적으로 건물을 수리하여야 합니다.",
        "기능": "호텔 10만 원, 빌딩 6만 원, 별장 3만 원"
    },
    "방법비": {
        "설명": "방범비를 각 건물별로 다음과 같이 은행에 지불하세요",
        "기능": "호텔 5만 원, 빌딩 3만 원, 별장 1만 원"
    },
    "유람선 여행": {
        "설명": "퀸 엘리자베스호를 타고 베이징으로 가세요",
        "기능": "퀸 엘리자베스호 소유주에게 탑승료를 지불합니다. 출발지를 지나갈 경우, 월급을 받습니다."
    },
    "관광여행2": {
        "설명": "부산으로 가세요",
        "기능": "부산을 상대방이 가지고 있는 경우, 통행료를 지불합니다. 출발지를 지나갈 경우, 월급을 받습니다."
    },
    "생일 축하": {
        "설명": "모두에게 생일 축하를 받으세요",
        "기능": "전원에게 축하금 1만 원씩 받습니다."
    },
    "장학금 혜택": {
        "설명": "장학금을 받으세요",
        "기능": "장학금 10만 원을 은행에서 받습니다."
    },
    "정기 종합소득세": {
        "설명": "종합소득세를 각 건물별로 아래와 같이 지불하세요",
        "기능": "호텔 15만 원, 빌딩 10만 원, 별장 3만 원"
    },
    "노벨평화상 수상": {
        "설명": "당신은 세계 평화를 위하여 공헌하였습니다.",
        "기능": "수상금 30만 원을 은행에서 받습니다."
    },
    "관광여행3": {
        "설명": "세계 중심 도시, 서울로 가세요",
        "기능": "서울을 상대방이 가지고 있을 경우 통행료를 지불합니다."
    },
    "반액대매출1": {
        "설명": "당신의 부동산 중에서 가장 비싼 곳을 반액으로 은행에 파세요",
        "기능": "건물이 지어진 경우, 반액으로 함께 처분합니다."
    },
    "우주여행 초청장": {
        "설명": "우주항공국에서 우주여행 초청장이 왔습니다. 우주정류장으로 가세요",
        "기능": "무료이므로 컬럼비아호에 탑승료를 지불하지 않습니다, 출발지를 지나갈 경우 월급을 받습니다."
    },
    "우대권2": {
        "설명": "상대방이 소유한 장소에 통행료 없이 머무를 수 있습니다.",
        "기능": "1회 사용 후, 황금 열쇠함에 반납합니다, 중요한 순간에 쓰세요."
    },
    "세계일주 초대권": {
        "설명": "현재 위치에서부터 한 바퀴 돌아오세요",
        "기능": "다른 곳으로 갈 수 없습니다, 출발지를 지나가면서 월급을 받습니다. 사회복지기금을 지나가면서 모아놓은 기금을 받습니다."
    },
    "이사2": {
        "설명": "뒤로 두 칸 옮기세요",
        "기능": ""
    },
    "사회복지기금 배당": {
        "설명": "사회복지기금 접수처로 가세요",
        "기능": "출발지를 지나갈 경우, 월급을 받습니다."
    },
    "반액대매출2": {
        "설명": "당신의 부동산중에서 가장 비싼 곳을 반액으로 은행에 파세요",
        "기능": "건물이 지어진 경우, 반액으로 함께 처분합니다."
    }
}

class Player:
    def __init__(self, user_id):
        self.name = None          # 유저 이름 (디스코드 닉네임)
        self.user_id = user_id
        self.money = START_MONEY # 보유 자금
        self.properties = {}     # 보유 도시
        self.cards = []          # 보유 카드
        self.debt = 0            # 빚
        self.debt_turns = 0      # 빚 갚는 턴 수
        self.round = 0           # 현재 라운드 수

def not_player(user_id):
    if user_id not in players:return True
    else:return False

# =========================
# 황금 열쇠 데이터 클래스
# =========================

# ---------------------------------------------------------
# Cog 등록
# ---------------------------------------------------------
class BlueMarble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    # =====================================================================================================================
    # 유저 관리 데이터 클래스
    # =====================================================================================================================
    @app_commands.command(name="상태창", description="현재 플레이어의 상태를 확인합니다.")
    async def status(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if not_player(user_id):
            await interaction.response.send_message("❌ 게임에 참여하지 않은 유저입니다. 주사위를 먼저 굴려주세요.")
            return

        player = players[user_id]
        embed = discord.Embed(
            title=f"🎭 {player.name}님의 상태창",
            description=f"\
                💰 자금: {player.money}원\n\
                🏙️ 보유 도시: {', '.join(player.properties.keys()) if player.properties else '없음'}\n\
                🎴 보유 카드: {', '.join(player.cards) if player.cards else '없음'}\n\
                💸 빚: {player.debt}원 (남은 턴: {player.debt_turns})\n\
                🔄 라운드: {player.round}",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    # =====================================================================================================================
    # 주사위 데이터 클래스
    # =====================================================================================================================
    @app_commands.command(name="주사위", description="주사위를 굴립니다.")
    async def roll_dice(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if not_player(user_id):
            players[user_id] = Player(user_id)
            players[user_id].name = interaction.user.display_name
            players[user_id].money = START_MONEY
            players[user_id].properties.clear()
            players[user_id].cards.clear()
            players[user_id].debt = 0
            players[user_id].debt_turns = 0
            players[user_id].round = 1
            welcome_text = f"🎉 {interaction.user.mention}님, 블루마블 게임에 오신 것을 환영합니다!, 주사위를 굴립니다!"
        else: welcome_text = f"🎲 {interaction.user.mention}님이 주사위를 굴립니다!"

        # 1. 초기 메시지 전송 (애니메이션 시작)
        embed = discord.Embed(
            title="🎲 주사위를 던졌습니다!",
            description="데굴데굴... 주사위가 굴러가고 있습니다.",
            color=discord.Color.light_grey()
        )
        await interaction.response.send_message(content=welcome_text, embed=embed)

        for _ in range(2):  # 2초간 대기 후 주사위 결과 전송
            await asyncio.sleep(0.2)
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)

            # 임베드 내용 업데이트
            embed.description = f"데굴데굴... **{DICE_EMOJIS[dice1]} {DICE_EMOJIS[dice2]}**"
            await interaction.edit_original_response(embed=embed)

        embed = discord.Embed(
            title = f"{dice1+dice2}칸 이동하세요",
            description = f"{DICE_EMOJIS[dice1]} {DICE_EMOJIS[dice2]} {('더블! 한번 더 주사위를 굴립니다.' if dice1 == dice2 else '')}",
            color = discord.Color.gold() if dice1 == dice2 else discord.Color.green()
        )
        await interaction.edit_original_response(embed=embed)

    # =====================================================================================================================
    # 매입 & 매각 데이터 클래스
    # =====================================================================================================================
    class BuyView(discord.ui.View):
        def __init__(self, city_name, price, buyer_id, owner_id):
            super().__init__()
            self.city_name = city_name
            self.price = price
            self.buyer_id = buyer_id
            self.owner_id = owner_id

        @discord.ui.button(label="매입한다", style=discord.ButtonStyle.green)
        async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.buyer_id:
                await interaction.response.send_message("❌ 이 버튼은 매입자만 사용할 수 있습니다.", ephemeral=True)
                return
            
            if self.price <= players[self.buyer_id].money:
                players[self.buyer_id].money -= self.price
                city[self.city_name]["소유자"] = self.buyer_id
                players[self.buyer_id].properties[self.city_name] = 0b000

                if self.owner_id != None:
                    players[self.owner_id].money += self.price
                    players[self.owner_id].properties.pop(self.city_name)

                await interaction.response.send_message(f"✅ {interaction.user.mention}님이 {self.city_name}을(를) 매입했습니다! {self.price}원을 지불하세요.")
            else: await interaction.response.send_message("❌ 매입에 필요한 자금이 부족합니다.", ephemeral=True)

        @discord.ui.button(label="취소한다", style=discord.ButtonStyle.red)
        async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.buyer_id:
                await interaction.response.send_message("❌ 이 버튼은 매입자만 사용할 수 있습니다.", ephemeral=True)
                return
            # 취소 로직 구현
            await interaction.response.send_message(f"❌ {interaction.user.mention}님이 {self.city_name} 매입을 취소했습니다.")

    async def city_autocomplete(self, interaction: discord.Interaction, current: str):
        if not_player(interaction.user.id):return []
        return [
            app_commands.Choice(name=city_name, value=city_name)
            for city_name in city.keys() if current.lower() in city_name.lower()
        ][:5]  # 최대 25개까지 반환

    @app_commands.command(name="매입", description="원하는 도시를 매입합니다.")
    @app_commands.autocomplete(city_name=city_autocomplete)
    async def buy_property(self, interaction: discord.Interaction, city_name: str):
        user_id = interaction.user.id
        if not_player(user_id):
            await interaction.response.send_message("❌ 게임에 참여하지 않은 유저입니다. 주사위를 먼저 굴려주세요.")
            return

        if city_name not in city:
            await interaction.response.send_message("❌ 존재하지 않는 도시입니다. 도시 이름을 확인해주세요.")
            return
        
        # 소유자가 없는 도시인지 확인
        if city[city_name]["소유자"] == None:
            price = city[city_name]["건설비"]["대지료"]
            embed = discord.Embed(
                title=f"🏙️ {city_name} 매입 제안",
                description=f"{interaction.user.mention}님이 [ {city_name} ]을(를) 매입하려고 합니다.\n\
                    매입 가격: {price}원\n매입하시겠습니까?\n\
                    보유 자금 : {players[user_id].money}원",
                color=city[city_name]["color"]
            )
        
        # 소유자가 있는 도시인 경우
        else:
            price = city[city_name]["건설비"]["대지료"]
            if players[city[city_name]["소유자"]].properties[city_name] & 0b100: price += city[city_name]["건설비"]["호텔"]
            if players[city[city_name]["소유자"]].properties[city_name] & 0b010: price += city[city_name]["건설비"]["빌딩"]
            if players[city[city_name]["소유자"]].properties[city_name] & 0b001: price += city[city_name]["건설비"]["별장"]
            price *= 2

            embed = discord.Embed(
                title=f"🏙️ {city_name} 매입 제안",
                description=f"{interaction.user.mention}님이 {players[city[city_name]['소유자']].name}의 도시 [ {city_name} ]을(를) 매입하려고 합니다.\n\
                    매입 가격: {price}원\n매입하시겠습니까?\n\
                    보유 자금 : {players[user_id].money}원",
                color=city[city_name]["color"]
            )

        view = self.BuyView(city_name, price, user_id, city[city_name]["소유자"])
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="매각", description="원하는 도시를 매각합니다.")
    async def sell_property(self, interaction: discord.Interaction, city_name: str):
        user_id = interaction.user.id
        if not_player(user_id):
            await interaction.response.send_message("❌ 게임에 참여하지 않은 유저입니다. 주사위를 먼저 굴려주세요.")
            return

        if city_name not in city:
            await interaction.response.send_message("❌ 존재하지 않는 도시입니다. 도시 이름을 확인해주세요.")
            return
        
        if city[city_name]["소유자"] != user_id:
            await interaction.response.send_message("❌ 매각하려는 도시의 소유자가 아닙니다.", ephemeral=True)
            return
        
        price = city[city_name]["건설비"]["대지료"]
        if players[user_id].properties[city_name] & 0b100: price += city[city_name]["건설비"]["호텔"]
        if players[user_id].properties[city_name] & 0b010: price += city[city_name]["건설비"]["빌딩"]
        if players[user_id].properties[city_name] & 0b001: price += city[city_name]["건설비"]["별장"]

        city[city_name]["소유자"] = None
        players[user_id].money += price
        players[user_id].properties.pop(city_name)

        await interaction.response.send_message(f"✅ {interaction.user.mention}님이 {city_name}을(를) 매각했습니다! {price}원을 받으세요.")

    # =====================================================================================================================
    # 건설 데이터 클래스
    # =====================================================================================================================
    @app_commands.command(name="건설", description="보유한 도시에 건물을 건설합니다.")
    async def build(self, interaction: discord.Interaction, city_name: str, building_type: str):
        user_id = interaction.user.id
        if not_player(user_id):
            await interaction.response.send_message("❌ 게임에 참여하지 않은 유저입니다. 주사위를 먼저 굴려주세요.")
            return

        if city_name not in city:
            await interaction.response.send_message("❌ 존재하지 않는 도시입니다. 도시 이름을 확인해주세요.")
            return
        
        if city[city_name]["소유자"] != user_id:
            await interaction.response.send_message("❌ 건설하려는 도시의 소유자가 아닙니다.", ephemeral=True)
            return
    # 1. 소유자의 id와 명령어를 사용한 유저의 id가 같아야 한다.
    # 2. 해당 땅에 건물의 건설비들의 합만큼 보유금액에서 줄어든다.
    # 3. 종류는 별장, 빌딩, 호텔
    # 4. 각 건물은 1개씩 밖에 못 짓는다.
    # 5. 월급을 1회 받았을 때, 빌딩을 지을 수 있다.
    # 6. 월급을 2회 받았을 때, 호텔을 지을 수 있다.

    # =====================================================================================================================
    # 통행료 데이터 클래스
    # =====================================================================================================================

    # =====================================================================================================================
    # 기타 등등 데이터 클래스
    # =====================================================================================================================



async def setup(bot):
    await bot.add_cog(BlueMarble(bot))