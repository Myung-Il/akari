from sqlalchemy import Column, Integer, String, BigInteger
from db.base import Base

class Guild(Base):
    __tablename__ = "guilds"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, unique=True, index=True) # 디스코드 서버 ID
    name = Column(String) # 서버 이름