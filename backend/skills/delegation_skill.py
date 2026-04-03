"""
Skill: Handle agent-to-agent delegation.

Bonus Feature: Multi-agent delegation with scope boundaries.
"""

import logging
from typing import Dict, Any

from ..core.intent_models import Intent, DelegationContext


logger = logging.getLogger(__name__)


class DelegationSkill:
    """
    Manage delegation between agents.
    
    Example use case:
    1. Analyst agent: Research MSFT, recommend trade
    2. Trader agent: Receive recommendation, execute within scope
    3. DelegationSkill: Enforce trader's bounded authority
    
    Enforce:
    - Only trade the recommended ticker
    - Only up to recommended quantity
    - Only within trader's delegated limits
    """
    
    def __init__(self, delegation_policies: Dict):
        """Initialize with delegation policies"""
        self.delegation_policies = delegation_policies
        logger.info("✅ Delegation Skill initialized")
    
    async def validate_delegation(self, intent: Intent) -> Dict[str, Any]:
        """
        Validate delegated intent.
        
        Args:
            intent: Intent with delegation_context
        
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "delegator": str,
                "delegatee": str,
            }
        """
        if not intent.is_delegated():
            return {
                "allowed": True,
                "reason": "Not a delegated intent",
            }
        
        dc = intent.delegation_context
        delegation_key = f"{dc.delegator_id}->{dc.delegatee_id}"
        
        logger.info(f"🔗 Validating delegation: {delegation_key}")
        
        # Check if delegation exists
        if delegation_key not in self.delegation_policies:
            logger.warning(f"❌ No delegation policy for {delegation_key}")
            return {
                "allowed": False,
                "reason": f"No delegation policy between {dc.delegator_id} and {dc.delegatee_id}",
                "delegator": dc.delegator_id,
                "delegatee": dc.delegatee_id,
            }
        
        policy = self.delegation_policies[delegation_key]
        
        # Validate delegated constraints
        violations = []
        
        # Check trade size
        if intent.quantity and intent.limit_price:
            trade_value = intent.quantity * intent.limit_price
            if policy.max_trade_size and trade_value > policy.max_trade_size:
                violations.append(f"Trade ${trade_value} exceeds delegated max ${policy.max_trade_size}")
        
        # Check tickers
        if intent.ticker and policy.allowed_tickers:
            if intent.ticker.upper() not in policy.allowed_tickers:
                violations.append(f"Ticker {intent.ticker} not in delegated whitelist")
        
        # Check sub-delegation
        if policy.no_sub_delegation and intent.is_delegated():
            violations.append("Sub-delegation not permitted")
        
        if violations:
            logger.warning(f"❌ Delegation violation(s): {violations}")
            return {
                "allowed": False,
                "reason": " | ".join(violations),
                "delegator": dc.delegator_id,
                "delegatee": dc.delegatee_id,
            }
        
        logger.info(f"✅ Delegation validated")
        return {
            "allowed": True,
            "reason": "Delegated intent within authorized scope",
            "delegator": dc.delegator_id,
            "delegatee": dc.delegatee_id,
        }
    
    async def create_delegated_intent(
        self,
        original_intent: Intent,
        delegator_id: str,
        delegatee_id: str,
    ) -> Intent:
        """
        Create a delegated copy of an intent.
        
        Used when analyst recommends a trade to trader:
        analyst → trader intent
        """
        delegated_intent = Intent(
            type=original_intent.type,
            ticker=original_intent.ticker,
            side=original_intent.side,
            quantity=original_intent.quantity,
            limit_price=original_intent.limit_price,
            order_type=original_intent.order_type,
            raw_input=original_intent.raw_input,
            delegation_context=DelegationContext(
                delegator_id=delegator_id,
                delegatee_id=delegatee_id,
                scope="execute_trades",
            )
        )
        
        logger.info(f"🔗 Created delegated intent: {delegator_id} → {delegatee_id}")
        return delegated_intent