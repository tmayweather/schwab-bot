from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class QuoteHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager
    
    async def get_quote(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle quote requests with better error handling and debugging"""
        user_id = update.effective_user.id
        logger.info(f"Quote request from user {user_id}")
        
        # Check authorization first
        if not self.auth.is_authorized(user_id):
            logger.warning(f"Unauthorized quote request from user {user_id}")
            await update.message.reply_text("🔒 You are not authorized to use this bot.")
            return
        
        # Check if symbol was provided
        if not context.args:
            await update.message.reply_text(
                "📈 *Quote Command Usage*\n\n"
                "Format: `/quote SYMBOL`\n"
                "Example: `/quote AAPL`\n"
                "Example: `/q TSLA`",
                parse_mode='Markdown'
            )
            return
        
        symbol = context.args[0].upper().strip()
        logger.info(f"Getting quote for symbol: {symbol}")
        
        # Send "typing" action to show the bot is working
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Check if schwab client is available
            if not self.schwab or not hasattr(self.schwab, 'get_quote'):
                logger.error("Schwab manager not properly initialized")
                await update.message.reply_text("❌ Trading service not available. Please try again later.")
                return
            
            # Get the quote
            quote_data = self.schwab.get_quote(symbol)
            logger.info(f"Quote data received: {quote_data is not None}")
            
            if quote_data and symbol in quote_data:
                await self._format_and_send_quote(update, symbol, quote_data[symbol])
            else:
                await update.message.reply_text(
                    f"❌ Could not find quote for *{symbol}*\n\n"
                    "Please check:\n"
                    "• Symbol spelling\n"
                    "• Market is open\n"
                    "• Symbol exists on the exchange",
                    parse_mode='Markdown'
                )
                
        except AttributeError as e:
            logger.error(f"AttributeError getting quote for {symbol}: {e}")
            await update.message.reply_text(
                f"❌ Service configuration error. Please contact support.\n"
                f"Error: {str(e)}"
            )
        except ConnectionError as e:
            logger.error(f"ConnectionError getting quote for {symbol}: {e}")
            await update.message.reply_text(
                "❌ Connection error. Please check your internet connection and try again."
            )
        except Exception as e:
            logger.error(f"Unexpected error getting quote for {symbol}: {e}")
            await update.message.reply_text(
                f"❌ Unexpected error getting quote for *{symbol}*\n"
                f"Error: {str(e)}\n\n"
                "Please try again in a moment.",
                parse_mode='Markdown'
            )
    
    async def _format_and_send_quote(self, update, symbol, data):
        """Format and send the quote data"""
        try:
            # Handle both possible data structures
            if 'quote' in data:
                quote = data['quote']
            else:
                quote = data
            
            # Extract quote data with defaults
            price = quote.get('lastPrice', 0)
            change = quote.get('netChange', 0)
            change_pct = quote.get('netPercentChangeInDouble', 0)
            volume = quote.get('totalVolume', 0)
            high = quote.get('highPrice', 0)
            low = quote.get('lowPrice', 0)
            bid = quote.get('bidPrice', 0)
            ask = quote.get('askPrice', 0)
            
            # Determine trend emoji
            if change > 0:
                change_emoji = "📈"
                change_color = "🟢"
            elif change < 0:
                change_emoji = "📉" 
                change_color = "🔴"
            else:
                change_emoji = "➖"
                change_color = "🔵"
            
            # Format the message
            message = f"""
{change_emoji} *{symbol}* {change_color}

💰 *Price:* ${price:.2f}
📊 *Change:* {change:+.2f} ({change_pct:+.2f}%)
📊 *Volume:* {volume:,}
📺 *High:* ${high:.2f}
📻 *Low:* ${low:.2f}
"""
            
            # Add bid/ask if available
            if bid > 0 and ask > 0:
                message += f"💵 *Bid/Ask:* ${bid:.2f} / ${ask:.2f}\n"
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("📈 Buy", callback_data=f"order_buy_{symbol}"),
                    InlineKeyboardButton("📉 Sell", callback_data=f"order_sell_{symbol}")
                ],
                [
                    InlineKeyboardButton("➕ Add to Watchlist", callback_data=f"watch_add_{symbol}"),
                    InlineKeyboardButton("🔔 Set Alert", callback_data=f"alert_set_{symbol}")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"quote_refresh_{symbol}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error formatting quote for {symbol}: {e}")
            # Fallback to simple message
            await update.message.reply_text(
                f"📊 *{symbol}*\n"
                f"Price: ${price:.2f}\n"
                f"Change: {change:+.2f} ({change_pct:+.2f}%)",
                parse_mode='Markdown'
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline buttons"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"Quote callback received: {data}")
        
        if data.startswith("quote_refresh_"):
            symbol = data.split("_")[2]
            await self.get_quote_refresh(query, symbol)
    
    async def get_quote_refresh(self, query, symbol):
        """Refresh a quote display"""
        try:
            # Send "typing" action
            await query.bot.send_chat_action(chat_id=query.message.chat_id, action="typing")
            
            quote_data = self.schwab.get_quote(symbol)
            
            if quote_data and symbol in quote_data:
                # Update the existing message
                await self._update_quote_message(query, symbol, quote_data[symbol])
            else:
                await query.edit_message_text(f"❌ Could not refresh quote for {symbol}")
                
        except Exception as e:
            logger.error(f"Error refreshing quote for {symbol}: {e}")
            await query.edit_message_text(f"❌ Error refreshing quote: {str(e)}")
    
    async def _update_quote_message(self, query, symbol, data):
        """Update an existing quote message"""
        try:
            # Handle both possible data structures
            if 'quote' in data:
                quote = data['quote']
            else:
                quote = data
            
            price = quote.get('lastPrice', 0)
            change = quote.get('netChange', 0)
            change_pct = quote.get('netPercentChangeInDouble', 0)
            volume = quote.get('totalVolume', 0)
            high = quote.get('highPrice', 0)
            low = quote.get('lowPrice', 0)
            
            # Determine trend emoji
            if change > 0:
                change_emoji = "📈"
                change_color = "🟢"
            elif change < 0:
                change_emoji = "📉"
                change_color = "🔴"
            else:
                change_emoji = "➖"
                change_color = "🔵"
            
            message = f"""
{change_emoji} *{symbol}* {change_color}

💰 *Price:* ${price:.2f}
📊 *Change:* {change:+.2f} ({change_pct:+.2f}%)
📊 *Volume:* {volume:,}
📺 *High:* ${high:.2f}
📻 *Low:* ${low:.2f}

🔄 *Updated*
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📈 Buy", callback_data=f"order_buy_{symbol}"),
                    InlineKeyboardButton("📉 Sell", callback_data=f"order_sell_{symbol}")
                ],
                [
                    InlineKeyboardButton("➕ Add to Watchlist", callback_data=f"watch_add_{symbol}"),
                    InlineKeyboardButton("🔔 Set Alert", callback_data=f"alert_set_{symbol}")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data=f"quote_refresh_{symbol}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error updating quote message for {symbol}: {e}")
            await query.edit_message_text(f"❌ Error updating quote: {str(e)}")