from telegram import Update
from telegram.ext import ContextTypes

class BaseHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        welcome_message = """
🤖 *Stock Trading Bot*

📊 *Quotes & Data:*
• `/quote SYMBOL` - Get stock quote
• `/movers` - Market movers
• `/gainers` - Top gainers
• `/losers` - Top losers

💼 *Portfolio:*
• `/portfolio` - Portfolio summary
• `/positions` - Current positions
• `/balance` - Account balance

🛒 *Trading:*
• `/order` - Place order
• `/buy SYMBOL SHARES` - Quick buy
• `/sell SYMBOL SHARES` - Quick sell
• `/orders` - View orders

🔔 *Alerts:*
• `/alert SYMBOL PRICE` - Price alert
• `/alerts` - List alerts
• `/delalert ID` - Delete alert

👀 *Watchlist:*
• `/watchlist` - Show watchlist
• `/addwatch SYMBOL` - Add to watchlist
• `/delwatch SYMBOL` - Remove from watchlist

📰 *News:*
• `/news SYMBOL` - Get news

⚠️ *Educational use only. Verify all trades.*
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)