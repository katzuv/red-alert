import asyncio

from telethon import TelegramClient

import consts


async def test_connection():
    print("Connecting to Telegram...")

    # The 'async with' block automatically starts the client and safely
    # disconnects it as soon as the block finishes.
    async with TelegramClient(consts.SESSION, consts.API_ID, consts.API_HASH) as client:
        print(f"Sending test message to {consts.DESTINATION_CHANNEL}...")

        # Send the message
        await client.send_message(
            consts.DESTINATION_CHANNEL, message="Test message from the bot!"
        )

        print("✅ Message sent successfully! Exiting.")


if __name__ == "__main__":
    asyncio.run(test_connection())
