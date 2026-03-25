import os

from dotenv import load_dotenv
from telethon.sessions import StringSession

load_dotenv()

def _load_as_int_or_str(env_var_name: str):
    value = os.getenv(env_var_name)
    try:
        return int(value)
    except ValueError:
        return value

PHONE_NUMBER = os.getenv("PHONE_NUMBER")
PASSWORD = os.getenv("TELEGRAM_PASSWORD")

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SOURCE_CHANNEL = _load_as_int_or_str("SOURCE_CHANNEL")
DESTINATION_CHANNEL = _load_as_int_or_str("DESTINATION_CHANNEL")
SESSION = StringSession(os.getenv("SESSION_STRING"))

MESSAGE_SIGNATURE = """.
🚨שתפו-https://t.me/beforeredalert"""

MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE"))
