# Placeholder file for decision_engine.py
def make_decision(valid, reason):
    if valid:
        return {
            "decision": "ALLOW",
            "reason": reason
        }
    else:
        return {
            "decision": "DENY",
            "reason": reason
        }
