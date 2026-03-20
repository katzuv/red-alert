import os

from dotenv import load_dotenv
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SOURCE_CHANNEL = os.environ["SOURCE_CHANNEL"]
DESTINATION_CHANNEL = int(os.environ["DESTINATION_CHANNEL"])
SESSION = StringSession(os.environ["SESSION_STRING"])

MESSAGE_SUFFIX = """.
🚨שתפו-https://t.me/beforeredalert"""

MAX_QUEUE_SIZE = int(os.environ["MAX_QUEUE_SIZE"])
