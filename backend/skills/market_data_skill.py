"""
Skill: Fetch live market data from Alpaca.

No enforcement needed (read-only).
But log all requests for audit trail.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..core.intent_models import Intent, IntentType


logger = logging.getLogger(__name__)


class MarketDataSkill:
    """
    Fetch real-time market quotes from Alpaca.
    
    No security enforcement needed (read-only, no state change).
    But log all data fetches for auditability.
    
    Usage:
        skill = MarketDataSkill(alpaca_client)
        quote = await skill.get_market_data(intent)
    """
    
    def __init__(self, alpaca_client):
        """Initialize with Alpaca client (from Person 4)"""
        self.alpaca = alpaca_client
        logger.info("✅ Market Data Skill initialized")
    
    async def get_market_data(self, intent: Intent) -> Dict[str, Any]:
        """
        Fetch market data for ticker.
        
        Args:
            intent: Intent with ticker specified
        
        Returns:
            {
                "status": "SUCCESS",
                "ticker": "MSFT",
                "bid": 429.50,
                "ask": 429.75,
                "last": 429.62,
                "timestamp": "2026-04-03T14:35:22Z"
            }
        """
        ticker = intent.ticker
        
        logger.info(f"📊 Step 1: Fetching market data for {ticker}...")
        
        try:
            # Call real Alpaca API (from Person 4)
            quote = await self.alpaca.get_latest_quote(ticker)
            
            logger.info(f"📊 Step 2: Got quote - bid={quote['bid']}, ask={quote['ask']}")
            
            response = {
                "status": "SUCCESS",
                "ticker": ticker,
                "bid": quote["bid"],
                "ask": quote["ask"],
                "last": quote["last"],
                "timestamp": quote["timestamp"],
            }
            
            logger.info(f"✅ Market data fetched successfully: {ticker} = ${response['last']}")
            return response
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch market data: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "ticker": ticker,
            }