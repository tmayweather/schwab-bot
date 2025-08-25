from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class AlertHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager
        # In production, use a database
        self.alerts = {}  # {user_id: [alerts]}
        self.alert_task = None
    
    async def create_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /alert SYMBOL PRICE\n"
                "Example: /alert AAPL 150.00"
            )
            return
        
        symbol = context.args[0].upper()
        try:
            target_price = float(context.args[1])
            user_id = update.effective_user.id
            
            # Add alert
            if user_id not in self.alerts:
                self.alerts[user_id] = []
            
            alert_id = len(self.alerts[user_id]) + 1
            alert = {
                'id': alert_id,
                'symbol': symbol,
                'target_price': target_price,
                'chat_id': update.effective_chat.id
            }
            
            self.alerts[user_id].append(alert)
            
            await update.message.reply_text(
                f"✅ Alert created!\n"
                f"Symbol: {symbol}\n"
                f"Target: ${target_price:.2f}\n"
                f"Alert ID: {alert_id}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid price format")
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            await update.message.reply_text(f"❌ Error creating alert: {str(e)}")
    
    async def list_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        user_id = update.effective_user.id
        
        if user_id not in self.alerts or not self.alerts[user_id]:
            await update.message.reply_text("📭 No active alerts")
            return
        
        message = "🔔 *Your Active Alerts*\n\n"
        for alert in self.alerts[user_id]:
            message += f"• ID: {alert['id']} - {alert['symbol']} @ ${alert['target_price']:.2f}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def delete_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /delalert ALERT_ID")
            return
        
        try:
            alert_id = int(context.args[0])
            user_id = update.effective_user.id
            
            if user_id in self.alerts:
                self.alerts[user_id] = [a for a in self.alerts[user_id] if a['id'] != alert_id]
                await update.message.reply_text(f"✅ Alert {alert_id} deleted")
            else:
                await update.message.reply_text("❌ Alert not found")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid alert ID")
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def start_alert_system(self):
        """Start the alert monitoring system"""
        if self.alert_task is None:
            self.alert_task = asyncio.create_task(self._monitor_alerts())
    
    async def _monitor_alerts(self):
        """Monitor alerts and send notifications"""
        while True:
            try:
                for user_id, user_alerts in self.alerts.items():
                    for alert in user_alerts[:]:  # Copy to avoid modification during iteration
                        try:
                            quote_data = self.schwab.get_quote(alert['symbol'])
                            if quote_data and alert['symbol'] in quote_data:
                                current_price = quote_data[alert['symbol']]['quote']['lastPrice']
                                
                                # Check if alert should trigger (simple price crossing)
                                if abs(current_price - alert['target_price']) <= 0.01:
                                    # Send alert notification
                                    message = f"""
🚨 *Price Alert Triggered!*

Symbol: {alert['symbol']}
Target: ${alert['target_price']:.2f}
Current: ${current_price:.2f}
                                    """
                                    
                                    # In production, you'd use the bot instance to send messages
                                    # For now, just log the alert
                                    logger.info(f"Alert triggered for {alert['symbol']} @ {current_price}")
                                    
                                    # Remove triggered alert
                                    user_alerts.remove(alert)
                                    
                        except Exception as e:
                            logger.error(f"Error checking alert: {e}")
                
                # Check alerts every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(60)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        if data.startswith("alert_set_"):
            symbol = data.split("_")[2]
            await query.edit_message_text(
                f"To set an alert for {symbol}, use:\n"
                f"`/alert {symbol} TARGET_PRICE`\n"
                f"Example: `/alert {symbol} 100.00`",
                parse_mode='Markdown'
            )