from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class PortfolioHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager
    
    async def get_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        try:
            accounts = self.schwab.get_accounts()
            if accounts and len(accounts) > 0:
                account_hash = accounts[0]['hashValue']
                account_info = self.schwab.get_account_details(account_hash)
                
                if account_info:
                    balances = account_info.get('currentBalances', {})
                    total_value = balances.get('liquidationValue', 0)
                    cash = balances.get('cashBalance', 0)
                    buying_power = balances.get('buyingPower', 0)
                    
                    message = f"""
💼 *Portfolio Summary*

💰 Total Value: ${total_value:,.2f}
💵 Cash: ${cash:,.2f}
🔋 Buying Power: ${buying_power:,.2f}
                    """
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("📊 Positions", callback_data="portfolio_positions"),
                            InlineKeyboardButton("📈 Performance", callback_data="portfolio_performance")
                        ]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        message, 
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text("❌ Could not retrieve account details")
            else:
                await update.message.reply_text("❌ No linked accounts found")
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def get_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        try:
            accounts = self.schwab.get_accounts()
            if accounts and len(accounts) > 0:
                account_hash = accounts[0]['hashValue']
                positions_data = self.schwab.get_account_details(account_hash, fields="positions")
                
                if positions_data and 'positions' in positions_data:
                    positions = positions_data['positions']
                    
                    if positions:
                        message = "📊 *Current Positions*\n\n"
                        for pos in positions[:10]:
                            instrument = pos.get('instrument', {})
                            symbol = instrument.get('symbol', 'N/A')
                            quantity = pos.get('longQuantity', 0) - pos.get('shortQuantity', 0)
                            market_value = pos.get('marketValue', 0)
                            
                            if quantity != 0:
                                message += f"• *{symbol}*: {quantity} shares (${market_value:,.2f})\n"
                        
                        await update.message.reply_text(message, parse_mode='Markdown')
                    else:
                        await update.message.reply_text("📊 No positions found")
                else:
                    await update.message.reply_text("❌ Could not retrieve positions")
            else:
                await update.message.reply_text("❌ No linked accounts found")
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def get_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Similar implementation to get_portfolio but focused on balances
        await self.get_portfolio(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data == "portfolio_positions":
            # Convert callback to positions call
            await self.get_positions(query, context)