"""
Skill: Multi-step market analysis with reasoning.

Implements:
✅ Multi-step reasoning (logged at each step)
✅ Technical analysis (simplified for demo)
✅ Recommendation generation
✅ Context for trade decisions
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..core.intent_models import Intent, IntentType


logger = logging.getLogger(__name__)


class AnalysisSkill:
    """
    Perform multi-step financial analysis.
    
    Demonstrates the reasoning layer:
    1. Fetch data
    2. Calculate metrics
    3. Evaluate signals
    4. Generate recommendation
    
    Usage:
        skill = AnalysisSkill(alpaca_client, market_data_skill)
        analysis = await skill.analyze_and_recommend(intent)
    """
    
    def __init__(self, alpaca_client, market_data_skill):
        """Initialize with dependencies"""
        self.alpaca = alpaca_client
        self.market_data_skill = market_data_skill
        logger.info("✅ Analysis Skill initialized")
    
    async def analyze_and_recommend(self, intent: Intent) -> Dict[str, Any]:
        """
        Multi-step analysis → recommendation.
        
        Args:
            intent: Intent with ticker
        
        Returns:
            {
                "status": "SUCCESS",
                "ticker": "MSFT",
                "current_price": 429.62,
                "recommendation": "BUY",
                "confidence": 0.85,
                "analysis_summary": "...",
                "analysis_steps": [...]
            }
        """
        ticker = intent.ticker
        analysis_steps = []
        
        logger.info(f"🔍 ANALYSIS START: {ticker}")
        logger.info(f"{'='*60}")
        
        try:
            # ========================================
            # STEP 1: Fetch current market data
            # ========================================
            logger.info("STEP 1: Fetching market data...")
            quote_result = await self.market_data_skill.get_market_data(intent)
            
            if quote_result.get("status") != "SUCCESS":
                logger.error(f"Step 1 ❌: {quote_result.get('error')}")
                return {
                    "status": "ERROR",
                    "error": f"Failed to fetch data: {quote_result.get('error')}",
                    "ticker": ticker,
                }
            
            current_price = quote_result["last"]
            step_1_msg = f"✅ Step 1: Fetched {ticker} = ${current_price}"
            analysis_steps.append(step_1_msg)
            logger.info(step_1_msg)
            
            # ========================================
            # STEP 2: Calculate technical indicators
            # ========================================
            logger.info("STEP 2: Calculating technical indicators...")
            volatility = self._calculate_volatility(ticker, current_price)
            momentum = self._calculate_momentum(ticker)
            trend_strength = self._calculate_trend_strength(ticker)
            
            step_2_msg = f"✅ Step 2: Volatility={volatility:.2f}, Momentum={momentum:.2f}, Trend={trend_strength:.2f}"
            analysis_steps.append(step_2_msg)
            logger.info(step_2_msg)
            
            # ========================================
            # STEP 3: Evaluate buy/sell signals
            # ========================================
            logger.info("STEP 3: Evaluating signals...")
            buy_signals = 0
            sell_signals = 0
            
            if momentum > 0.6:
                buy_signals += 1
                analysis_steps.append("  📈 Positive momentum signal")
            
            if trend_strength > 0.7:
                buy_signals += 1
                analysis_steps.append("  📈 Strong uptrend signal")
            
            if volatility > 0.8:
                sell_signals += 1
                analysis_steps.append("  ⚠️  High volatility warning")
            
            step_3_msg = f"✅ Step 3: {buy_signals} buy signals, {sell_signals} sell signals"
            analysis_steps.append(step_3_msg)
            logger.info(step_3_msg)
            
            # ========================================
            # STEP 4: Generate recommendation
            # ========================================
            logger.info("STEP 4: Generating recommendation...")
            
            # Simple heuristic: more buy signals = buy
            signal_ratio = buy_signals / (buy_signals + sell_signals + 1)
            
            if signal_ratio > 0.66:
                recommendation = "BUY"
                confidence = min(0.95, 0.5 + signal_ratio)
            elif signal_ratio < 0.33:
                recommendation = "SELL"
                confidence = min(0.95, 0.5 + (1 - signal_ratio))
            else:
                recommendation = "HOLD"
                confidence = 0.60
            
            step_4_msg = f"✅ Step 4: Recommendation = {recommendation} (confidence: {confidence:.0%})"
            analysis_steps.append(step_4_msg)
            logger.info(step_4_msg)
            
            # ========================================
            # STEP 5: Create summary
            # ========================================
            summary = f"{ticker} @ ${current_price}: {recommendation} signal ({buy_signals} buy, {sell_signals} sell)"
            
            response = {
                "status": "SUCCESS",
                "ticker": ticker,
                "current_price": current_price,
                "recommendation": recommendation,
                "confidence": confidence,
                "analysis_summary": summary,
                "analysis_steps": analysis_steps,
                "signals": {
                    "buy": buy_signals,
                    "sell": sell_signals,
                }
            }
            
            logger.info(f"{'='*60}")
            logger.info(f"✅ ANALYSIS COMPLETE: {recommendation}")
            return response
        
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "ticker": ticker,
            }
    
    # ================================================
    # TECHNICAL ANALYSIS (Simplified for demo)
    # ================================================
    
    def _calculate_volatility(self, ticker: str, price: float) -> float:
        """
        Calculate volatility (0.0-1.0).
        
        In production: use historical prices, std dev, etc.
        For demo: heuristic based on price level
        """
        # Higher prices = typically lower volatility
        if price > 500:
            return 0.25  # Large cap, low volatility
        elif price > 200:
            return 0.50  # Mid cap, medium volatility
        elif price > 50:
            return 0.70  # Small cap, high volatility
        else:
            return 0.90  # Micro cap, very high volatility
    
    def _calculate_momentum(self, ticker: str) -> float:
        """
        Calculate momentum (0.0-1.0).
        
        In production: RSI, MACD, etc.
        For demo: ticker-based heuristic
        """
        momentum_map = {
            "AAPL": 0.65,
            "MSFT": 0.75,
            "GOOGL": 0.60,
            "AMZN": 0.70,
            "NVDA": 0.80,
        }
        return momentum_map.get(ticker.upper(), 0.55)
    
    def _calculate_trend_strength(self, ticker: str) -> float:
        """Calculate trend strength (0.0-1.0)"""
        trend_map = {
            "AAPL": 0.60,
            "MSFT": 0.75,
            "GOOGL": 0.55,
            "AMZN": 0.70,
            "NVDA": 0.85,
        }
        return trend_map.get(ticker.upper(), 0.50)