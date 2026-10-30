"""Mock partner APIs: KYC, bureau, Paytm inflows, e-sign. Swap for real connectors later."""
import json
import time
import uuid
from pathlib import Path

USERS = json.loads((Path(__file__).parent / "data/users.json").read_text(encoding="utf-8"))

PLANS = {
    "basic": {
        "id": "SHB",
        "name": "SecureHealth Basic",
        "premium": 8400,
        "sum_insured": 500_000,
        "waiting_years": 4,
    },
    "plus": {
        "id": "SHP",
        "name": "SecureHealth Plus",
        "premium": 12900,
        "sum_insured": 1_000_000,
        "waiting_years": 2,
    },
}


def profile(user_id: str) -> dict:
    if user_id not in USERS:
        raise KeyError(user_id)
    return USERS[user_id]


def fetch_kyc(user_id: str) -> dict:
    u = profile(user_id)
    return {"complete": bool(u["kyc"]), "name": u["name"], "city": u["city"], "age": u.get("age", 30)}


def fetch_bureau(user_id: str) -> dict:
    u = profile(user_id)
    return {"score": int(u["bureau"])}


def fetch_inflows(user_id: str) -> dict:
    u = profile(user_id)
    months = list(u["monthly_inflow"])
    return {
        "months": months,
        "avg": int(sum(months) / max(len(months), 1)),
        "vintage_months": int(u["vintage_months"]),
        "kind": u["kind"],
        "life_event": u.get("life_event"),
        "hint": u.get("hint", ""),
    }


def esign(kind: str, amount: int) -> str:
    prefix = "PTM-L" if kind == "loan" else "PTM-H"
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}-{int(time.time()) % 10000}"


def decide_plan(text: str) -> str | None:
    t = (text or "").lower()
    if "plus" in t:
        return "plus"
    if "basic" in t or "बेसिक" in t:
        return "basic"
    return None
