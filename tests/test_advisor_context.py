from __future__ import annotations

import unittest

from app.recommender import RecommendationEngine
from app.schemas import CustomerProfile
from services.advisor_context_engine import generate_advisor_context, simulate_advisor_context


def customer(**overrides) -> CustomerProfile:
    data = {
        "name": "Rahul",
        "age": 28,
        "occupation": "Salaried",
        "annual_income": 900000,
        "monthly_income": 75000,
        "number_of_dependents": 0,
        "existing_investments": 200000,
        "existing_loans_or_emis": 10000,
        "emergency_fund_months": 6,
        "goal_type": "Wealth Creation",
        "goal_amount": 5000000,
        "goal_timeline_years": 12,
        "investment_amount": 20000,
        "investment_mode": "SIP",
        "risk_appetite": "Aggressive",
        "investment_experience": "Beginner",
        "reaction_to_market_volatility": "Can tolerate 20% fall",
        "need_for_early_withdrawal": "Low",
        "lock_in_acceptance": "Yes",
        "tax_slab": 20,
        "tax_saving_required": "Yes",
        "international_exposure_pref": "Moderate",
        "nomination_status": "Unknown",
    }
    data.update(overrides)
    return CustomerProfile(**data)


class AdvisorContextTests(unittest.TestCase):
    def test_existing_recommendation_output_does_not_change_after_context(self) -> None:
        profile = customer()
        engine = RecommendationEngine()
        before = engine.recommend(profile)
        _ = generate_advisor_context(profile)
        after = engine.recommend(profile)
        self.assertEqual(before["customer_risk_bucket"], after["customer_risk_bucket"])
        self.assertEqual(before["recommended_asset_allocation"], after["recommended_asset_allocation"])
        self.assertEqual(
            [item["mutual_fund_name"] for item in before["recommendations"]],
            [item["mutual_fund_name"] for item in after["recommendations"]],
        )

    def test_advisor_context_scores_are_generated(self) -> None:
        context = generate_advisor_context(customer())
        self.assertIn("advisor_context", context)
        self.assertEqual(len(context["advisor_context"]), 7)
        for insight in context["advisor_context"].values():
            self.assertGreaterEqual(insight["score"], 0)
            self.assertLessEqual(insight["score"], 100)
            self.assertIn("label", insight)
            self.assertIn("advisor_note", insight)

    def test_young_long_goal_has_high_life_stage_score(self) -> None:
        context = generate_advisor_context(customer(age=28, goal_timeline_years=12))
        self.assertGreaterEqual(context["advisor_context"]["life_stage_time_horizon"]["score"], 80)

    def test_older_short_goal_has_low_life_stage_score(self) -> None:
        context = generate_advisor_context(customer(age=55, goal_timeline_years=2))
        self.assertLess(context["advisor_context"]["life_stage_time_horizon"]["score"], 45)

    def test_high_emi_low_emergency_fund_has_low_stability(self) -> None:
        context = generate_advisor_context(
            customer(
                annual_income=600000,
                monthly_income=50000,
                existing_loans_or_emis=30000,
                emergency_fund_months=1,
                number_of_dependents=3,
            )
        )
        self.assertLess(context["advisor_context"]["financial_stability"]["score"], 45)

    def test_beginner_weak_volatility_has_low_behavioral_risk(self) -> None:
        context = generate_advisor_context(
            customer(investment_experience="Beginner", risk_appetite="Critical", reaction_to_market_volatility="Panic and sell")
        )
        self.assertLess(context["advisor_context"]["behavioral_risk_tolerance"]["score"], 45)

    def test_high_withdrawal_need_has_low_liquidity_score(self) -> None:
        context = generate_advisor_context(
            customer(need_for_early_withdrawal="High", lock_in_acceptance="No", emergency_fund_months=1)
        )
        self.assertLess(context["advisor_context"]["liquidity_commitment"]["score"], 45)

    def test_tax_saving_with_lock_in_creates_elss_note(self) -> None:
        context = generate_advisor_context(customer(tax_saving_required="Yes", lock_in_acceptance="Yes"))
        warnings = context["advisor_context"]["tax_documentation"]["warnings"]
        self.assertTrue(any("ELSS" in warning for warning in warnings))

    def test_context_sliders_do_not_alter_original_when_simulation_off(self) -> None:
        profile = customer()
        original = RecommendationEngine().recommend(profile)
        _ = generate_advisor_context(
            profile,
            {
                "life_stage_time_horizon": 5,
                "financial_stability": 5,
                "behavioral_risk_tolerance": 5,
            },
        )
        after = RecommendationEngine().recommend(profile)
        self.assertEqual(original["recommended_asset_allocation"], after["recommended_asset_allocation"])

    def test_simulation_creates_separate_preview(self) -> None:
        profile = customer()
        original = RecommendationEngine().recommend(profile)
        simulation = simulate_advisor_context(
            profile,
            {
                "life_stage_time_horizon": 10,
                "financial_stability": 10,
                "goal_feasibility": 10,
                "behavioral_risk_tolerance": 10,
                "liquidity_commitment": 10,
                "portfolio_diversification": 10,
                "tax_documentation": 10,
            },
            include_recommendation_preview=True,
        )
        self.assertIn("simulated_recommendation_preview", simulation)
        self.assertEqual(original["recommended_asset_allocation"], RecommendationEngine().recommend(profile)["recommended_asset_allocation"])
        self.assertNotEqual(
            original["recommended_asset_allocation"],
            simulation["simulated_recommendation_preview"]["simulated_asset_allocation"],
        )


if __name__ == "__main__":
    unittest.main()
