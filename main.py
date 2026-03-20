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


Message = namedtuple("Message", ["is_spam", "original_reply_to", "id"])

messages: dict[int, Message] = {}


async def send_message(text: str, alert_media, mine_reply_to=None) -> int:
    sent_message = await client.send_message(
        consts.DESTINATION_CHANNEL,
        message=text,
        file=alert_media,
        reply_to=mine_reply_to,
    )
    return sent_message.id


def is_message_spam(text: str, reply_to_msg_id: int) -> bool:
    if "t.me/" in text or "telegram.me/" in text:
        return True

    try:
        return messages[reply_to_msg_id].is_spam
    except KeyError:
        return False


# The Event Listener
@client.on(events.NewMessage(chats=consts.SOURCE_CHANNEL))
async def forward_alert(event):
    message = event.message
    text = message.text or ""

    # Remove signature
    text = text.replace(consts.MESSAGE_SUFFIX, "").strip()

    # Check for ads
    reply_to_msg_id = message.reply_to_msg_id
    is_spam = is_message_spam(text, reply_to_msg_id)

    if is_spam:
        messages[message.id] = Message(is_spam, reply_to_msg_id, None)
        print("Dropped an ad promoting another channel.")
        return

    alert_media = message.media
    try:
        mine_reply_to = messages[reply_to_msg_id].id
    except KeyError:
        mine_reply_to = None
    try:
        sent_message_id = await send_message(text, alert_media, mine_reply_to)
        print("Forwarded a clean alert!")

    except FloodWaitError as e:
        print(f"Rate limit hit! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        sent_message_id = await send_message(text, alert_media, mine_reply_to)
        print("Forwarded the alert after sleeping.")

    except Exception as e:
        print(f"Failed to forward message: {e}")
        return

    messages[message.id] = Message(is_spam, reply_to_msg_id, sent_message_id)

    if len(messages) > consts.MAX_QUEUE_SIZE:
        # Dictionaries in Python 3.7+ maintain insertion order, so popping the first item will remove the oldest message.
        messages.pop(next(iter(messages)))


async def main():
    print("Securely booted up! Listening for alerts...")
    await client.start()
    # Keep the script running and listening for new messages
    await client.run_until_disconnected()


# Safely boot the asyncio loop
if __name__ == "__main__":
    asyncio.run(main())
