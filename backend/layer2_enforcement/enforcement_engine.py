# Placeholder file for enforcement_engine.py
from backend.layer2_enforcement.constraint_validator import validate_trade
from backend.layer2_enforcement.decision_engine import make_decision
from backend.layer2_enforcement.policy_models import get_adversarial_policy
from backend.logging.audit_logger import log_decision


def detect_adversarial(intent):
    keywords = get_adversarial_policy().get("forbidden_keywords", [])

    intent_lower = intent.lower()

    for word in keywords:
        if word in intent_lower:
            return True, word

    return False, None


def enforce(intent, action, user="demo"):

    # 🔴 Step 1: Adversarial check
    bad, keyword = detect_adversarial(intent)
    if bad:
        result = make_decision(False, f"Adversarial input: {keyword}")
        log_decision(user, intent, action, result["decision"], result["reason"])
        return result

    # 🔵 Step 2: Validate action
    if action.get("type") == "trade":
        valid, reason = validate_trade(action)
    else:
        valid, reason = False, "Unknown action"

    # 🧠 Step 3: Decision
    result = make_decision(valid, reason)

    # 📝 Step 4: Logging
    log_decision(user, intent, action, result["decision"], result["reason"])

    return result