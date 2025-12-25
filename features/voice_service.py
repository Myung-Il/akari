from gtts import gTTS
import uuid
import os

# 생성된 파일이 저장될 경로 (data 폴더 활용)
DATA_DIR = "data"

def text_to_mp3(text: str, lang: str = 'ko') -> str:
    """
    텍스트를 받아 MP3 파일로 변환하고, 저장된 파일 경로를 반환합니다.
    파일명은 겹치지 않게 UUID를 사용합니다.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 고유한 파일명 생성 (예: data/tts_a1b2c3d4.mp3)
    filename = f"{DATA_DIR}/tts_{uuid.uuid4()}.mp3"
    
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    
    return filename

def delete_file(filename: str):
    """파일을 삭제합니다."""
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception as e:
            print(f"⚠️ 파일 삭제 실패 ({filename}): {e}")