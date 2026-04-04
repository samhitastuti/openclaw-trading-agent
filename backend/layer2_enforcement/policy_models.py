import yaml
from pathlib import Path

# Policy file under backend/config/ — re-read on each access so edits apply
# without restarting the API process.
policy_path = Path(__file__).resolve().parent.parent / "config" / "policies.yaml"


def _load_policies() -> dict:
    with open(policy_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def get_policies():
    return _load_policies()


def get_trade_policy():
    return _load_policies().get("trade_policy", {})


def get_adversarial_policy():
    return _load_policies().get("adversarial_policy", {})