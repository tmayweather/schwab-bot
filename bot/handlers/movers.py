from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

import logging

logger = logging.getLogger(__name__)


def get_market_movers_data(client, index, top_n=5):
    """
    Fetch and return the top N movers by % change and volume from a specified index.
    Args:
        client: API client instance (must have .movers() method).
        index (str): Market index symbol, e.g. "$DJI".
        top_n (int): Number of top movers to return for each category.

    Returns:
        dict: Dictionary containing two lists — 'top_percent' and 'top_volume'.
    """
    if not index:
        return {"error": "No index provided"}

    # Prepend '$' if it's not already there
    if not index.startswith('$'):
        index = '$' + index

    try:
        # Call the API
        data = client.movers(index).json()  # note the () after json
        # Extract the list of movers
        screeners = data.get("screeners", [])
        if not screeners:
            return {"error": "No movers found for this index"}

        # Pull only important fields
        movers_list = [
            {
                'symbol': s['symbol'],
                'company': s['description'],
                'price': s['lastPrice'],
                'netChange': s['netChange'],
                'percentChange': s['netPercentChange'] * 100,  # convert decimal to %
                'volume': s['volume'],
                'trades': s['trades'],
                'marketShare': s['marketShare']
            }
            for s in screeners
        ]

        # Sort for top N movers
        top_percent = sorted(movers_list, key=lambda x: abs(x['percentChange']), reverse=True)[:top_n]
        top_volume = sorted(movers_list, key=lambda x: x['volume'], reverse=True)[:top_n]

        return {
            "top_percent": top_percent,
            "top_volume": top_volume
        }
    except Exception as e:
        return {"error": f"Error fetching movers: {e}"}


class MoversHandler:
    def __init__(self, schwab_manager, auth_manager):
        self.schwab = schwab_manager
        self.auth = auth_manager

    async def get_market_movers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.auth.is_authorized(update.effective_user.id):
            return

        index = None
        if context.args:
            index = context.args[0].upper()  # Get the index from the arguments and convert to uppercase
        else:
            index = "SPX"  # Default index

        try:
            movers_data = get_market_movers_data(self.schwab.client, index)

            if "error" in movers_data:
                await update.message.reply_text(f"❌ Error: {movers_data['error']}")
                return

            message = "📊 *Market Movers*\n\n"

            if movers_data.get("top_percent"):
                message += "📈 *Top Movers by Percent Change:*\n"
                for i, mover in enumerate(movers_data["top_percent"][:5], 1):
                    message += (f"{i}. {mover['symbol']} - {mover['company']} "
                                f"(${mover['price']:.2f}, {mover['percentChange']:.2f}%)\n")

            if movers_data.get("top_volume"):
                message += "\n💰 *Top Movers by Volume:*\n"
                for i, mover in enumerate(movers_data["top_volume"][:5], 1):
                    message += (f"{i}. {mover['symbol']} - {mover['company']} "
                                f"(${mover['price']:.2f}, Volume: {mover['volume']})\n")

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error getting market movers: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")


    async def get_gainers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # This functionality is replaced by the new get_market_movers which can sort by both volume and percent
        await update.message.reply_text("This command is no longer supported. Use /movers instead.", parse_mode='Markdown')

    async def get_losers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # This functionality is replaced by the new get_market_movers which can sort by both volume and percent
        await update.message.reply_text("This command is no longer supported. Use /movers instead.", parse_mode='Markdown')