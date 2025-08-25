#!/usr/bin/env python3
"""
Simple test script to verify bot is receiving messages
Run this instead of your main bot to debug basic connectivity
"""

import logging
import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

load_dotenv()

# Configure logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

class TestBot:
    def __init__(self, token):
        self.token = token
        print(f"🤖 Test bot initialized with token: {token[:10]}...")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        print(f"🚀 START command received from user {update.effective_user.id}")
        await update.message.reply_text(
            "🤖 Test bot is working!\n\n"
            "Available commands:\n"
            "/start - This message\n"
            "/test - Test response\n"
            "/quote - Test quote command\n"
            "Send any message to test message handling"
        )
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /test command"""
        print(f"🧪 TEST command received from user {update.effective_user.id}")
        print(f"📝 Full message: {update.message.text}")
        print(f"👤 User info: {update.effective_user.username} ({update.effective_user.id})")
        
        await update.message.reply_text(
            f"✅ Test successful!\n\n"
            f"👤 User: {update.effective_user.first_name}\n"
            f"🆔 ID: {update.effective_user.id}\n"
            f"📝 Message: {update.message.text}\n"
            f"⏰ Time: {update.message.date}"
        )
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test quote command"""
        print(f"📊 QUOTE command received from user {update.effective_user.id}")
        print(f"📝 Args: {context.args}")
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a symbol: /quote AAPL")
            return
        
        symbol = context.args[0].upper()
        print(f"📊 Symbol requested: {symbol}")
        
        await update.message.reply_text(
            f"📈 Quote test for {symbol}\n\n"
            f"✅ Command received successfully\n"
            f"✅ Symbol parsed: {symbol}\n"
            f"✅ Bot is responding correctly\n\n"
            f"(This is just a test - no real quote data)"
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle any text message"""
        print(f"💬 Regular message received from user {update.effective_user.id}")
        print(f"📝 Message: {update.message.text}")
        
        await update.message.reply_text(
            f"👋 I received your message: \"{update.message.text}\"\n\n"
            f"Try these commands:\n"
            f"/start - Welcome message\n"
            f"/test - Test bot functionality\n"
            f"/quote AAPL - Test quote command"
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        print(f"❌ ERROR occurred: {context.error}")
        logger.error("Exception while handling update:", exc_info=context.error)

async def main():
    """Run the test bot"""
    
    # Get token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        print("Make sure your .env file contains: TELEGRAM_BOT_TOKEN=your_token_here")
        return
    
    print(f"🤖 Starting test bot...")
    print(f"🔑 Token starts with: {token[:10]}...")
    
    # Create bot instance
    test_bot = TestBot(token)
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", test_bot.start_command))
    app.add_handler(CommandHandler("test", test_bot.test_command))
    app.add_handler(CommandHandler("quote", test_bot.quote_command))
    app.add_handler(CommandHandler("q", test_bot.quote_command))
    
    # Handle all other text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, test_bot.handle_message))
    
    # Error handler
    app.add_error_handler(test_bot.error_handler)
    
    print("🚀 Test bot starting...")
    print("📱 Send /start to your bot in Telegram to test")
    
    try:
        await app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        print("⚠️  nest_asyncio not installed, may have event loop issues")
    
    asyncio.run(main())
