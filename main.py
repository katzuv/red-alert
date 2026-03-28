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


Message = namedtuple("Message", ["is_spam", "original_reply_to", "id", "text"])

messages: dict[int, Message] = {}


async def send_message(
    text: str, alert_media, mine_reply_to: int | None, source_channel_message_id: int
) -> int:
    sent_message = await client.send_message(
        consts.DESTINATION_CHANNEL,
        message=text,
        file=alert_media,
        reply_to=mine_reply_to,
    )
    log = f"Forwarded a clean alert. Original ID: {source_channel_message_id}, my ID: {sent_message.id}"
    if mine_reply_to:
        log += f". Reply to my message ID: {mine_reply_to}"
    logging.info(log)
    return sent_message.id


def clean_text(text: str) -> str:
    for string in consts.STRINGS_TO_REMOVE:
        text = text.replace(string, "").strip()
    return text


def is_message_spam(text: str, reply_to_msg_id: int) -> bool:
    if "http" in text:
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

    source_channel_message = event.message
    original_text = source_channel_message.text or ""

    if source_channel_message.id in messages:
        logging.info(
            f"Already processed message ID {source_channel_message.id}, skipping."
        )
        return

    # Remove signature
    text = clean_text(original_text)

    # Check for ads
    reply_to_msg_id = source_channel_message.reply_to_msg_id
    is_spam = is_message_spam(text, reply_to_msg_id)

    if is_spam:
        messages[source_channel_message.id] = Message(
            is_spam, reply_to_msg_id, None, original_text
        )
        logging.info(
            f"Dropped an ad promoting another channel. Message ID: {source_channel_message.id}"
        )
        return

    alert_media = source_channel_message.media
    try:
        mine_reply_to = messages[reply_to_msg_id].id
    except KeyError:
        mine_reply_to = None

    try:
        sent_message_id = await send_message(
            text, alert_media, mine_reply_to, source_channel_message.id
        )

    except FloodWaitError as e:
        logging.info(f"Rate limit hit! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        sent_message_id = await send_message(
            text, alert_media, mine_reply_to, source_channel_message.id
        )

    except Exception:
        logging.exception("Failed to forward message")
        return

    messages[source_channel_message.id] = Message(
        is_spam, reply_to_msg_id, sent_message_id, original_text
    )


async def edit_message(
    new_text: str, my_message_id: int, source_channel_message_id: int
):
    await client.edit_message(
        entity=consts.DESTINATION_CHANNEL, message=my_message_id, text=new_text
    )
    logging.info(
        f"Mirrored an edited message. Original ID: {source_channel_message_id}, my ID: {my_message_id}"
    )


@client.on(events.MessageEdited(chats=consts.SOURCE_CHANNEL))
async def sync_edits(event):
    source_channel_message = event.message
    if source_channel_message.id not in messages:
        return

    my_original_message = messages[source_channel_message.id]
    logging.info(
        f"Received an edit for original ID {source_channel_message.id}, my ID {my_original_message.id}, Original text: {my_original_message.text}, New text: {source_channel_message.text}"
    )

    if my_original_message.is_spam:
        return

    text = clean_text(source_channel_message.text)

    if text == my_original_message.text:
        logging.info("Dropping an edit because the cleaned text didn't change.")
        return

    if is_message_spam(text, source_channel_message.reply_to_msg_id):
        logging.info("Dropping an edit because it turned into an ad.")
        return

    my_message_id = my_original_message.id
    try:
        await edit_message(text, my_message_id, source_channel_message.id)

    except FloodWaitError as e:
        logging.info(f"Rate limit hit! Sleeping for {e.seconds} seconds...")
        await asyncio.sleep(e.seconds)
        await edit_message(text, my_message_id, source_channel_message.id)

    except MessageNotModifiedError:
        # Telegram is just telling us the text is already identical. We can safely ignore it!
        logging.info("Ignored an edit because the text didn't actually change.")
        return

    except Exception:
        logging.exception("Failed to edit message")
        return


@client.on(events.MessageDeleted(chats=consts.SOURCE_CHANNEL))
async def sync_deletions(event):
    original_ids = []
    my_ids = []
    for original_id in event.deleted_ids:
        original_ids.append(original_id)

        try:
            message = messages[original_id]
        except KeyError:
            logging.warning(
                f"Received deletion for message absent from database. Original ID: {original_id}"
            )
            continue

        if message.is_spam:
            logging.info(
                f"Received deletion for spam message. Original ID: {original_id}"
            )
        else:
            my_ids.append(message.id)

    if not my_ids:
        logging.info("No messages to actually be deleted.")
        return

    await client.delete_messages(entity=consts.DESTINATION_CHANNEL, message_ids=my_ids)

    original_ids = ", ".join(map(str, original_ids))
    my_ids = ", ".join(map(str, my_ids))
    logging.info(
        f"Successfully mirrored a deletion. Original IDs: {original_ids}, my ID: {my_ids}"
    )


async def main():
    logging.info("Securely booted up! Listening for alerts...")
    await client.start()
    # Keep the script running and listening for new messages
    await client.run_until_disconnected()


# Safely boot the asyncio loop
if __name__ == "__main__":
    asyncio.run(main())
