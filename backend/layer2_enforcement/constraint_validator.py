from backend.layer2_enforcement.policy_models import get_trade_policy


def validate_trade(action):
    policy = get_trade_policy()

    ticker = action.get("ticker")
    qty = action.get("quantity", 0)
    price = action.get("price", 0)

    value = qty * price

    # Ticker restriction — empty / missing allowed_tickers means no symbol cap
    raw_allowed = policy.get("allowed_tickers") or []
    allowed = raw_allowed if isinstance(raw_allowed, list) else []
    if allowed:
        allowed_u = {str(t).upper() for t in allowed}
        tk = (ticker or "").upper()
        if tk not in allowed_u:
            return False, f"Ticker '{ticker}' not allowed"

    # Max trade limit
    if value > policy.get("max_order_value", 0):
        return False, f"Trade value {value} exceeds limit"

    return True, "Valid trade"
