import logging
from schwabdev import Client

logger = logging.getLogger(__name__)


class SchwabManager:
    def __init__(self, app_key: str, app_secret: str, callback_url: str):
        self.app_key = app_key
        self.app_secret = app_secret
        self.callback_url = callback_url
        self.client = None

    async def initialize(self):
        try:
            self.client = Client(
                app_key=self.app_key,
                app_secret=self.app_secret,
                callback_url=self.callback_url
            )
            logger.info("Schwab client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Schwab client: {e}")
            raise

    async def get_quote(self, symbol: str):
        return await self.client.quote(symbol)

    async def get_movers(self, index: str):
        return await self.client.movers(index)

    async def get_accounts(self):
        return await self.client.account_linked()

    async def get_account_details(self, account_hash: str, fields: str = None):
        return await self.client.account_details(account_hash, fields)

    async def place_order(self, account_hash: str, order_data: dict):
        return await self.client.place_order(account_hash, order_data)