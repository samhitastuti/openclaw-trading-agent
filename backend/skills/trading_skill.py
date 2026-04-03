"""
Skill: Execute trades on Alpaca with enforcement.

Implements:
✅ Real Alpaca order submission
✅ Double-check enforcement (defense-in-depth)
✅ Order tracking and logging
✅ Error handling
"""

import logging
from typing import Dict, Any
from datetime import datetime

from ..core.intent_models import Intent, IntentType


logger = logging.getLogger(__name__)


class TradingSkill:
    """
    Execute trades with policy enforcement.
    
    Defense-in-depth:
    1. Intent already checked by Person 2's enforcement (before this skill)
    2. This skill double-checks enforcement
    3. Submits to real Alpaca API
    4. Logs execution result
    
    Usage:
        skill = TradingSkill(policy_engine, alpaca_client, audit_logger)
        result = await skill.execute_trade(intent)
    """
    
    def __init__(self, policy_engine, alpaca_client, audit_logger):
        """Initialize with all dependencies"""
        self.policy_engine = policy_engine
        self.alpaca = alpaca_client
        self.audit_logger = audit_logger
        logger.info("✅ Trading Skill initialized")
    
    async def execute_trade(self, intent: Intent) -> Dict[str, Any]:
        """
        Execute trade with multi-layer enforcement.
        
        Args:
            intent: TradeIntent (already checked by policy engine)
        
        Returns:
            {
                "status": "SUCCESS" | "REJECTED" | "ERROR",
                "order_id": "...",
                ...
            }
        """
        ticker = intent.ticker
        logger.info(f"\n{'='*60}")
        logger.info(f"🤖 TRADE EXECUTION: {intent.side.value} {intent.quantity} {ticker}")
        logger.info(f"{'='*60}")
        
        # ========================================
        # DEFENSE-IN-DEPTH: STEP 1 - Re-check enforcement
        # ========================================
        logger.info("STEP 1: Re-checking policy enforcement (defense-in-depth)...")
        
        decision = self.policy_engine.enforce(intent)
        
        if not decision.allowed:
            logger.warning(f"STEP 1 ❌: Trade rejected - {decision.reason}")
            return {
                "status": "REJECTED",
                "reason": decision.reason,
                "constraint": decision.constraint_violated,
                "enforcement_level": "HARD_BLOCK",
                "ticker": ticker,
            }
        
        logger.info(f"STEP 1 ✅: Enforcement passed - {decision.reason}")
        
        # ========================================
        # STEP 2 - Prepare order parameters
        # ========================================
        logger.info("STEP 2: Preparing order parameters...")
        
        order_params = {
            "symbol": ticker,
            "qty": int(intent.quantity),
            "side": intent.side.value,
            "type": intent.order_type,
        }
        
        if intent.order_type == "limit" and intent.limit_price:
            order_params["limit_price"] = intent.limit_price
        
        logger.info(f"STEP 2 ✅: Order params: {order_params}")
        
        # ========================================
        # STEP 3 - Submit to Alpaca (Real API!)
        # ========================================
        logger.info("STEP 3: Submitting to Alpaca paper trading API...")
        
        try:
            order = await self.alpaca.submit_order(**order_params)
            
            logger.info(f"STEP 3 ✅: Order submitted - ID: {order['order_id']}")
            
            # ========================================
            # STEP 4 - Log execution
            # ========================================
            logger.info("STEP 4: Logging execution to audit trail...")
            
            self.audit_logger.log_execution({
                "status": "EXECUTED",
                "order_id": order["order_id"],
                "intent": intent.to_dict(),
                "order": order,
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            logger.info(f"STEP 4 ✅: Execution logged")
            
            # ========================================
            # STEP 5 - Record trade for daily tracking
            # ========================================
            logger.info("STEP 5: Recording trade for daily limits...")
            
            self.policy_engine.record_trade(intent)
            
            logger.info(f"STEP 5 ✅: Trade recorded")
            
            # ========================================
            # RETURN SUCCESS
            # ========================================
            logger.info(f"{'='*60}")
            logger.info(f"✅ TRADE EXECUTED SUCCESSFULLY")
            logger.info(f"{'='*60}\n")
            
            return {
                "status": "SUCCESS",
                "order_id": order["order_id"],
                "ticker": ticker,
                "qty": intent.quantity,
                "side": intent.side.value,
                "order_type": intent.order_type,
                "limit_price": intent.limit_price,
                "order_status": order.get("status"),
                "created_at": order.get("created_at"),
            }
        
        except Exception as e:
            logger.error(f"STEP 3 ❌: Alpaca error: {e}")
            
            # Log error
            self.audit_logger.log_execution({
                "status": "ERROR",
                "error": str(e),
                "intent": intent.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            logger.info(f"{'='*60}")
            logger.info(f"❌ TRADE FAILED")
            logger.info(f"{'='*60}\n")
            
            return {
                "status": "ERROR",
                "error": str(e),
                "ticker": ticker,
                "error_type": type(e).__name__,
            }