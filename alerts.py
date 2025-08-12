from main import client

price_alerts = {}

async def handle_alert_command(update, context):
    if not update.message or not update.message.text.lower().startswith("alert"):
        return
    try:
        _, symbol, op, price = update.message.text.split()
        price = float(price)
        symbol = symbol.upper()
    except Exception:
        await update.effective_message.reply_text(
            "Usage: alert SYMBOL > price  OR alert SYMBOL < price"
        )
        return
    alerts = price_alerts.setdefault(update.effective_chat.id, [])
    alerts.append({"symbol": symbol, "op": op, "price": price})
    await update.effective_message.reply_text(f"✅ Alert set for {symbol} {op} {price}")

async def check_alerts(context):
    from bot import client  # Avoid circular imports
    to_remove = []
    for chat_id, alerts in price_alerts.items():
        for alert in alerts:
            data = client.quotes([alert["symbol"]]).json()
            last = data[alert["symbol"]]["quote"]["lastPrice"]
            if alert["op"] == ">" and last > alert["price"]:
                await context.bot.send_message(chat_id, f"📢 {alert['symbol']} hit {last} > {alert['price']}")
                to_remove.append((chat_id, alert))
            elif alert["op"] == "<" and last < alert["price"]:
                await context.bot.send_message(chat_id, f"📢 {alert['symbol']} hit {last} < {alert['price']}")
                to_remove.append((chat_id, alert))
    for chat_id, alert in to_remove:
        price_alerts[chat_id].remove(alert)
