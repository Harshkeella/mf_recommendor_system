from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, BaseModel, Field


RiskAppetite = Literal[
    "Very Critical",
    "Critical",
    "Balanced",
    "Aggressive",
    "Very Aggressive",
]


class CustomerProfile(BaseModel):
    name: str = "Customer"
    age: int = Field(ge=18, le=100)
    occupation: str = "Salaried"
    annual_income: float = Field(ge=0)
    monthly_income_input: float | None = Field(default=None, ge=0, validation_alias="monthly_income")
    dependents: int = Field(default=0, ge=0, validation_alias=AliasChoices("number_of_dependents", "dependents"))
    existing_investments: float = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("existing_investments_value", "existing_investments"),
    )
    existing_loans_emi_monthly: float = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("existing_loans_emi_monthly", "existing_loans_or_emis", "emi"),
    )
    emergency_fund_months: float = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("emergency_fund_months", "emergency_fund_availability"),
    )
    goal_type: str = "Wealth Creation"
    goal_amount: float = Field(default=0, ge=0)
    goal_timeline_years: float = Field(gt=0)
    monthly_investment_amount: float = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("investment_amount_monthly", "investment_amount", "monthly_investment_amount"),
    )
    investment_mode: str = "SIP"
    risk_appetite: RiskAppetite = "Balanced"
    investment_experience: str = "Beginner"
    reaction_to_market_volatility: str = "Neutral"
    need_for_early_withdrawal: str = "Medium"
    lock_in_acceptance: str = "No"
    tax_slab: int = Field(default=0, ge=0, le=40)
    tax_saving_requirement: str = Field(
        default="No",
        validation_alias=AliasChoices("tax_saving_requirements", "tax_saving_requirement", "tax_saving_required"),
    )
    preferred_equity_exposure: float | None = Field(default=None, ge=0, le=100)
    international_exposure_preference: str = Field(default="None", alias="international_exposure_pref")
    nomination_status: str = "Unknown"

    model_config = {
        "populate_by_name": True,
        "str_strip_whitespace": True,
    }

    @property
    def monthly_income(self) -> float:
        if self.monthly_income_input is not None:
            return self.monthly_income_input
        return self.annual_income / 12 if self.annual_income else 0.0

    @property
    def emi_burden_ratio(self) -> float:
        if self.monthly_income <= 0:
            return 1.0 if self.existing_loans_emi_monthly else 0.0
        return self.existing_loans_emi_monthly / self.monthly_income

    @property
    def disposable_income_monthly(self) -> float:
        return max(self.monthly_income - self.existing_loans_emi_monthly, 0.0)


class RecommendationRequest(BaseModel):
    customer: CustomerProfile
    top_n_per_bucket: int = Field(default=3, ge=1, le=10)


class AdvisorContextRequest(BaseModel):
    customer: CustomerProfile


class AdvisorContextSimulationRequest(BaseModel):
    customer: CustomerProfile
    adjusted_scores: dict[str, float] = Field(default_factory=dict)
    include_recommendation_preview: bool = False
