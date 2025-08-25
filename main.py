import logging
import asyncio
import os
import nest_asyncio
from dotenv import load_dotenv

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram import Update
from bot.auth import AuthManager
from bot.schwab_client import SchwabManager
from bot.handlers.quotes import QuoteHandler
from bot.handlers.orders import OrderHandler
from bot.handlers.portfolio import PortfolioHandler
from bot.handlers.movers import MoversHandler
from bot.handlers.alerts import AlertHandler
from bot.handlers.watchlist import WatchlistHandler
from bot.handlers.news import NewsHandler
from bot.handlers.base import BaseHandler

load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self, telegram_token: str, schwab_app_key: str, schwab_app_secret: str,
                 schwab_callback_url: str):
        self.telegram_token = telegram_token
        self.auth_manager = AuthManager()
        self.schwab_manager = SchwabManager(schwab_app_key, schwab_app_secret, schwab_callback_url)

        # Initialize handlers
        self.quote_handler = QuoteHandler(self.schwab_manager, self.auth_manager)
        self.order_handler = OrderHandler(self.schwab_manager, self.auth_manager)
        self.portfolio_handler = PortfolioHandler(self.schwab_manager, self.auth_manager)
        self.movers_handler = MoversHandler(self.schwab_manager, self.auth_manager)
        self.alert_handler = AlertHandler(self.schwab_manager, self.auth_manager)
        self.watchlist_handler = WatchlistHandler(self.schwab_manager, self.auth_manager)
        self.news_handler = NewsHandler(self.schwab_manager, self.auth_manager)
        self.base_handler = BaseHandler(self.schwab_manager, self.auth_manager)

    async def initialize(self):
        """Initialize all components"""
        await self.schwab_manager.initialize()
        await self.alert_handler.start_alert_system()

    def setup_handlers(self, application: Application):
        """Setup all command handlers"""
        # Base commands
        application.add_handler(CommandHandler("start", self.base_handler.start))
        application.add_handler(CommandHandler("help", self.base_handler.help))

        # Quote handlers
        application.add_handler(CommandHandler("quote", self.quote_handler.get_quote))
        application.add_handler(CommandHandler("q", self.quote_handler.get_quote))

        # Order handlers
        application.add_handler(CommandHandler("order", self.order_handler.place_order_start))
        application.add_handler(CommandHandler("buy", self.order_handler.quick_buy))
        application.add_handler(CommandHandler("sell", self.order_handler.quick_sell))
        application.add_handler(CommandHandler("orders", self.order_handler.get_orders))

        # Portfolio handlers
        application.add_handler(CommandHandler("portfolio", self.portfolio_handler.get_portfolio))
        application.add_handler(CommandHandler("positions", self.portfolio_handler.get_positions))
        application.add_handler(CommandHandler("balance", self.portfolio_handler.get_balance))

        # Market movers
        application.add_handler(CommandHandler("movers", self.movers_handler.get_market_movers))
        application.add_handler(CommandHandler("gainers", self.movers_handler.get_gainers))
        application.add_handler(CommandHandler("losers", self.movers_handler.get_losers))

        # Alert system
        application.add_handler(CommandHandler("alert", self.alert_handler.create_alert))
        application.add_handler(CommandHandler("alerts", self.alert_handler.list_alerts))
        application.add_handler(CommandHandler("delalert", self.alert_handler.delete_alert))

        # Watchlist
        application.add_handler(CommandHandler("watchlist", self.watchlist_handler.show_watchlist))
        application.add_handler(CommandHandler("addwatch", self.watchlist_handler.add_to_watchlist))
        application.add_handler(CommandHandler("delwatch", self.watchlist_handler.remove_from_watchlist))

        # News
        application.add_handler(CommandHandler("news", self.news_handler.get_news))

        # Callback handlers
        application.add_handler(CallbackQueryHandler(self.handle_callback))

        # Error handler
        application.add_error_handler(self.error_handler)

    async def handle_callback(self, update: Update, context):
        """Route callback queries to appropriate handlers"""
        query = update.callback_query
        data = query.data
        if data.startswith("order_"):
            await self.order_handler.handle_callback(update, context)
        elif data.startswith("portfolio_"):
            await self.portfolio_handler.handle_callback(update, context)
        elif data.startswith("alert_"):
            await self.alert_handler.handle_callback(update, context)
        elif data.startswith("watch_"):
            await self.watchlist_handler.handle_callback(update, context)
        elif data.startswith("quote_"):
            await self.quote_handler.handle_callback(update, context)

    async def error_handler(self, update: object, context):
        """Global error handler"""
        logger.error("Exception while handling update:", exc_info=context.error)

    async def run(self):
        """Run the bot"""
        # Initialize the bot first
        await self.initialize()
        
        # Then set up and run the application
        application = Application.builder().token(self.telegram_token).build()
        self.setup_handlers(application)
        print("🤖 Starting Telegram Stock Bot...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)


async def async_main():
    """Async main function that combines initialization and running"""
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    SCHWAB_APP_KEY = os.getenv("SCHWAB_APP_KEY")
    SCHWAB_APP_SECRET = os.getenv("SCHWAB_APP_SECRET")
    SCHWAB_CALLBACK_URL = os.getenv("SCHWAB_CALLBACK_URL")

    if not all([TELEGRAM_BOT_TOKEN, SCHWAB_APP_KEY, SCHWAB_APP_SECRET, SCHWAB_CALLBACK_URL]):
        raise ValueError("Missing required environment variables")
    
    # Initialize the bot components
    bot = TradingBot(TELEGRAM_BOT_TOKEN, SCHWAB_APP_KEY, SCHWAB_APP_SECRET, SCHWAB_CALLBACK_URL)
    
    # Run the bot (this will handle initialization internally)
    await bot.run()


def main():
    """Main entry point"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()