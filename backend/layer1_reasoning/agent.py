"""
agent.py — OpenClaw Agent Orchestrator (Reasoning Layer).

This is the central brain of the OpenClaw trading agent. It owns exactly
three responsibilities and NOTHING else:

  1. UNDERSTAND  — Parse raw user input into a structured Intent.
  2. GUARD       — Detect adversarial / prompt-injection attempts.
  3. ROUTE       — Send the Intent to enforcement, then (if allowed) to
                   the correct skill.

What this module does NOT do:
  ✗ Execute trades
  ✗ Call broker APIs
  ✗ Enforce policies
  ✗ Implement business rules

Dependency Injection
--------------------
All external collaborators (policy engine, skills, logger) are injected
at construction time, keeping this class fully testable in isolation.

Usage
-----
    from backend.core.agent import OpenClawAgent

    agent = OpenClawAgent(
        policy_engine=my_policy_engine,
        skills={
            "trading_skill":     my_trading_skill,
            "analysis_skill":    my_analysis_skill,
            "market_data_skill": my_market_data_skill,
        },
    )

    response = await agent.run("Buy 10 shares of AAPL", user_id="u_001")
    print(response.to_dict())
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional, Protocol, runtime_checkable

from .constants import (
    MAX_INPUT_LENGTH,
    SKILL_ANALYZE,
    SKILL_MARKET_DATA,
    SKILL_TRADE,
    SUSPICIOUS_KEYWORDS,
)
from .intent_models import (
    ActionSide,
    AgentResponse,
    EnforcementResult,
    Intent,
    IntentType,
)
from .intent_parser import parse_intent

# ─────────────────────────────────────────────
# Collaborator Protocols
# (Duck-typed interfaces so the agent never imports concrete implementations)
# ─────────────────────────────────────────────


@runtime_checkable
class PolicyEngine(Protocol):
    """
    Minimal interface the agent expects from the enforcement layer.
    Person 2 must implement a class compatible with this Protocol.
    """

    async def enforce(self, intent: Intent) -> EnforcementResult:
        """
        Evaluate the intent against all active policies.

        Returns an EnforcementResult with:
          allowed=True   → safe to proceed to skill execution
          allowed=False  → blocked; result.reason explains why
        """
        ...


@runtime_checkable
class Skill(Protocol):
    """
    Minimal interface the agent expects from each skill.
    Person 3 must implement skills compatible with this Protocol.
    """

    async def execute(self, intent: Intent) -> dict:
        """
        Execute the skill for the given intent.
        Must return a JSON-serialisable dict.
        """
        ...


# ─────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────


class OpenClawAgent:
    """
    Async orchestrator for the OpenClaw trading agent reasoning layer.

    Parameters
    ----------
    policy_engine : An object implementing the PolicyEngine protocol.
    skills        : Dict mapping skill-key → Skill instance.
                    Keys must include those defined in constants.py:
                      SKILL_TRADE, SKILL_ANALYZE, SKILL_MARKET_DATA
    logger        : Optional pre-configured logger (defaults to module logger).
    """

    def __init__(
        self,
        policy_engine: PolicyEngine,
        skills: dict[str, Skill],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._policy_engine = policy_engine
        self._skills = skills
        self._logger = logger or logging.getLogger(__name__)

        self._logger.info(
            "OpenClawAgent initialised | skills=%s",
            list(self._skills.keys()),
        )

    # ─────────────────────────────────────────
    # Primary Entry Point
    # ─────────────────────────────────────────

    async def run(
        self,
        raw_input: str,
        user_id: str = "anonymous",
    ) -> AgentResponse:
        """
        Full pipeline: raw text → Intent → enforcement → skill (if allowed).

        Flow
        ----
        1. Validate input length.
        2. Detect adversarial / injection keywords.
        3. Parse input → Intent  (returns error if unparseable).
        4. Send Intent to policy_engine.enforce().
        5a. Blocked → return AgentResponse.blocked().
        5b. Allowed → route to the correct skill.
        6. Return AgentResponse with skill result.

        All exceptions are caught and wrapped as AgentResponse.error()
        so callers always receive a structured response.
        """
        self._logger.info(
            "Agent.run() called | user=%s | input=%r",
            user_id,
            raw_input[:100],
        )

        try:
            # ── Step 1: Input length guard ─────────────────────────────────
            if len(raw_input) > MAX_INPUT_LENGTH:
                return AgentResponse.error(
                    f"Input exceeds maximum allowed length of {MAX_INPUT_LENGTH} characters.",
                )

            # ── Step 2: Adversarial input detection ────────────────────────
            adversarial_reason = self._detect_adversarial(raw_input)
            if adversarial_reason:
                self._logger.warning(
                    "Adversarial input detected | user=%s | reason=%s",
                    user_id,
                    adversarial_reason,
                )
                return AgentResponse.error(
                    f"Rejected: potentially unsafe input detected ({adversarial_reason}).",
                )

            # ── Step 3: Parse intent ───────────────────────────────────────
            intent = parse_intent(raw_input, user_id=user_id)
            if intent is None:
                self._logger.info(
                    "Intent parsing failed | user=%s | input=%r",
                    user_id,
                    raw_input[:80],
                )
                return AgentResponse.error(
                    "Could not understand the request. "
                    "Try: 'buy 10 AAPL', 'analyze MSFT', or 'price of GOOGL'."
                )

            self._logger.info("Intent parsed: %r", intent)

            # ── Step 4: Enforce ────────────────────────────────────────────
            enforcement: EnforcementResult = await self._policy_engine.enforce(intent)

            # ── Step 5a: Blocked ───────────────────────────────────────────
            if not enforcement.allowed:
                self._logger.info(
                    "Intent BLOCKED | intent_id=%s | reason=%s",
                    intent.intent_id,
                    enforcement.reason,
                )
                return AgentResponse.blocked(intent=intent, reason=enforcement.reason)

            # ── Step 5b: Allowed → route to skill ─────────────────────────
            self._logger.info(
                "Intent ALLOWED | intent_id=%s | routing to skill",
                intent.intent_id,
            )
            result = await self._route_to_skill(intent)
            return AgentResponse.success(intent=intent, result=result)

        except Exception as exc:  # Broad catch: agent must never crash the API layer
            self._logger.exception(
                "Unexpected error in Agent.run() | user=%s | error=%s",
                user_id,
                exc,
            )
            return AgentResponse.error(
                f"Internal agent error: {type(exc).__name__}: {exc}"
            )

    # ─────────────────────────────────────────
    # Multi-Step Reasoning
    # ─────────────────────────────────────────

    async def reason_then_execute(
        self,
        ticker: str,
        user_id: str = "anonymous",
        quantity: float = 10.0,
    ) -> AgentResponse:
        """
        Multi-step reasoning flow:
          1. Fetch current market data for the ticker.
          2. Run analysis on the ticker.
          3. If analysis signals BULLISH → construct a BUY intent.
             If analysis signals BEARISH → construct a SELL intent.
          4. Route the new trade intent through the FULL pipeline
             (enforcement → skill) so all policies still apply.

        This method demonstrates autonomous chained reasoning while
        respecting the hard constraint that enforcement is NEVER bypassed.

        Parameters
        ----------
        ticker   : Asset symbol to analyse and potentially trade.
        user_id  : Requesting user identifier.
        quantity : Number of shares for the potential trade.

        Returns
        -------
        AgentResponse — either the trade result or the block/error reason.
        """
        self._logger.info(
            "reason_then_execute | ticker=%s | user=%s | qty=%s",
            ticker,
            user_id,
            quantity,
        )

        # ── Step 1: Fetch market data ──────────────────────────────────────
        fetch_response = await self.run(
            f"price of {ticker}", user_id=user_id
        )
        if fetch_response.status != "success":
            return AgentResponse.error(
                f"Could not fetch market data for {ticker}: {fetch_response.reason}"
            )

        market_data: dict = fetch_response.result or {}
        self._logger.info("Market data fetched: %s", market_data)

        # ── Step 2: Run analysis ───────────────────────────────────────────
        analyze_response = await self.run(
            f"analyze {ticker}", user_id=user_id
        )
        if analyze_response.status != "success":
            return AgentResponse.error(
                f"Could not analyse {ticker}: {analyze_response.reason}"
            )

        analysis: dict = analyze_response.result or {}
        self._logger.info("Analysis result: %s", analysis)

        # ── Step 3: Determine trade direction from analysis signal ─────────
        signal: str = analysis.get("signal", "NEUTRAL").upper()

        if signal == "BULLISH":
            trade_side = ActionSide.BUY
        elif signal == "BEARISH":
            trade_side = ActionSide.SELL
        else:
            # Neutral signal → no trade
            return AgentResponse(
                status="success",
                intent=analyze_response.intent,
                result={
                    "action": "no_trade",
                    "reason": f"Analysis returned NEUTRAL signal for {ticker}.",
                    "market_data": market_data,
                    "analysis": analysis,
                },
            )

        # ── Step 4: Construct new trade intent & run full pipeline ─────────
        trade_intent = Intent(
            type=IntentType.EXECUTE_TRADE,
            ticker=ticker,
            quantity=quantity,
            side=trade_side,
            raw_input=f"[auto-generated by reason_then_execute] {trade_side.value} {quantity} {ticker}",
            user_id=user_id,
        )

        self._logger.info(
            "reason_then_execute: submitting auto trade intent %r",
            trade_intent,
        )

        # Enforcement is NOT bypassed — the auto-generated intent goes
        # through the same policy_engine.enforce() call as any manual trade.
        enforcement: EnforcementResult = await self._policy_engine.enforce(trade_intent)

        if not enforcement.allowed:
            return AgentResponse.blocked(
                intent=trade_intent,
                reason=f"Auto-trade blocked by policy: {enforcement.reason}",
            )

        skill_result = await self._route_to_skill(trade_intent)
        return AgentResponse.success(intent=trade_intent, result={
            **skill_result,
            "reasoning": {
                "signal": signal,
                "market_data": market_data,
                "analysis": analysis,
            },
        })

    # ─────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────

    def _detect_adversarial(self, raw_input: str) -> Optional[str]:
        """
        Scan the raw input for prompt-injection / credential-exfiltration
        keywords defined in constants.SUSPICIOUS_KEYWORDS.

        Returns the matched keyword (for logging) or None if clean.

        Case-insensitive comparison. Checks both whole-token and substring
        matches so "API_KEY" and "apikey" are both caught.
        """
        lowered = raw_input.lower()
        for keyword in SUSPICIOUS_KEYWORDS:
            if keyword.lower() in lowered:
                return keyword
        return None

    async def _route_to_skill(self, intent: Intent) -> dict:
        """
        Map IntentType → skill key → skill.execute(intent).

        Raises
        ------
        ValueError : If no skill is registered for the intent type, or if
                     the IntentType is UNKNOWN.
        """
        skill_key = self._resolve_skill_key(intent)

        if skill_key not in self._skills:
            raise ValueError(
                f"Skill '{skill_key}' is not registered. "
                f"Registered skills: {list(self._skills.keys())}"
            )

        skill = self._skills[skill_key]
        self._logger.info(
            "Routing intent_id=%s to skill=%s",
            intent.intent_id,
            skill_key,
        )

        result = await skill.execute(intent)
        return result

    @staticmethod
    def _resolve_skill_key(intent: Intent) -> str:
        """
        Pure mapping from IntentType to the corresponding skill registry key.

        Centralised here so adding a new IntentType only requires one change.
        """
        routing: dict[IntentType, str] = {
            IntentType.EXECUTE_TRADE: SKILL_TRADE,
            IntentType.ANALYZE:       SKILL_ANALYZE,
            IntentType.FETCH_DATA:    SKILL_MARKET_DATA,
        }

        key = routing.get(intent.type)
        if key is None:
            raise ValueError(
                f"No skill mapping defined for IntentType '{intent.type}'. "
                "Add it to _resolve_skill_key()."
            )
        return key

    # ─────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────

    def registered_skills(self) -> list[str]:
        """Return the list of currently registered skill keys."""
        return list(self._skills.keys())

    def update_skill(self, key: str, skill: Skill) -> None:
        """
        Hot-swap or add a skill at runtime (e.g. during testing).
        Does NOT require agent restart.
        """
        self._skills[key] = skill
        self._logger.info("Skill updated: %s", key)