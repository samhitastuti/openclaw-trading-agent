"""
AI Intent Classifier - Layer for semantic understanding + risk detection

This sits BETWEEN Layer 1 (Agent) and Layer 2 (Policy Engine).
Think of it as a semantic gateway that:
1. Understands what the user REALLY wants
2. Flags suspicious patterns early
3. Provides confidence scores

Four modes (priority order):
- OpenClaw: Local AI gateway (http://127.0.0.1:18789) using Kimi model
- Ollama/Mistral: Free, locally-running AI (http://localhost:11434)
- OpenAI: Semantic + sophisticated threat detection
- Local NLP: Fast, deterministic, no API calls
"""

import logging
import json
import os
import re
import urllib.request
import urllib.error
from typing import Dict, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================
# OpenClaw configuration
# ============================================================

OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "http://127.0.0.1:18789")
# The 'ollama/' prefix is required by the OpenClaw gateway to route the request
# to the locally-running Ollama instance. See the OpenClaw gateway documentation.
OPENCLAW_MODEL = os.getenv("OPENCLAW_MODEL", "ollama/kimi-k2.5:cloud")


def _openclaw_is_available() -> bool:
    """Return True if the OpenClaw gateway is reachable."""
    try:
        req = urllib.request.Request(
            f"{OPENCLAW_BASE_URL}/v1/models",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


# ============================================================
# Ollama configuration
# ============================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


def _ollama_is_available() -> bool:
    """Return True if the Ollama server is reachable."""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/tags",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:  # ← Changed from 2 to 5
            return resp.status == 200
    except Exception as e:
        logger.warning(f"⚠️ Ollama probe failed: {e}")  # ← Add logging
        return False

# ============================================================
# Module-level constants for local NLP extraction
# ============================================================

# Uppercase words to skip when falling back to a bare ticker search,
# so that action verbs like "BUY" or "SELL" are never mistaken for tickers.
_TICKER_SKIP_WORDS: set[str] = {"BUY", "SELL", "AT", "FOR", "OF", "THE"}

# Common company names → canonical ticker symbols.
# Used when the user writes the full company name rather than the symbol.
_COMPANY_TO_TICKER: dict[str, str] = {
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
    "adobe": "ADBE",
    "salesforce": "CRM",
    "oracle": "ORCL",
    "intel": "INTC",
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
        """Initialize classifier (auto-detects OpenClaw, then Ollama, then OpenAI)"""
        
        # ---- OpenClaw ----
        use_openclaw_env = os.getenv("USE_OPENCLAW", "auto").lower()
        if use_openclaw_env == "true":
            self.use_openclaw = True
        elif use_openclaw_env == "false":
            self.use_openclaw = False
        else:  # "auto" – probe the server
            self.use_openclaw = _openclaw_is_available()

        if self.use_openclaw:
            logger.info(
                f"✅ IntentClassifier: Using OpenClaw ({OPENCLAW_MODEL}) at {OPENCLAW_BASE_URL}"
            )

        # ---- Ollama ----
        use_ollama_env = os.getenv("USE_OLLAMA", "auto").lower()
        if use_ollama_env == "true":
            self.use_ollama = True
        elif use_ollama_env == "false":
            self.use_ollama = False
        else:  # "auto" – probe the server
            self.use_ollama = _ollama_is_available()

        if self.use_ollama and not self.use_openclaw:
            logger.info(
                f"✅ IntentClassifier: Using Ollama ({OLLAMA_MODEL}) at {OLLAMA_BASE_URL}"
            )

        # ---- OpenAI ----
        self.use_openai = OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY"))
        
        if self.use_openai:
            base_url = os.getenv("OPENAI_BASE_URL")
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=base_url
            )
            logger.info(f"✅ IntentClassifier: Using OpenAI (gpt-3.5-turbo) with base_url={base_url or 'default'}")
        else:
            self.client = None
        
        if not self.use_openclaw and not self.use_ollama and not self.use_openai:
            logger.info("✅ IntentClassifier: Using Local NLP (regex + keywords)")
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Main classification entry point.
        
        Priority: OpenClaw > Ollama > OpenAI > Local NLP

        Args:
            user_input: User's natural language command
        
        Returns:
            Classification result dict
        """
        
        if self.use_openclaw:
            return self._classify_with_openclaw(user_input)
        elif self.use_ollama:
            return self._classify_with_ollama(user_input)
        elif self.use_openai:
            return self._classify_with_openai(user_input)
        else:
            return self._classify_with_local_nlp(user_input)
    
    # ============================================================
    # OPENCLAW CLASSIFICATION (Local AI Gateway – Kimi model)
    # ============================================================

    def _classify_with_openclaw(self, user_input: str) -> Dict[str, Any]:
        """Use the OpenClaw local AI gateway (Kimi model) for classification.

        OpenClaw exposes an OpenAI-compatible /v1/chat/completions endpoint.
        """

        logger.info(f"🦅 OpenClaw classification: {user_input[:60]}...")

        system_prompt = (
            "You are a financial intent classifier for an autonomous trading agent.\n"
            "Your job: Analyze user input and return a JSON classification.\n\n"
            "Return ONLY valid JSON (no markdown, no explanation):\n"
            "{\n"
            '    "intent": "buy_stock" | "sell_stock" | "analyze" | "check_balance" | "unknown",\n'
            '    "risk_level": "safe" | "caution" | "high_risk" | "critical",\n'
            '    "confidence": 0.0-1.0,\n'
            '    "extracted_data": {\n'
            '        "ticker": "AAPL" or null,\n'
            '        "qty": 100 or null,\n'
            '        "price": 150.50 or null,\n'
            '        "action": "buy" | "sell" | "analyze" or null\n'
            "    },\n"
            '    "risk_factors": ["list", "of", "detected", "risks"],\n'
            '    "reasoning": "explanation of classification"\n'
            "}\n\n"
            "RISK LEVELS:\n"
            "- safe: Normal trading within bounds\n"
            "- caution: Unusual but potentially valid\n"
            "- high_risk: Multiple risk signals\n"
            "- critical: DEFINITE adversarial pattern (credential exposure, bypass attempts, etc.)"
        )

        payload = json.dumps({
            "model": OPENCLAW_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify: {user_input}"},
            ],
            "stream": False,
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                f"{OPENCLAW_BASE_URL}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                response_body = resp.read().decode("utf-8")

            response_json = json.loads(response_body)
            response_text = response_json["choices"][0]["message"]["content"]

            try:
                classification = json.loads(response_text)
            except json.JSONDecodeError:
                # Strip markdown code fences if the model wrapped its response
                parts_json = response_text.split("```json")
                parts_plain = response_text.split("```")
                if len(parts_json) >= 2 and "```" in parts_json[1]:
                    json_str = parts_json[1].split("```")[0].strip()
                    classification = json.loads(json_str)
                elif len(parts_plain) >= 3:
                    json_str = parts_plain[1].strip()
                    classification = json.loads(json_str)
                else:
                    raise ValueError(
                        "Could not parse OpenClaw response as JSON "
                        f"(tried raw and markdown-fenced formats): "
                        f"{response_text[:100]}..."
                    )

            classification["ai_model"] = "openclaw"

            logger.info(
                f"✅ OpenClaw result: {classification['intent']} ({classification['risk_level']})"
            )
            return classification

        except Exception as e:
            logger.error(f"❌ OpenClaw error: {e}")
            logger.info("⚠️  Falling back to Ollama, OpenAI or local NLP...")
            if self.use_ollama:
                return self._classify_with_ollama(user_input)
            if self.use_openai:
                return self._classify_with_openai(user_input)
            return self._classify_with_local_nlp(user_input)

    # ============================================================
    # OLLAMA CLASSIFICATION (Free local AI – Mistral)
    # ============================================================

    def _classify_with_ollama(self, user_input: str) -> Dict[str, Any]:
        """Use the local Ollama/Mistral model for classification."""

        logger.info(f"🦙 Ollama classification: {user_input[:60]}...")

        system_prompt = (
            "You are a financial intent classifier for an autonomous trading agent.\n"
            "Your job: Analyze user input and return a JSON classification.\n\n"
            "Return ONLY valid JSON (no markdown, no explanation):\n"
            "{\n"
            '    "intent": "buy_stock" | "sell_stock" | "analyze" | "check_balance" | "unknown",\n'
            '    "risk_level": "safe" | "caution" | "high_risk" | "critical",\n'
            '    "confidence": 0.0-1.0,\n'
            '    "extracted_data": {\n'
            '        "ticker": "AAPL" or null,\n'
            '        "qty": 100 or null,\n'
            '        "price": 150.50 or null,\n'
            '        "action": "buy" | "sell" | "analyze" or null\n'
            "    },\n"
            '    "risk_factors": ["list", "of", "detected", "risks"],\n'
            '    "reasoning": "explanation of classification"\n'
            "}\n\n"
            "RISK LEVELS:\n"
            "- safe: Normal trading within bounds\n"
            "- caution: Unusual but potentially valid\n"
            "- high_risk: Multiple risk signals\n"
            "- critical: DEFINITE adversarial pattern (credential exposure, bypass attempts, etc.)"
        )

        payload = json.dumps({
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify: {user_input}"},
            ],
            "stream": False,
        }).encode("utf-8")

        try:
            logger.info(f"📤 Sending to Ollama: {OLLAMA_BASE_URL}/api/chat")
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/chat",  # ✅ CORRECT ENDPOINT
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            # ✅ INCREASED TIMEOUT - Ollama can be slow on first request
            with urllib.request.urlopen(req, timeout=120) as resp:
                response_body = resp.read().decode("utf-8")

logger.info(f"📥 Ollama response: {resp.status}")
response_json = json.loads(response_body)
logger.info(f"📋 Full Ollama JSON response: {response_body[:500]}")  # Log raw response
response_text = response_json.get("message", {}).get("content", "")
logger.info(f"📝 Ollama content: {response_text}")
            try:
                classification = json.loads(response_text)
            except json.JSONDecodeError:
                # Strip markdown code fences if the model wrapped its response
                parts_json = response_text.split("```json")
                parts_plain = response_text.split("```")
                if len(parts_json) >= 2 and "```" in parts_json[1]:
                    json_str = parts_json[1].split("```")[0].strip()
                    classification = json.loads(json_str)
                elif len(parts_plain) >= 3:
                    json_str = parts_plain[1].strip()
                    classification = json.loads(json_str)
                else:
                    raise ValueError(
                        "Could not parse Ollama response as JSON "
                        f"(tried raw and markdown-fenced formats): "
                        f"{response_text[:100]}..."
                    )

            classification["ai_model"] = "ollama"

            logger.info(
                f"✅ Ollama result: {classification['intent']} ({classification['risk_level']})"
            )
            return classification

        except Exception as e:
            logger.error(f"❌ Ollama error: {e}")
            logger.info("⚠️  Falling back to local NLP...")
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
                parts_json = response_text.split("```json")
                parts_plain = response_text.split("```")
                if len(parts_json) >= 2 and "```" in parts_json[1]:
                    json_str = parts_json[1].split("```")[0].strip()
                    classification = json.loads(json_str)
                elif len(parts_plain) >= 3:
                    json_str = parts_plain[1].strip()
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

        user_lower = user_input.lower()
        logger.info(f"🔍 Input text: '{user_input}' | Lowercase: '{user_lower}'")
        
        result = {
            "intent": "unknown",
            "risk_level": "safe",
            "confidence": 0.5,
            "extracted_data": {},
            "risk_factors": [],
            "reasoning": "",
            "ai_model": "local_nlp",
        }
        
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

        logger.info(
            f"📍 Intent detected: {result['intent']} | Action: {result['extracted_data'].get('action')}"
        )

        # ========================================
        # STEP 5: EXTRACT TICKER + QUANTITY
        # ========================================
        # Primary strategy: match qty and ticker together so that uppercase
        # action words (BUY/SELL) before the number are never confused with
        # the ticker symbol.
        # Handles patterns like:
        #   "50 AAPL", "50 shares AAPL", "50 shares of AAPL"
        logger.info("🔄 Attempting PRIMARY qty+ticker regex match...")
        qty_ticker_match = re.search(
            r'(\d+(?:\.\d+)?)\s+(?:shares?\s+(?:of\s+)?|units?\s+(?:of\s+)?)?([A-Z]{1,5})\b',
            user_input,
        )
        if qty_ticker_match:
            result["extracted_data"]["qty"] = float(qty_ticker_match.group(1))
            result["extracted_data"]["ticker"] = qty_ticker_match.group(2)
            logger.info(
                f"✅ PRIMARY match: qty={result['extracted_data']['qty']}, "
                f"ticker={result['extracted_data']['ticker']}"
            )
        else:
            logger.info("❌ PRIMARY qty+ticker regex failed — using fallback extraction")

            # Fallback: extract quantity alone
            qty_match = re.search(r'(\d+(?:\.\d+)?)', user_input)
            if qty_match:
                result["extracted_data"]["qty"] = float(qty_match.group(1))
                logger.info(f"💰 Fallback qty found: {result['extracted_data']['qty']}")
            else:
                logger.info("💰 Fallback qty found: None")

            # Fallback: extract ticker, skipping common action/preposition words
            skipped_words: list[str] = []
            found_ticker: str | None = None
            for m in re.finditer(r'\b([A-Z]{1,5})\b', user_input):
                word = m.group(1)
                if word in _TICKER_SKIP_WORDS:
                    skipped_words.append(word)
                else:
                    found_ticker = word
                    result["extracted_data"]["ticker"] = word
                    break
            logger.info(
                f"🎯 Fallback ticker (before company mapping): {result['extracted_data'].get('ticker')}"
            )

            if found_ticker:
                logger.info(
                    f"  → Fallback ticker search: Found ticker={found_ticker}"
                    + (f", skipped {skipped_words}" if skipped_words else "")
                )
            else:
                logger.info(
                    f"  → Fallback ticker search: Found uppercase words but skipped {skipped_words}"
                )

        # Company name → ticker fallback (e.g. "Apple" → "AAPL")
        if "ticker" not in result["extracted_data"]:
            logger.info("🏢 No ticker found yet — attempting company name mapping...")
            for company, sym in _COMPANY_TO_TICKER.items():
                if company in user_lower:
                    result["extracted_data"]["ticker"] = sym
                    logger.info(f"🏢 Company name '{company}' → ticker '{sym}'")
                    break
            else:
                logger.info("🏢 No company name matched in input")
        else:
            logger.info(
                f"🏢 Skipping company mapping — ticker already set: {result['extracted_data']['ticker']}"
            )

        logger.info(f"📊 Extracted data before price: {result['extracted_data']}")

        # ========================================
        # STEP 6: EXTRACT PRICE
        # ========================================

        price_match = re.search(r'(?:at|@|\$)\s*(\d+(?:\.\d+)?)', user_input)
        if price_match:
            result["extracted_data"]["price"] = float(price_match.group(1))

        logger.info(f"📊 Final extracted data: {result['extracted_data']}")

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

        logger.info(
            f"✅ FINAL: intent={result['intent']}, "
            f"ticker={result['extracted_data'].get('ticker')}, "
            f"qty={result['extracted_data'].get('qty')}, "
            f"risk={result['risk_level']}, "
            f"conf={result['confidence']}"
        )
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
