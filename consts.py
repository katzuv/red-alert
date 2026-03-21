import os

from dotenv import load_dotenv
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
DESTINATION_CHANNEL = int(os.getenv("DESTINATION_CHANNEL"))
SESSION = StringSession(os.getenv("SESSION_STRING"))

MESSAGE_SUFFIX = """.
🚨שתפו-https://t.me/beforeredalert"""

MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE"))
