from __future__ import annotations

from dataclasses import dataclass

from .schemas import CustomerProfile


BUCKETS = ["Very Critical", "Critical", "Balanced", "Aggressive", "Very Aggressive"]

RISK_SCALE = {
    "Very Critical": {"min": 0, "max": 20, "equity": 5, "debt": 90, "gold": 5},
    "Critical": {"min": 21, "max": 40, "equity": 20, "debt": 75, "gold": 5},
    "Balanced": {"min": 41, "max": 60, "equity": 50, "debt": 45, "gold": 5},
    "Aggressive": {"min": 61, "max": 80, "equity": 70, "debt": 20, "gold": 10},
    "Very Aggressive": {"min": 81, "max": 100, "equity": 90, "debt": 10, "gold": 0},
}

# Customer scoring weights from the product brief. High impact factors dominate
# the risk-capacity bucket; low and very-low impact fields are intentionally
# present but cannot overpower age, timeline, appetite, volatility reaction, or
# experience.
CUSTOMER_SCORING_WEIGHTS = {
    "age": 20,
    "goal_timeline_years": 25,
    "risk_appetite": 15,
    "reaction_to_market_volatility": 12,
    "investment_experience": 10,
    "goal_type": 8,
    "goal_amount": 5,
    "investment_amount": 5,
    "number_of_dependents": 5,
    "need_for_early_withdrawal": 4,
    "annual_income": 2,
    "tax_saving_required": 2,
    "occupation": 1,
    "tax_slab": 1,
    "lock_in_acceptance": 1,
    "international_exposure_preference": 1,
}


@dataclass(frozen=True)
class RiskProfile:
    score: float
    bucket: str
    components: dict[str, float]
    notes: list[str]
    raw_score: float
    bucket_before_cap: str
    bucket_after_cap: str
    applied_safety_rules: list[str]


def _timeline_score(years: float) -> float:
    if years < 1:
        return 5
    if years < 3:
        return 20
    if years < 5:
        return 45
    if years < 7:
        return 60
    if years < 10:
        return 78
    return 95


def _age_score(age: int) -> float:
    if age <= 30:
        return 95
    if age <= 40:
        return 82
    if age < 50:
        return 62
    if age <= 60:
        return 35
    return 15


def _emergency_score(months: float) -> float:
    if months <= 0:
        return 0
    if months < 3:
        return 25
    if months < 6:
        return 65
    return 90


def _income_after_emi_score(customer: CustomerProfile) -> float:
    if customer.monthly_income <= 0:
        return 10
    disposable_ratio = customer.disposable_income_monthly / customer.monthly_income
    if disposable_ratio < 0.45:
        return 20
    if disposable_ratio < 0.60:
        return 45
    if disposable_ratio < 0.75:
        return 68
    return 88


def _dependents_score(dependents: int) -> float:
    if dependents <= 0:
        return 95
    if dependents == 1:
        return 80
    if dependents == 2:
        return 62
    if dependents == 3:
        return 42
    return 25


def _reaction_score(reaction: str) -> float:
    text = reaction.lower()
    if "very comfortable" in text or "buy" in text:
        return 95
    if "cannot tolerate" in text or "can't tolerate" in text or "loss" in text:
        return 10
    if "neutral" in text:
        return 65
    if "hold" in text or "worried" in text:
        return 45
    if "panic" in text or "sell" in text:
        return 10
    return 50


def _experience_score(experience: str) -> float:
    text = experience.lower()
    if "experienced" in text:
        return 90
    if "intermediate" in text:
        return 65
    if "beginner" in text:
        return 40
    return 25


def _risk_appetite_score(appetite: str) -> float:
    return {
        "very critical": 0,
        "critical": 25,
        "balanced": 50,
        "aggressive": 75,
        "very aggressive": 100,
    }.get(appetite.lower(), 55)


def _risk_appetite_max_score(appetite: str) -> float:
    return {
        "very critical": 20,
        "critical": 40,
        "balanced": 60,
        "aggressive": 80,
        "very aggressive": 100,
    }.get(appetite.lower(), 60)


def _bucket_max_score(bucket: str) -> float:
    return float(RISK_SCALE[bucket]["max"])


def _goal_type_score(goal_type: str) -> float:
    text = goal_type.lower()
    if any(term in text for term in ["emergency", "capital preservation"]):
        return 20
    if any(term in text for term in ["house", "marriage", "education"]):
        return 50
    if any(term in text for term in ["retirement", "wealth", "tax"]):
        return 78
    return 60


def _goal_amount_score(customer: CustomerProfile) -> float:
    if customer.goal_amount <= 0 or customer.annual_income <= 0:
        return 55
    ratio = customer.goal_amount / customer.annual_income
    if ratio <= 1:
        return 80
    if ratio <= 3:
        return 65
    if ratio <= 6:
        return 48
    return 32


def _investment_amount_score(customer: CustomerProfile) -> float:
    if customer.monthly_income <= 0:
        return 45
    savings_ratio = customer.monthly_investment_amount / customer.monthly_income
    if savings_ratio >= 0.25:
        return 88
    if savings_ratio >= 0.15:
        return 72
    if savings_ratio >= 0.08:
        return 55
    return 35


def _early_withdrawal_score(need: str) -> float:
    return {"low": 90, "medium": 60, "high": 30}.get(need.lower(), 55)


def _annual_income_score(income: float) -> float:
    if income >= 2_400_000:
        return 85
    if income >= 1_200_000:
        return 70
    if income >= 600_000:
        return 55
    return 38


def _tax_saving_score(required: str) -> float:
    return 65 if required.lower() == "yes" else 55


def _occupation_score(occupation: str) -> float:
    text = occupation.lower()
    if any(term in text for term in ["retired", "student"]):
        return 35
    if any(term in text for term in ["business", "self"]):
        return 60
    return 65


def _tax_slab_score(tax_slab: int) -> float:
    return 60 if tax_slab >= 20 else 55


def _lock_in_score(acceptance: str) -> float:
    return {"yes": 70, "maybe": 55, "no": 45}.get(acceptance.lower(), 50)


def _international_score(preference: str) -> float:
    return {"yes": 65, "high": 65, "moderate": 60, "none": 50, "no": 50}.get(preference.lower(), 55)


def bucket_from_score(score: float) -> str:
    if score <= 20:
        return "Very Critical"
    if score <= 40:
        return "Critical"
    if score <= 60:
        return "Balanced"
    if score <= 80:
        return "Aggressive"
    return "Very Aggressive"


def allocation_for_score(score: float) -> dict[str, float]:
    bucket = bucket_from_score(score)
    scale = RISK_SCALE[bucket]
    return {
        "equity": float(scale["equity"]),
        "debt": float(scale["debt"]),
        "gold": float(scale["gold"]),
    }


def calculate_risk_profile(customer: CustomerProfile) -> RiskProfile:
    components = {
        "age": _age_score(customer.age),
        "goal_timeline_years": _timeline_score(customer.goal_timeline_years),
        "risk_appetite": _risk_appetite_score(customer.risk_appetite),
        "reaction_to_market_volatility": _reaction_score(customer.reaction_to_market_volatility),
        "investment_experience": _experience_score(customer.investment_experience),
        "goal_type": _goal_type_score(customer.goal_type),
        "goal_amount": _goal_amount_score(customer),
        "investment_amount": _investment_amount_score(customer),
        "number_of_dependents": _dependents_score(customer.dependents),
        "need_for_early_withdrawal": _early_withdrawal_score(customer.need_for_early_withdrawal),
        "annual_income": _annual_income_score(customer.annual_income),
        "tax_saving_required": _tax_saving_score(customer.tax_saving_requirement),
        "occupation": _occupation_score(customer.occupation),
        "tax_slab": _tax_slab_score(customer.tax_slab),
        "lock_in_acceptance": _lock_in_score(customer.lock_in_acceptance),
        "international_exposure_preference": _international_score(customer.international_exposure_preference),
        "emergency_fund": _emergency_score(customer.emergency_fund_months),
        "income_after_emi": _income_after_emi_score(customer),
    }
    weighted = sum(components[key] * weight for key, weight in CUSTOMER_SCORING_WEIGHTS.items())
    score = weighted / sum(CUSTOMER_SCORING_WEIGHTS.values())
    raw_score = score
    bucket_before_cap = bucket_from_score(raw_score)
    applied_safety_rules: list[str] = []

    # Emergency fund, near-goal timeline, and EMI are strong guardrails. They
    # cap the final score so the displayed bucket always matches the allocation
    # scale shown to the advisor.
    if customer.emergency_fund_months <= 0:
        score = min(score - 8, 40)
        applied_safety_rules.append("No emergency fund caps risk at Critical.")
    elif customer.emergency_fund_months < 3:
        score = min(score - 8, 60)
        applied_safety_rules.append("Emergency fund below 3 months caps risk at Balanced.")
    if customer.emi_burden_ratio > 0.40:
        score = min(score - 8, 60)
        applied_safety_rules.append("High EMI burden caps risk at Balanced.")
    if customer.goal_timeline_years < 3:
        score = min(score, 40)
        applied_safety_rules.append("Goal timeline below 3 years caps risk at Critical.")

    if customer.age >= 60:
        score = min(score, _bucket_max_score("Critical"))
        applied_safety_rules.append("Age 60 or above caps risk at Critical.")
    elif customer.age >= 50:
        score = min(score, _bucket_max_score("Balanced"))
        applied_safety_rules.append("Age 50 or above caps risk at Balanced.")
    elif customer.age >= 45 and customer.risk_appetite in {"Very Critical", "Critical"}:
        score = min(score, _bucket_max_score("Critical"))
        applied_safety_rules.append("Age 45+ with conservative appetite caps risk at Critical.")

    appetite_cap = _risk_appetite_max_score(customer.risk_appetite)
    if score > appetite_cap:
        applied_safety_rules.append("Risk score capped at the customer's stated risk appetite.")
    score = min(score, appetite_cap)
    if components["reaction_to_market_volatility"] <= 20:
        score = min(score, 60)
        applied_safety_rules.append("Weak market-volatility reaction caps risk at Balanced.")
    if components["reaction_to_market_volatility"] <= 20 and components["investment_experience"] <= 40:
        score = min(score, 55)
        applied_safety_rules.append("Beginner plus weak volatility reaction keeps risk within Balanced.")
    score = max(0, min(100, score))
    bucket = bucket_from_score(score)

    notes: list[str] = []
    if customer.risk_appetite != bucket:
        notes.append(
            f"Stated risk appetite is {customer.risk_appetite}, but objective capacity maps to {bucket}."
        )
    if "Risk score capped at the customer's stated risk appetite." in applied_safety_rules:
        notes.append("Final risk score is capped at the customer's stated risk appetite.")
    if customer.goal_timeline_years < 3:
        notes.append("Near-term goal reduces risk capacity even if stated appetite is high.")
    if customer.emergency_fund_months < 3:
        notes.append("Emergency fund below 3 months materially reduces risk capacity.")
    if customer.emi_burden_ratio > 0.40:
        notes.append("EMI burden above 40% of monthly income reduces risk capacity.")
    if components["reaction_to_market_volatility"] <= 20:
        notes.append("Weak market-volatility reaction caps the profile at Balanced risk.")
    if customer.investment_experience.lower() == "beginner" and bucket in {"Aggressive", "Very Aggressive"}:
        notes.append("Customer is beginner; avoid heavy small-cap and sectoral exposure.")

    return RiskProfile(
        score=round(score, 2),
        bucket=bucket,
        components=components,
        notes=notes,
        raw_score=round(raw_score, 2),
        bucket_before_cap=bucket_before_cap,
        bucket_after_cap=bucket,
        applied_safety_rules=applied_safety_rules,
    )
