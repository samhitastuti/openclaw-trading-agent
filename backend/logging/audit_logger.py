# Placeholder file for audit_logger.py
import json
import datetime
from pathlib import Path

log_file = Path(__file__).parent.parent / "audit_log.jsonl"

def log_decision(user, intent, action, status, reason):
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user": user,
        "intent": intent,
        "action": action,
        "status": status,
        "reason": reason
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def log_trade_decision(instruction: str, ai_classification: dict, policy_decision: dict, user: str = "api") -> None:
    """Log a full pipeline trade decision to the audit trail."""
    log_entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "user": user,
        "instruction": instruction,
        "ai_classification": ai_classification,
        "policy_decision": policy_decision,
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
