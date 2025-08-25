from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class WatchlistHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager
        # In production, use a database
        self.watchlists = {}  # {user_id: [symbols]}
    
    async def show_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        user_id = update.effective_user.id
        
        if user_id not in self.watchlists or not self.watchlists[user_id]:
            await update.message.reply_text("👀 Your watchlist is empty\nUse `/addwatch SYMBOL` to add stocks")
            return
        
        try:
            message = "👀 *Your Watchlist*\n\n"
            
            # Get quotes for all watchlist symbols
            for symbol in self.watchlists[user_id][:10]:  # Limit to 10 for performance
                try:
                    quote_data = self.schwab.get_quote(symbol)
                    if quote_data and symbol in quote_data:
                        quote = quote_data[symbol]['quote']
                        price = quote.get('lastPrice', 0)
                        change = quote.get('netChange', 0)
                        change_pct = quote.get('netPercentChangeInDouble', 0)
                        
                        emoji = "📈" if change >= 0 else "📉"
                        message += f"{emoji} *{symbol}*: ${price:.2f} ({change_pct:+.2f}%)\n"
                    else:
                        message += f"❓ *{symbol}*: Quote unavailable\n"
                except Exception as e:
                    logger.error(f"Error getting quote for {symbol}: {e}")
                    message += f"❓ *{symbol}*: Error getting quote\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="watch_refresh"),
                    InlineKeyboardButton("➕ Add Stock", callback_data="watch_add_prompt")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing watchlist: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def add_to_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /addwatch SYMBOL\nExample: /addwatch AAPL")
            return
        
        symbol = context.args[0].upper()
        user_id = update.effective_user.id
        
        try:
            # Verify symbol exists by getting quote
            quote_data = self.schwab.get_quote(symbol)
            if not quote_data or symbol not in quote_data:
                await update.message.reply_text(f"❌ Could not find symbol {symbol}")
                return
            
            # Add to watchlist
            if user_id not in self.watchlists:
                self.watchlists[user_id] = []
            
            if symbol not in self.watchlists[user_id]:
                self.watchlists[user_id].append(symbol)
                await update.message.reply_text(f"✅ Added {symbol} to your watchlist")
            else:
                await update.message.reply_text(f"ℹ️ {symbol} is already in your watchlist")
                
        except Exception as e:
            logger.error(f"Error adding to watchlist: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def remove_from_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /delwatch SYMBOL\nExample: /delwatch AAPL")
            return
        
        symbol = context.args[0].upper()
        user_id = update.effective_user.id
        
        try:
            if user_id in self.watchlists and symbol in self.watchlists[user_id]:
                self.watchlists[user_id].remove(symbol)
                await update.message.reply_text(f"✅ Removed {symbol} from your watchlist")
            else:
                await update.message.reply_text(f"ℹ️ {symbol} is not in your watchlist")
                
        except Exception as e:
            logger.error(f"Error removing from watchlist: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data == "watch_refresh":
            # Refresh watchlist
            await self.show_watchlist(query, context)
        elif data.startswith("watch_add_"):
            symbol = data.split("_")[2]
            user_id = query.from_user.id
            
            if user_id not in self.watchlists:
                self.watchlists[user_id] = []
            
            if symbol not in self.watchlists[user_id]:
                self.watchlists[user_id].append(symbol)
                await query.edit_message_text(f"✅ Added {symbol} to your watchlist")
            else:
                await query.edit_message_text(f"ℹ️ {symbol} is already in your watchlist")