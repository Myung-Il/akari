import os
from db.database import engine
from db.base import Base
from db.models import user, guild 

def init_db():
    # 데이터베이스 파일이 저장될 'data' 폴더가 없으면 생성
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📁 [DB] 'data' 폴더를 생성했습니다.")

    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    print("✨ [DB] 테이블 생성 완료!")