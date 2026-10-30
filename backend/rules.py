"""Transparent rules engine. The model explains; THIS module sets every number."""
from dataclasses import asdict, dataclass

MAX_LOAN, MIN_LOAN = 500_000, 10_000
MIN_SCORE, MIN_VINTAGE, FOIR_CAP = 650, 6, 0.40
PROC_FEE_PCT, GST = 0.02, 0.18


def rate_for(score: int) -> float:
    return 14.0 if score >= 750 else 17.0 if score >= 700 else 21.0


def emi(principal: float, annual_rate: float, months: int) -> float:
    months = max(int(months or 36), 1)
    r = annual_rate / 12 / 100
    if r == 0:
        return principal / months
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)


@dataclass
class Decision:
    eligible: bool
    reasons: list
    max_amount: int = 0
    amount: int = 0
    tenure: int = 0
    rate: float = 0.0
    emi: int = 0
    fee: int = 0
    gst: int = 0
    total_interest: int = 0
    total_payable: int = 0
    disbursed: int = 0
    avg_inflow: int = 0
    bureau: int = 0
    foir: float = 0.0

    def dict(self):
        return asdict(self)


def decide(profile: dict, amount: int, tenure: int = 36) -> Decision:
    inflows = profile["monthly_inflow"]
    avg = int(sum(inflows) / max(len(inflows), 1))
    why = []
    tenure = 12 if tenure < 12 else 60 if tenure > 60 else int(tenure)
    amount = int(amount or 0)
    if not profile["kyc"]:
        why.append("kyc")
    if profile["bureau"] < MIN_SCORE:
        why.append("score")
    if profile["vintage_months"] < MIN_VINTAGE:
        why.append("vintage")
    if amount < MIN_LOAN:
        why.append("min_amount")
    if why:
        return Decision(False, why, avg_inflow=avg, bureau=profile["bureau"], tenure=tenure)
    cap = int(min(MAX_LOAN, 2.5 * avg) // 1000 * 1000)
    amt = min(amount, cap)
    rate = rate_for(profile["bureau"])
    e = emi(amt, rate, tenure)
    if e > FOIR_CAP * avg:
        why.append("foir")
        # Shrink principal until EMI fits 40% of inflows
        lo, hi = MIN_LOAN, amt
        fit = MIN_LOAN
        while lo <= hi:
            mid = (lo + hi) // 2
            if emi(mid, rate, tenure) <= FOIR_CAP * avg:
                fit = mid
                lo = mid + 1
            else:
                hi = mid - 1
        amt = int(fit // 1000 * 1000)
        e = emi(amt, rate, tenure)
        if amt < MIN_LOAN:
            return Decision(False, ["foir"], avg_inflow=avg, bureau=profile["bureau"], tenure=tenure)
    fee = round(amt * PROC_FEE_PCT)
    gst = round(fee * GST)
    tp = round(e * tenure)
    return Decision(
        True, why, cap, amt, tenure, rate, round(e), fee, gst,
        tp - amt, tp, amt - fee - gst, avg, profile["bureau"], round(e / max(avg, 1), 2),
    )
