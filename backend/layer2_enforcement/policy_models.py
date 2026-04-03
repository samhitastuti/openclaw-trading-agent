import yaml
from pathlib import Path

# Load policy file from backend/config/
policy_path = Path(__file__).resolve().parent.parent / "config" / "policies.yaml"

with open(policy_path, "r") as f:
    policies = yaml.safe_load(f)


def get_policies():
    return policies


def get_trade_policy():
    return policies.get("trade_policy", {})


def get_adversarial_policy():
    return policies.get("adversarial_policy", {})