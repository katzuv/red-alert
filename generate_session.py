import asyncio
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

import consts

load_dotenv()


async def main():
    print("Starting the Telegram client...")

    # Initialize the client with an empty StringSession
    client = TelegramClient(StringSession(), consts.API_ID, consts.API_HASH)

    # Start the client (this triggers the phone number & code prompt)
    await client.start(password=lambda: input("Please enter your 2FA Cloud Password: "))

    print("\n✅ Login successful! Here is your StringSession:\n")
    session = client.session.save()
    print(session)
    Path(".session_string").write_text(session)

    print("\n---------------------------------------------------------")
    print("🚨 COPY THE ENTIRE STRING ABOVE.")
    print("🚨 GO TO GITHUB -> SECRETS -> ADD AS 'TELEGRAM_SESSION'.")
    print("🚨 NEVER SHARE THIS STRING WITH ANYONE. IT IS YOUR PASSWORD.")

    # Close the connection safely
    client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
