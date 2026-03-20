import asyncio
from collections import namedtuple

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

import consts

# Load variables from .env if running locally
load_dotenv()

# Initialize the client
client = TelegramClient(consts.SESSION, consts.API_ID, consts.API_HASH)


Message = namedtuple("Message", ["is_spam", "original_reply_to"])

messages: dict[int, Message] = {}


async def send_message(text: str, alert_media):
    await client.send_message(
        consts.DESTINATION_CHANNEL, message=text, file=alert_media
    )


# The Event Listener
@client.on(events.NewMessage(chats=consts.SOURCE_CHANNEL))
async def forward_alert(event):
    text = event.message.text or ""

    # Remove signature
    text = text.replace(consts.MESSAGE_SUFFIX, "").strip()

    # Check for ads
    if "t.me/" in text or "telegram.me/" in text:
        print("Dropped an ad promoting another channel.")
        return

    alert_media = event.message.media

    try:
        await send_message(text, alert_media)
        print("Forwarded a clean alert!")

    except FloodWaitError as e:
        print(f"Rate limit hit! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        await send_message(text, alert_media)
        print("Forwarded the alert after sleeping.")

    except Exception as e:
        print(f"Failed to forward message: {e}")


async def main():
    print("Securely booted up! Listening for alerts...")
    await client.start()
    # Keep the script running and listening for new messages
    await client.run_until_disconnected()


# Safely boot the asyncio loop
if __name__ == "__main__":
    asyncio.run(main())
