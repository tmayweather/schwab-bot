from quotes import get_formatted_quotes
import os
import logging
from dotenv import load_dotenv
import schwabdev

def main():
    load_dotenv()

    if len(os.getenv('app_key')) != 32 or len(os.getenv('app_secret')) != 16:
        raise Exception("Add your app key and app secret to the .env file.")

    logging.basicConfig(level=logging.INFO)

    client = schwabdev.Client(
        os.getenv('app_key'),
        os.getenv('app_secret'),
        os.getenv('callback_url')
    )

    # Prompt the user for symbols, space-separated
    symbols_input = input("Enter symbol(s), separated by spaces: ").strip().upper()
    symbols = symbols_input.split()

    get_formatted_quotes(client, symbols)

if __name__ == '__main__':
    print("Welcome to Mambalab Trader")
    main()
