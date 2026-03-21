import asyncio
import logging
from collections import namedtuple

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, MessageNotModifiedError

import consts

# Load variables from .env if running locally
load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

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
    logging.info("Forwarded a clean alert.")
    return sent_message.id


def clean_text(text: str) -> str:
    return text.replace(consts.MESSAGE_SUFFIX, "").strip()


def is_message_spam(text: str, reply_to_msg_id: int) -> bool:
    if "t.me/" in text or "telegram.me/" in text:
        return True

    try:
        return messages[reply_to_msg_id].is_spam
    except KeyError:
        return False


def clean_queue_if_needed():
    if len(messages) >= consts.MAX_QUEUE_SIZE:
        # Dictionaries in Python 3.7+ maintain insertion order, so popping the first item will remove the oldest message.
        messages.pop(next(iter(messages)))


# The Event Listener
@client.on(events.NewMessage(chats=consts.SOURCE_CHANNEL))
async def forward_alert(event):
    clean_queue_if_needed()

    message = event.message
    text = message.text or ""

    # Remove signature
    text = clean_text(text)

    # Check for ads
    reply_to_msg_id = message.reply_to_msg_id
    is_spam = is_message_spam(text, reply_to_msg_id)

    if is_spam:
        messages[message.id] = Message(is_spam, reply_to_msg_id, None)
        logging.info("Dropped an ad promoting another channel.")
        return

    alert_media = message.media
    try:
        mine_reply_to = messages[reply_to_msg_id].id
    except KeyError:
        mine_reply_to = None

    try:
        sent_message_id = await send_message(text, alert_media, mine_reply_to)

    except FloodWaitError as e:
        logging.info(f"Rate limit hit! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        sent_message_id = await send_message(text, alert_media, mine_reply_to)

    except Exception:
        logging.exception("Failed to forward message")
        return

    messages[message.id] = Message(is_spam, reply_to_msg_id, sent_message_id)


async def edit_message(new_text: str, message_id: int):
    await client.edit_message(
        entity=consts.DESTINATION_CHANNEL, message=message_id, text=new_text
    )
    logging.info("Mirrored an edited message.")


@client.on(events.MessageEdited(chats=consts.SOURCE_CHANNEL))
async def sync_edits(event):
    message = event.message
    if message.id not in messages:
        return

    my_original_message = messages[message.id]
    if my_original_message.is_spam:
        return

    text = clean_text(message.text)
    if is_message_spam(text, message.reply_to_msg_id):
        return

    message_id = my_original_message.id
    try:
        await edit_message(text, message_id)

    except FloodWaitError as e:
        logging.info(f"Rate limit hit! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        await edit_message(text, message_id)

    except MessageNotModifiedError:
        # Telegram is just telling us the text is already identical. We can safely ignore it!
        logging.info("Ignored an edit because the text didn't actually change.")
        return

    except Exception:
        logging.exception("Failed to edit message")
        return


async def main():
    print("Securely booted up! Listening for alerts...")
    await client.start()
    # Keep the script running and listening for new messages
    await client.run_until_disconnected()


# Safely boot the asyncio loop
if __name__ == "__main__":
    asyncio.run(main())
