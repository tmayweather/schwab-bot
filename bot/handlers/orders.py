from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class OrderHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager
        # Store order sessions temporarily (use database in production)
        self.order_sessions = {}
    
    async def place_order_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📈 Buy Order", callback_data="order_type_buy"),
                InlineKeyboardButton("📉 Sell Order", callback_data="order_type_sell")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 Select order type:",
            reply_markup=reply_markup
        )
    
    async def quick_buy(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /buy SYMBOL SHARES\nExample: /buy AAPL 10")
            return
        
        symbol = context.args[0].upper()
        try:
            shares = int(context.args[1])
            await self._initiate_order(update, symbol, shares, "BUY")
        except ValueError:
            await update.message.reply_text("❌ Invalid number of shares")
    
    async def quick_sell(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: /sell SYMBOL SHARES\nExample: /sell AAPL 10")
            return
        
        symbol = context.args[0].upper()
        try:
            shares = int(context.args[1])
            await self._initiate_order(update, symbol, shares, "SELL")
        except ValueError:
            await update.message.reply_text("❌ Invalid number of shares")
    
    async def _initiate_order(self, update, symbol, shares, action):
        # Get current quote
        try:
            quote_data = self.schwab.get_quote(symbol)
            if quote_data and symbol in quote_data:
                price = quote_data[symbol]['quote']['lastPrice']
                estimated_cost = price * shares
                
                message = f"""
🔧 *Order Confirmation*

Symbol: {symbol}
Action: {action}
Shares: {shares}
Current Price: ${price:.2f}
Estimated {'Cost' if action == 'BUY' else 'Proceeds'}: ${estimated_cost:.2f}

⚠️ This is a market order that will execute immediately.
                """
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Confirm", callback_data=f"order_confirm_{symbol}_{shares}_{action}"),
                        InlineKeyboardButton("❌ Cancel", callback_data="order_cancel")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(f"❌ Could not get quote for {symbol}")
        except Exception as e:
            logger.error(f"Error initiating order: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def get_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        try:
            accounts = self.schwab.get_accounts()
            if accounts and len(accounts) > 0:
                account_hash = accounts[0]['hashValue']
                # Get orders (you'd need to implement this in SchwabManager)
                # orders = self.schwab.get_orders(account_hash)
                
                # Placeholder response
                await update.message.reply_text("📋 *Recent Orders*\n\nNo recent orders found.")
            else:
                await update.message.reply_text("❌ No accounts found")
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            await update.message.reply_text(f"❌ Error getting orders: {str(e)}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data.startswith("order_confirm_"):
            parts = data.split("_")
            symbol, shares, action = parts[2], parts[3], parts[4]
            await self._execute_order(query, symbol, int(shares), action)
        elif data == "order_cancel":
            await query.edit_message_text("❌ Order cancelled")
    
    async def _execute_order(self, query, symbol, shares, action):
        # In production, implement actual order execution
        message = f"""
✅ *Order Submitted*

Symbol: {symbol}
Action: {action}
Shares: {shares}

⚠️ *Demo Mode*: This is a simulation. 
In production, this would place a real order through Schwab API.
        """
        await query.edit_message_text(message, parse_mode='Markdown')