import os

from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SOURCE_CHANNEL = "@beforeredalert"
DESTINATION_CHANNEL = int(os.environ["DESTINATION_CHANNEL"])
SESSION_STRING = os.environ["SESSION_STRING"]

MESSAGE_SUFFIX = """.
🚨שתפו-https://t.me/beforeredalert"""
