"""
AI Intent Classifier - Layer for semantic understanding + risk detection

This sits BETWEEN Layer 1 (Agent) and Layer 2 (Policy Engine).
Think of it as a semantic gateway that:
1. Understands what the user REALLY wants
2. Flags suspicious patterns early
3. Provides confidence scores

Two modes:
- OpenAI: Semantic + sophisticated threat detection
- Local NLP: Fast, deterministic, no API calls
"""

import logging
import json
import os
import re
from typing import Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================
# Ticker extraction helpers
# ============================================================

# Words that should never be interpreted as ticker symbols
_TICKER_EXCLUSIONS: frozenset = frozenset({
    "BUY", "SELL", "PURCHASE", "ACQUIRE", "LIQUIDATE", "EXIT",
    "GET", "SET", "AT", "THE", "ALL", "ANY", "FOR", "OF", "TO",
    "IN", "ON", "IS", "A", "AN", "MY", "ME", "US",
    "SHARES", "STOCK", "STOCKS", "UNITS", "SHARE", "UNIT",
    "ASAP", "NOW", "TODAY", "AND", "OR", "NOT",
    "ANALYZE", "ANALYSIS", "RESEARCH", "ASSESS", "CHECK",
    "BALANCE", "ACCOUNT", "POSITION", "TRANSFER", "SEND", "MOVE",
})

# Company name → ticker symbol mapping
_COMPANY_TICKER_MAP: dict = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "netflix": "NFLX",
    "paypal": "PYPL",
    "intel": "INTC",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "jpmorgan": "JPM",
    "goldman": "GS",
    "exxon": "XOM",
    "chevron": "CVX",
}

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️  OpenAI not installed. Using local NLP fallback.")


# ============================================================
# Risk Levels
# ============================================================

class RiskLevel(Enum):
    """Risk classification (increasing severity)"""
    SAFE = "safe"  # ✅ Normal operation
    CAUTION = "caution"  # ⚠️ Unusual but potentially valid
    HIGH_RISK = "high_risk"  # 🔴 Multiple risk signals
    CRITICAL = "critical"  # 🚨 Definite adversarial pattern


# ============================================================
# Main Classifier Class
# ============================================================

class IntentClassifier:
    """
    AI-powered intent classification.
    
    Public API:
        classifier = IntentClassifier()
        result = classifier.classify("Buy 10 MSFT")
    """
    
    def __init__(self):
        """Initialize classifier (auto-detects OpenAI availability)"""
        
        self.use_openai = OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY")
        
        if self.use_openai:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ IntentClassifier: Using OpenAI (gpt-3.5-turbo)")
        else:
            logger.info("✅ IntentClassifier: Using Local NLP (regex + keywords)")
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Main classification entry point.
        
        Args:
            user_input: User's natural language command
        
        Returns:
            Classification result dict
        """
        
        if self.use_openai:
            return self._classify_with_openai(user_input)
        else:
            return self._classify_with_local_nlp(user_input)
    
    # ============================================================
    # OPENAI CLASSIFICATION (Sophisticated)
    # ============================================================
    
    def _classify_with_openai(self, user_input: str) -> Dict[str, Any]:
        """Use GPT-3.5-turbo for semantic understanding + threat detection."""
        
        logger.info(f"🤖 OpenAI classification: {user_input[:60]}...")
        
        system_prompt = """You are a financial intent classifier for an autonomous trading agent.
Your job: Analyze user input and return a JSON classification.

Return ONLY valid JSON (no markdown, no explanation):
{
    "intent": "buy_stock" | "sell_stock" | "analyze" | "check_balance" | "unknown",
    "risk_level": "safe" | "caution" | "high_risk" | "critical",
    "confidence": 0.0-1.0,
    "extracted_data": {
        "ticker": "AAPL" or null,
        "qty": 100 or null,
        "price": 150.50 or null,
        "action": "buy" | "sell" | "analyze" or null
    },
    "risk_factors": ["list", "of", "detected", "risks"],
    "reasoning": "explanation of classification"
}

RISK LEVELS:
- safe: Normal trading within bounds
- caution: Unusual but potentially valid
- high_risk: Multiple risk signals
- critical: DEFINITE adversarial pattern (credential exposure, bypass attempts, etc.)
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Classify: {user_input}"}
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            response_text = response.choices[0].message.content
            
            try:
                classification = json.loads(response_text)
            except json.JSONDecodeError:
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                    classification = json.loads(json_str)
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                    classification = json.loads(json_str)
                else:
                    raise ValueError(f"Could not parse response: {response_text}")
            
            classification["ai_model"] = "openai"
            
            logger.info(f"✅ OpenAI result: {classification['intent']} ({classification['risk_level']})")
            return classification
        
        except Exception as e:
            logger.error(f"❌ OpenAI error: {e}")
            logger.info("⚠️  Falling back to local NLP...")
            return self._classify_with_local_nlp(user_input)
    
    # ============================================================
    # LOCAL NLP CLASSIFICATION (Fast + Deterministic)
    # ============================================================
    
    def _classify_with_local_nlp(self, user_input: str) -> Dict[str, Any]:
        """Fast, deterministic classification using regex + keyword matching."""
        
        logger.info(f"🔍 Local NLP classification: {user_input[:60]}...")
        
        result = {
            "intent": "unknown",
            "risk_level": "safe",
            "confidence": 0.5,
            "extracted_data": {},
            "risk_factors": [],
            "reasoning": "",
            "ai_model": "local_nlp",
        }
        
        user_lower = user_input.lower()
        
        # ========================================
        # STEP 1: DETECT CRITICAL THREATS
        # ========================================
        
        critical_patterns = [
            ("api_key", ["log", "print", "output", "write", "send", "expose"]),
            ("secret", ["log", "print", "expose", "send"]),
            ("password", ["log", "print", "expose"]),
            ("token", ["log", "send", "expose"]),
            ("credential", ["write", "log", "send", "expose"]),
            ("ignore", ["constraint", "policy", "limit", "rule"]),
            ("bypass", ["policy", "enforcement", "check", "constraint"]),
            ("override", ["limit", "constraint", "policy"]),
            ("delete", ["audit", "log", "record", "trail"]),
            ("disable", ["enforcement", "policy", "check"]),
        ]
        
        for keyword, combos in critical_patterns:
            if keyword in user_lower:
                for combo in combos:
                    if combo in user_lower:
                        result["risk_level"] = "critical"
                        result["risk_factors"].append(f"CRITICAL: '{keyword}' + '{combo}'")
                        result["confidence"] = 0.99
                        result["reasoning"] = f"Definite adversarial pattern: {keyword} + {combo}"
                        logger.warning(f"🚨 CRITICAL: {keyword} + {combo}")
                        return result
        
        # ========================================
        # STEP 2: DETECT HIGH-RISK PATTERNS
        # ========================================
        
        high_risk_keywords = [
            "bypass", "ignore", "override", "force",
            "all", "everything", "any", "maximum", "unlimited",
        ]
        
        high_risk_count = sum(1 for kw in high_risk_keywords if kw in user_lower)
        
        if high_risk_count >= 2:
            result["risk_level"] = "high_risk"
            result["risk_factors"].append(f"Multiple high-risk keywords ({high_risk_count})")
            result["confidence"] = 0.85
        
        # ========================================
        # STEP 3: DETECT UNUSUAL QUANTITIES
        # ========================================
        
        numbers = re.findall(r'\d+', user_input)
        if numbers:
            for num_str in numbers:
                num = int(num_str)
                if num > 1000:
                    result["risk_factors"].append(f"Unusually large quantity: {num}")
                    if result["risk_level"] == "safe":
                        result["risk_level"] = "caution"
                        result["confidence"] = 0.70
        
        # ========================================
        # STEP 4: CLASSIFY INTENT
        # ========================================
        
        if any(w in user_lower for w in ["buy", "purchase", "acquire"]):
            result["intent"] = "buy_stock"
            result["extracted_data"]["action"] = "buy"
        elif any(w in user_lower for w in ["sell", "liquidate", "exit"]):
            result["intent"] = "sell_stock"
            result["extracted_data"]["action"] = "sell"
        elif any(w in user_lower for w in ["analyze", "research", "assess"]):
            result["intent"] = "analyze"
            result["extracted_data"]["action"] = "analyze"
        elif any(w in user_lower for w in ["transfer", "send", "move"]):
            result["intent"] = "transfer"
            result["extracted_data"]["action"] = "transfer"
        elif any(w in user_lower for w in ["balance", "account", "position"]):
            result["intent"] = "check_balance"
            result["extracted_data"]["action"] = "check"
        
        # ========================================
        # STEP 5: EXTRACT QUANTITY AND TICKER
        # ========================================

        # Ticker priority 1: company name → ticker mapping checked before regex
        # so that multi-word names (e.g. "Microsoft") are caught even when the
        # ticker pattern would only capture a prefix ("Micro").
        for company, sym in _COMPANY_TICKER_MAP.items():
            if company in user_lower:
                result["extracted_data"]["ticker"] = sym
                break

        # Primary: extract qty and ticker together from a trade pattern so that
        # the action keyword (buy/sell) is never confused with a ticker symbol.
        trade_extract = re.search(
            r'(?:buy|sell|purchase|acquire|liquidate)\s+'
            r'(?P<qty>\d+(?:\.\d+)?)\s*'
            r'(?:shares?|units?|stocks?)?\s*(?:of\s+)?'
            r'(?P<ticker>[A-Za-z]{1,5})?',
            user_input,
            re.IGNORECASE,
        )
        if trade_extract:
            qty_val = trade_extract.group("qty")
            if qty_val:
                result["extracted_data"]["qty"] = float(qty_val)
            # Only set ticker from trade pattern if not already resolved via
            # company-name mapping above.
            if "ticker" not in result["extracted_data"]:
                ticker_val = trade_extract.group("ticker")
                if ticker_val:
                    candidate = ticker_val.upper()
                    if candidate not in _TICKER_EXCLUSIONS:
                        result["extracted_data"]["ticker"] = candidate

        # Fallback qty extraction if not already set (e.g. non-trade intents)
        if "qty" not in result["extracted_data"]:
            qty_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(?:shares?|units?|stocks?)?',
                user_input,
                re.IGNORECASE,
            )
            if qty_match:
                result["extracted_data"]["qty"] = float(qty_match.group(1))

        # Ticker fallback: any uppercase-only sequence that is not an exclusion
        if "ticker" not in result["extracted_data"]:
            for m in re.finditer(r'\b([A-Z]{1,5})\b', user_input):
                candidate = m.group(1)
                if candidate not in _TICKER_EXCLUSIONS:
                    result["extracted_data"]["ticker"] = candidate
                    break

        # ========================================
        # STEP 6: EXTRACT PRICE
        # ========================================

        price_match = re.search(r'(?:at|@|\$)\s*(\d+(?:\.\d+)?)', user_input)
        if price_match:
            result["extracted_data"]["price"] = float(price_match.group(1))
        
        # ========================================
        # STEP 7: FINALIZE REASONING
        # ========================================
        
        if result["risk_level"] == "safe":
            result["reasoning"] = f"Safe: Normal {result['intent']} request"
            result["confidence"] = 0.80
        elif result["risk_level"] == "caution":
            factors = ", ".join(result["risk_factors"][:2])
            result["reasoning"] = f"Caution: {factors}"
            result["confidence"] = 0.70
        elif result["risk_level"] == "high_risk":
            factors = ", ".join(result["risk_factors"][:2])
            result["reasoning"] = f"High Risk: {factors}"
            result["confidence"] = 0.85
        
        logger.info(f"✅ Local NLP result: {result['intent']} ({result['risk_level']})")
        return result


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_risk_color(risk_level: str) -> str:
    """Get HTML color for risk level (for UI)"""
    colors = {
        "safe": "#00ff88",
        "caution": "#ffaa00",
        "high_risk": "#ff6600",
        "critical": "#ff3d3d",
    }
    return colors.get(risk_level, "#ffffff")


def get_risk_emoji(risk_level: str) -> str:
    """Get emoji for risk level"""
    emojis = {
        "safe": "✅",
        "caution": "⚠️",
        "high_risk": "🔴",
        "critical": "🚨",
    }
    return emojis.get(risk_level, "❓")