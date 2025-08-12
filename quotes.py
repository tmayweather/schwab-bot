

def get_quotes_as_string(client, symbols):
    """
    Fetch quotes from the Schwab API for given symbols and format relevant data for a day trader.
    
    Args:
        client: authenticated schwabdev.Client instance.
        symbols: list of ticker symbols (e.g. ["AAPL", "AMD"])
    
    Returns:
        str: Formatted multi-line string with relevant market and fundamental data.
    """
    if not symbols:
        return "No symbols provided."

    try:
        quotes_data = client.quotes(symbols).json()
    except Exception as e:
        return f"Error fetching quotes: {e}"

    lines = []
    for symbol, info in quotes_data.items():
        # Sections from the JSON response
        quote = info.get('quote', {})
        extended = info.get('extended', {})
        fundamental = info.get('fundamental', {})
        reference = info.get('reference', {})
        regular = info.get('regular', {})

        # Extract fields with fallback where applicable
        last_price = quote.get('lastPrice') or extended.get('lastPrice') or regular.get('regularMarketLastPrice')
        net_percent_change = quote.get('netPercentChange') or regular.get('regularMarketPercentChange')
        low_price = quote.get('lowPrice') or extended.get('lowPrice')
        open_price = quote.get('openPrice') or extended.get('openPrice')
        close_price = quote.get('closePrice') or extended.get('closePrice')
        high_price = quote.get('highPrice') or extended.get('highPrice')

        total_volume = quote.get('totalVolume') or extended.get('totalVolume')
        avg_10d_volume = fundamental.get('avg10DaysVolume')
        pe_ratio = fundamental.get('peRatio')
        div_yield = fundamental.get('divYield')
        security_status = quote.get('securityStatus')
        description = reference.get('description', symbol)

        # Formatting numbers nicely
        def fmt_number(num, decimals=2):
            if num is None:
                return "N/A"
            if isinstance(num, float):
                return f"{num:.{decimals}f}"
            return str(num)

        def fmt_percent(num):
            if num is None:
                return "N/A"
            return f"{num:+.2f}%"

        # Compose formatted string for this symbol
        s = f"  ~ {description} ({symbol}) ~\n"
        s += f"  LAST: {fmt_number(last_price)}\n"
        s += f"  CHANGE: {fmt_percent(net_percent_change)}\n"
        s += f"  OPEN: {fmt_number(open_price)}  High: {fmt_number(high_price)}  Low: {fmt_number(low_price)}\n"
        s += f"  CLOSE: {fmt_number(close_price)}\n"
        s += f"  VOLUME: {total_volume if total_volume is not None else 'N/A'}  10D Avg Vol: {fmt_number(avg_10d_volume, 0)}\n"
        s += f"  P/E RATIO: {fmt_number(pe_ratio)}  Dividend Yield: {fmt_number(div_yield, 3)}%\n"
        s += f"  SECURITY STATUS: {security_status}\n"

        lines.append(s)

    return "\n\n".join(lines)
