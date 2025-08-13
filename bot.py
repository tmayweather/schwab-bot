import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, filters
import schwabdev
from quotes import get_quotes_as_string
from movers import get_market_movers

# Load .env variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

# Create Schwab API client
client = schwabdev.Client(
    os.getenv("app_key"),
    os.getenv("app_secret"),
    os.getenv("callback_url")
)

# Handler for any text messages or channel posts
async def handle_message(update, context):
    text = None

    # Check where the message came from
    if update.message:  # Private or group chat
        text = update.message.text
    elif hasattr(update, "channel_post") and update.channel_post:  # Channel post
        text = update.channel_post.text

    # Ignore if not text
    if not text:
        return

    text = text.strip()

    # Only respond if it starts with "quote"
    if text.lower().startswith("q"):
        parts = text.split()
        symbols = [s.upper() for s in parts[1:]]  # Skip first word "quote"
        if not symbols:
            await update.effective_message.reply_text(
                "Please provide at least one symbol, e.g. `quote AAPL`",
                parse_mode="MarkdownV2"
            )
            return

        # Fetch from Schwab API
        result = get_quotes_as_string(client, symbols)

        # Reply
        await update.effective_message.reply_text(result)

if __name__ == "__main__":
    TELEGRAM_TOKEN = os.getenv("telegram_token")
    if not TELEGRAM_TOKEN:
        raise Exception("Add your telegram_token to .env")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # One handler for private chats, groups, and channels
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
