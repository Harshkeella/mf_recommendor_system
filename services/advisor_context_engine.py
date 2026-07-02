from __future__ import annotations

from statistics import mean

from app.allocation import BASE_ALLOCATIONS
from app.risk_profile import bucket_from_score
from app.schemas import CustomerProfile


CONTEXT_SCORE_KEYS = [
    "life_stage_time_horizon",
    "financial_stability",
    "goal_feasibility",
    "behavioral_risk_tolerance",
    "liquidity_commitment",
    "portfolio_diversification",
    "tax_documentation",
]

DISCLAIMER = (
    "This advisor context is for decision support and explanation. It does not "
    "replace certified financial advice."
)


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return round(max(low, min(high, value)), 2)


def _label(score: float, strong: str, moderate: str, weak: str) -> str:
    if score >= 75:
        return strong
    if score >= 45:
        return moderate
    return weak


def _yes(value: str) -> bool:
    return str(value or "").strip().lower() in {"yes", "y", "true", "accepted", "available", "done"}


def _text_attr(customer: CustomerProfile, attr: str, default: str) -> str:
    return str(getattr(customer, attr, default) or default)


def _reaction_score(reaction: str) -> float:
    text = reaction.lower()
    if "very comfortable" in text or "20%" in text or "buy" in text:
        return 90
    if "neutral" in text:
        return 65
    if "hold" in text or "worried" in text:
        return 45
    if "panic" in text or "sell" in text or "cannot tolerate" in text or "loss" in text:
        return 15
    return 50


def _risk_appetite_score(appetite: str) -> float:
    return {
        "very critical": 10,
        "critical": 30,
        "balanced": 55,
        "aggressive": 78,
        "very aggressive": 92,
    }.get(appetite.lower(), 55)


def _experience_score(experience: str) -> float:
    text = experience.lower()
    if "experienced" in text:
        return 85
    if "intermediate" in text:
        return 65
    return 35


def _score_life_stage(customer: CustomerProfile) -> dict[str, object]:
    age_component = 95 if customer.age <= 30 else 78 if customer.age <= 40 else 55 if customer.age <= 50 else 30
    timeline_component = (
        95
        if customer.goal_timeline_years >= 10
        else 75
        if customer.goal_timeline_years >= 7
        else 55
        if customer.goal_timeline_years >= 5
        else 30
        if customer.goal_timeline_years >= 3
        else 12
    )
    goal_type_component = 75 if customer.goal_type.lower() in {"wealth creation", "retirement"} else 55
    score = _clamp(age_component * 0.35 + timeline_component * 0.50 + goal_type_component * 0.15)
    return {
        "score": score,
        "label": _label(score, "Strong long-term investing profile", "Moderate time horizon", "Limited equity-risk runway"),
        "explanation": f"{customer.name} is {customer.age} with a {customer.goal_timeline_years:g}-year {customer.goal_type} goal.",
        "advisor_note": "Equity exposure may be discussed if behavior and liquidity also support it.",
        "how_calculated": "Age, goal timeline, and goal type are weighted to estimate the time available for volatility.",
        "warnings": [] if score >= 45 else ["Short horizon or older age calls for conservative fund categories."],
    }


def _score_financial_stability(customer: CustomerProfile) -> dict[str, object]:
    emergency = min(customer.emergency_fund_months / 6 * 100, 100)
    emi = 100 - min(customer.emi_burden_ratio * 160, 100)
    dependents = max(100 - customer.dependents * 18, 20)
    occupation = 75 if customer.occupation.lower() in {"salaried", "government employee", "professional"} else 55
    income = 80 if customer.annual_income >= 1_200_000 else 60 if customer.annual_income >= 600_000 else 40
    score = _clamp(emergency * 0.30 + emi * 0.30 + dependents * 0.15 + occupation * 0.10 + income * 0.15)
    warnings = []
    if customer.emergency_fund_months < 3:
        warnings.append("Emergency fund is below 3 months.")
    if customer.emi_burden_ratio > 0.40:
        warnings.append("EMI burden is high relative to monthly income.")
    return {
        "score": score,
        "label": _label(score, "Good stability", "Moderate stability", "Weak stability"),
        "explanation": "Stability is based on income, EMI burden, dependents, occupation, and emergency fund.",
        "advisor_note": "SIP sustainability should be confirmed before increasing risk exposure.",
        "how_calculated": "Emergency fund and EMI burden are the strongest inputs, followed by income, dependents, and occupation.",
        "warnings": warnings,
    }


def _score_goal_feasibility(customer: CustomerProfile) -> dict[str, object]:
    months = max(customer.goal_timeline_years * 12, 1)
    simple_required = customer.goal_amount / months if customer.goal_amount else 0
    capacity_ratio = customer.monthly_investment_amount / simple_required if simple_required else 1
    score = _clamp(capacity_ratio * 70 + min(customer.goal_timeline_years, 15) * 2)
    warnings = []
    if capacity_ratio < 0.5:
        warnings.append("Current investment amount may be far below the simple monthly amount needed for the goal.")
    elif capacity_ratio < 0.8:
        warnings.append("Goal may need higher SIP, longer timeline, or revised target amount.")
    return {
        "score": score,
        "label": _label(score, "Goal appears feasible", "Goal needs monitoring", "Goal looks stretched"),
        "explanation": "Compares current investment amount with goal amount and timeline.",
        "advisor_note": "Do not increase fund risk just to compensate for a stretched goal.",
        "how_calculated": "Uses a simple non-return monthly requirement as a conservative feasibility check.",
        "warnings": warnings,
    }


def _score_behavior(customer: CustomerProfile) -> dict[str, object]:
    score = _clamp(
        _risk_appetite_score(customer.risk_appetite) * 0.35
        + _experience_score(customer.investment_experience) * 0.25
        + _reaction_score(customer.reaction_to_market_volatility) * 0.40
    )
    warnings = []
    if customer.investment_experience.lower() == "beginner":
        warnings.append("Beginner investor; explain volatility and avoid heavy small-cap or sectoral exposure.")
    if _reaction_score(customer.reaction_to_market_volatility) <= 20:
        warnings.append("Weak reaction to volatility; explain downside scenarios clearly.")
    return {
        "score": score,
        "label": _label(score, "Strong behavioral tolerance", "Moderate behavioral tolerance", "Low behavioral tolerance"),
        "explanation": "Measures emotional ability to stay invested through market volatility.",
        "advisor_note": "Use this for conversation quality, not as a direct override to recommendations.",
        "how_calculated": "Risk appetite, investment experience, and volatility reaction are combined.",
        "warnings": warnings,
    }


def _score_liquidity(customer: CustomerProfile) -> dict[str, object]:
    withdrawal = {"low": 90, "medium": 60, "high": 20}.get(customer.need_for_early_withdrawal.lower(), 55)
    lock_in = {"yes": 85, "maybe": 55, "no": 25}.get(customer.lock_in_acceptance.lower(), 45)
    emergency = min(customer.emergency_fund_months / 6 * 100, 100)
    investment_mode = _text_attr(customer, "investment_mode", "SIP")
    mode = 75 if investment_mode.lower() in {"sip", "monthly"} else 60
    score = _clamp(withdrawal * 0.35 + lock_in * 0.25 + emergency * 0.30 + mode * 0.10)
    warnings = []
    if customer.need_for_early_withdrawal.lower() == "high":
        warnings.append("High early-withdrawal need; avoid lock-in and high exit-load products.")
    if customer.lock_in_acceptance.lower() == "no":
        warnings.append("Customer does not accept lock-in.")
    return {
        "score": score,
        "label": _label(score, "Flexible long-term commitment", "Moderate liquidity flexibility", "Liquidity-sensitive profile"),
        "explanation": "Checks whether the customer can stay invested without needing early withdrawals.",
        "advisor_note": "Liquidity-sensitive clients may need liquid/debt allocation before equity exposure.",
        "how_calculated": "Early withdrawal need, lock-in acceptance, emergency fund, and investment mode are combined.",
        "warnings": warnings,
    }


def _score_diversification(customer: CustomerProfile) -> dict[str, object]:
    existing = min(customer.existing_investments / max(customer.goal_amount, 1) * 100, 100) if customer.goal_amount else 50
    equity_pref = customer.preferred_equity_exposure if customer.preferred_equity_exposure is not None else 50
    international = 75 if customer.international_exposure_preference.lower() in {"yes", "moderate", "high"} else 45
    score = _clamp(55 + (100 - abs(equity_pref - 55)) * 0.20 + international * 0.15 - existing * 0.10)
    warnings = []
    if equity_pref >= 80:
        warnings.append("High preferred equity exposure; check concentration and downside comfort.")
    if customer.international_exposure_preference.lower() in {"yes", "moderate", "high"}:
        warnings.append("Optional global diversification can be discussed as a satellite allocation.")
    return {
        "score": score,
        "label": _label(score, "Diversification discussion useful", "Moderate diversification need", "Low diversification priority"),
        "explanation": "Highlights whether the advisor should discuss concentration and asset/geography spread.",
        "advisor_note": "Use this to discuss portfolio construction, not to force international funds.",
        "how_calculated": "Existing investments, preferred equity exposure, international preference, and goal type are considered.",
        "warnings": warnings,
    }


def _score_tax_docs(customer: CustomerProfile) -> dict[str, object]:
    tax_need = 85 if customer.tax_saving_requirement.lower() == "yes" else 55
    slab = 80 if customer.tax_slab >= 20 else 55
    lock = 85 if customer.lock_in_acceptance.lower() == "yes" else 35
    nomination_status = _text_attr(customer, "nomination_status", "Unknown")
    nomination = 90 if _yes(nomination_status) else 30 if nomination_status.lower() in {"no", "missing"} else 55
    score = _clamp(tax_need * 0.25 + slab * 0.20 + lock * 0.25 + nomination * 0.30)
    warnings = []
    if customer.tax_saving_requirement.lower() == "yes" and customer.lock_in_acceptance.lower() == "yes":
        warnings.append("ELSS can be discussed as a tax-saving option.")
    if nomination < 60:
        warnings.append("Nomination/documentation status should be confirmed.")
    return {
        "score": score,
        "label": _label(score, "Tax and documentation ready", "Some tax/documentation points", "Documentation follow-up needed"),
        "explanation": "Checks tax-saving relevance and documentation readiness.",
        "advisor_note": "Confirm tax section eligibility and nomination before execution.",
        "how_calculated": "Tax slab, tax-saving need, lock-in acceptance, and nomination status are combined.",
        "warnings": warnings,
    }


def generate_advisor_context(
    customer: CustomerProfile,
    adjusted_scores: dict[str, float] | None = None,
) -> dict[str, object]:
    insights = {
        "life_stage_time_horizon": _score_life_stage(customer),
        "financial_stability": _score_financial_stability(customer),
        "goal_feasibility": _score_goal_feasibility(customer),
        "behavioral_risk_tolerance": _score_behavior(customer),
        "liquidity_commitment": _score_liquidity(customer),
        "portfolio_diversification": _score_diversification(customer),
        "tax_documentation": _score_tax_docs(customer),
    }
    adjusted_scores = adjusted_scores or {}
    for key, value in adjusted_scores.items():
        if key in insights:
            insights[key]["score"] = _clamp(value)
            insights[key]["simulated"] = True

    positive_signals: list[str] = []
    red_flags: list[str] = []
    for key, insight in insights.items():
        if insight["score"] >= 75:
            positive_signals.append(str(insight["label"]))
        if insight["score"] < 45:
            red_flags.append(str(insight["label"]))
        red_flags.extend(insight.get("warnings", []))

    if customer.emergency_fund_months >= 6:
        positive_signals.append("Emergency fund available")
    if customer.dependents == 0:
        positive_signals.append("Low dependent burden")
    if customer.goal_timeline_years >= 7:
        positive_signals.append("Long goal timeline")

    advisor_questions = [
        "Has the customer experienced a real market fall before?",
        "Is the goal amount inflation adjusted?",
        "Is the emergency fund kept separately from investments?",
        "Are existing investments diversified across asset classes?",
        "Is nomination and KYC documentation complete?",
    ]
    overall = (
        f"{customer.name} has a {customer.goal_timeline_years:g}-year {customer.goal_type} goal. "
        f"Financial stability is {insights['financial_stability']['label'].lower()}, and behavioral tolerance is "
        f"{insights['behavioral_risk_tolerance']['label'].lower()}. Use this context to explain recommendations, "
        "not to override the recommendation engine."
    )
    return {
        "advisor_context": insights,
        "overall_summary": overall,
        "positive_signals": sorted(set(positive_signals)),
        "red_flags": sorted(set(red_flags)),
        "advisor_questions": advisor_questions,
        "disclaimer": DISCLAIMER,
    }


def simulate_advisor_context(
    customer: CustomerProfile,
    adjusted_scores: dict[str, float],
    include_recommendation_preview: bool = False,
) -> dict[str, object]:
    context = generate_advisor_context(customer, adjusted_scores)
    response: dict[str, object] = {
        "simulated_context": context,
        "simulation_note": "Advisor context sliders are for explanation only and do not overwrite the original recommendation.",
    }
    if include_recommendation_preview and adjusted_scores:
        avg_score = mean(_clamp(score) for score in adjusted_scores.values())
        simulated_bucket = bucket_from_score(avg_score)
        response["simulated_recommendation_preview"] = {
            "simulated_context_score": round(avg_score, 2),
            "simulated_risk_bucket": simulated_bucket,
            "simulated_asset_allocation": BASE_ALLOCATIONS[simulated_bucket],
            "note": "Preview only. Original recommendation is not modified or saved.",
        }
    return response
