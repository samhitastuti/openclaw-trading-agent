"""
Alpaca Trading API Client
Real HTTP calls to paper trading account (NO MOCKING)
"""

import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional
from datetime import datetime, timezone

import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Thread pool for running blocking Alpaca SDK calls without blocking the event loop
_executor = ThreadPoolExecutor(max_workers=4)


class AlpacaClient:
    """
    Real Alpaca paper trading client.

    NO MOCKING. Real HTTP calls.
    Handles:
    - Authentication
    - Market data fetching
    - Order submission
    - Account management
    - Position retrieval

    All async methods use a ThreadPoolExecutor so the event loop is never
    blocked by synchronous SDK calls.
    """

    def __init__(self):
        """Initialize with credentials from .env"""

        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        if not self.api_key or not self.secret_key:
            raise ValueError("ALPACA_API_KEY and ALPACA_SECRET_KEY required in .env")

        # Connect to real Alpaca API
        try:
            self.api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.secret_key,
                base_url=self.base_url,
            )
            logger.info("✅ Connected to Alpaca paper trading")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Alpaca: {e}")
            raise

    # ------------------------------------------------------------------
    # Internal helper: run a blocking callable in the thread pool so that
    # the asyncio event loop is not blocked.
    # ------------------------------------------------------------------

    async def _run_in_executor(self, func, *args):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, func, *args)

    async def get_latest_quote(self, symbol: str) -> Dict:
        """
        Fetch latest market quote.

        Real API call to:
        GET https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest

        Args:
            symbol: Ticker symbol (e.g., "MSFT")

        Returns:
            {
                "bid": float,
                "ask": float,
                "last": float,
                "timestamp": str (ISO 8601)
            }
        """
        try:
            quote = await self._run_in_executor(self.api.get_latest_quote, symbol)

            if not quote:
                raise ValueError(f"No quote available for {symbol}")

            bid = float(quote.bidprice)
            ask = float(quote.askprice)

            return {
                "bid": bid,
                "ask": ask,
                "last": (bid + ask) / 2,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise

    async def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        type: str = "market",
        limit_price: Optional[float] = None,
    ) -> Dict:
        """
        Submit order to Alpaca.

        Real API call to:
        POST https://paper-api.alpaca.markets/v2/orders

        Args:
            symbol: Ticker symbol (e.g., "MSFT")
            qty: Quantity of shares
            side: "buy" or "sell"
            type: "market" or "limit"
            limit_price: Price limit (required if type="limit")

        Returns:
            {
                "order_id": str,
                "status": str,
                "symbol": str,
                "qty": int,
                "side": str,
                "created_at": str (ISO 8601)
            }
        """
        try:
            order_kwargs = {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "type": type,
                "time_in_force": "day",
            }

            if type == "limit" and limit_price is not None:
                order_kwargs["limit_price"] = limit_price

            def _submit():
                return self.api.submit_order(**order_kwargs)

            order = await self._run_in_executor(_submit)

            return {
                "order_id": order.id,
                "status": order.status,
                "symbol": order.symbol,
                "qty": int(order.qty),
                "side": order.side,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        except Exception as e:
            logger.error(f"Failed to submit order: {e}")
            raise

    async def get_account(self) -> Dict:
        """
        Get account information.

        Real API call to:
        GET https://paper-api.alpaca.markets/v2/account

        Returns:
            {
                "cash": float,
                "portfolio_value": float,
                "buying_power": float,
            }
        """
        try:
            account = await self._run_in_executor(self.api.get_account)

            return {
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "buying_power": float(account.buying_power),
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    async def get_positions(self) -> List[Dict]:
        """
        Get all open positions.

        Real API call to:
        GET https://paper-api.alpaca.markets/v2/positions

        Returns:
            List of position dicts:
            [
                {
                    "symbol": str,
                    "qty": int,
                    "avg_entry_price": float,
                    "current_price": float,
                    "market_value": float,
                    "unrealized_pl": float,
                    "unrealized_plpc": float,
                    "side": str,
                }
            ]
        """
        try:
            positions = await self._run_in_executor(self.api.list_positions)

            return [
                {
                    "symbol": pos.symbol,
                    "qty": int(pos.qty),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "market_value": float(pos.market_value),
                    "unrealized_pl": float(pos.unrealized_pl),
                    "unrealized_plpc": float(pos.unrealized_plpc),
                    "side": pos.side,
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise