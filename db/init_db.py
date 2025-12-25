from db.database import engine
from db.base import Base
# 모델들을 미리 임포트해야 Base가 인식합니다.
from db.models import user, guild 

def init_db():
    Base.metadata.create_all(bind=engine)
    print("✨ [DB] 테이블 생성 완료!")