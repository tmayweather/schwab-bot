print(client.movers("$DJI").json())

def get_market_movers(client, index, top_n=5):
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

    try:
        # Call the API
        data = client.movers(index).json()   # note the () after json

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

   
