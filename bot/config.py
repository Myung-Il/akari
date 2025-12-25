import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
INTENTS_FLAGS = {
    "members": True,
    "message_content": True,
}