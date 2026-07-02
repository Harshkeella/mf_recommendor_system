from __future__ import annotations

import unittest

import pandas as pd

from app.allocation import calculate_allocation
from app.clustering import cluster_funds, cosine_similar_funds
from app.filtering import filter_funds
from app.recommender import RecommendationEngine
from app.risk_profile import allocation_for_score, bucket_from_score, calculate_risk_profile
from app.schemas import CustomerProfile
from app.scoring import score_funds


def customer(**overrides) -> CustomerProfile:
    data = {
        "age": 35,
        "occupation": "Salaried",
        "annual_income": 1800000,
        "number_of_dependents": 1,
        "existing_investments_value": 250000,
        "existing_loans_emi_monthly": 20000,
        "emergency_fund_months": 6,
        "goal_type": "Wealth Creation",
        "goal_amount": 5000000,
        "goal_timeline_years": 10,
        "investment_amount_monthly": 30000,
        "risk_appetite": "Balanced",
        "investment_experience": "Intermediate",
        "reaction_to_market_volatility": "Neutral",
        "need_for_early_withdrawal": "Medium",
        "lock_in_acceptance": "Yes",
        "tax_slab": 20,
        "tax_saving_requirements": "No",
        "preferred_equity_exposure": 60,
        "international_exposure_pref": "Moderate",
    }
    data.update(overrides)
    return CustomerProfile(**data)


class RuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = RecommendationEngine()
        cls.funds = cls.engine.load_universe()

    def test_older_user_with_near_goal_should_not_get_high_equity(self) -> None:
        profile = customer(
            age=67,
            annual_income=900000,
            number_of_dependents=2,
            emergency_fund_months=2,
            goal_timeline_years=2,
            existing_loans_emi_monthly=15000,
            risk_appetite="Very Aggressive",
            reaction_to_market_volatility="Worried but hold",
            investment_experience="Beginner",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertLessEqual(allocation["equity"], 20)
        self.assertIn(risk.bucket, {"Very Critical", "Critical"})

    def test_risk_score_scale_maps_to_expected_allocation(self) -> None:
        cases = [
            (10, "Very Critical", {"equity": 5.0, "debt": 90.0, "gold": 5.0}),
            (30, "Critical", {"equity": 20.0, "debt": 75.0, "gold": 5.0}),
            (50, "Balanced", {"equity": 50.0, "debt": 45.0, "gold": 5.0}),
            (70, "Aggressive", {"equity": 70.0, "debt": 20.0, "gold": 10.0}),
            (90, "Very Aggressive", {"equity": 90.0, "debt": 10.0, "gold": 0.0}),
        ]
        for score, bucket, allocation in cases:
            self.assertEqual(bucket_from_score(score), bucket)
            self.assertEqual(allocation_for_score(score), allocation)

    def test_young_user_with_far_goal_can_get_aggressive_allocation(self) -> None:
        profile = customer(
            age=27,
            annual_income=2400000,
            number_of_dependents=0,
            emergency_fund_months=9,
            goal_timeline_years=15,
            existing_loans_emi_monthly=0,
            risk_appetite="Very Aggressive",
            reaction_to_market_volatility="Very comfortable",
            investment_experience="Experienced",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertIn(risk.bucket, {"Aggressive", "Very Aggressive"})
        self.assertGreaterEqual(allocation["equity"], 70)

    def test_no_emergency_fund_should_cap_equity(self) -> None:
        profile = customer(emergency_fund_months=0, goal_timeline_years=12, risk_appetite="Very Aggressive")
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertLessEqual(allocation["equity"], 20)
        self.assertLessEqual(risk.score, 40)

    def test_low_emergency_fund_bucket_and_allocation_stay_on_scale(self) -> None:
        profile = customer(
            age=27,
            annual_income=2400000,
            number_of_dependents=0,
            emergency_fund_months=2,
            goal_timeline_years=15,
            existing_loans_emi_monthly=0,
            risk_appetite="Very Aggressive",
            reaction_to_market_volatility="Very comfortable",
            investment_experience="Experienced",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Balanced")
        self.assertEqual(allocation["equity"], 50.0)

    def test_high_emi_bucket_and_allocation_stay_on_scale(self) -> None:
        profile = customer(
            age=27,
            annual_income=1200000,
            number_of_dependents=0,
            emergency_fund_months=9,
            goal_timeline_years=15,
            existing_loans_emi_monthly=60000,
            risk_appetite="Very Aggressive",
            reaction_to_market_volatility="Very comfortable",
            investment_experience="Experienced",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Balanced")
        self.assertEqual(allocation["equity"], 50.0)

    def test_beginner_panic_reaction_caps_profile_at_balanced(self) -> None:
        profile = customer(
            age=36,
            occupation="Salaried",
            annual_income=1800000,
            number_of_dependents=1,
            existing_investments_value=300000,
            existing_loans_emi_monthly=25000,
            emergency_fund_months=6,
            goal_type="Wealth Creation",
            goal_amount=5000000,
            goal_timeline_years=10,
            investment_amount_monthly=30000,
            risk_appetite="Balanced",
            investment_experience="Beginner",
            reaction_to_market_volatility="Panic and sell",
            need_for_early_withdrawal="Medium",
            lock_in_acceptance="No",
            tax_slab=20,
            tax_saving_requirements="No",
            international_exposure_pref="None",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Balanced")
        self.assertLessEqual(risk.score, 60)
        self.assertEqual(allocation["equity"], 50.0)

    def test_stated_balanced_appetite_cannot_receive_aggressive_allocation(self) -> None:
        profile = customer(
            age=28,
            annual_income=2400000,
            number_of_dependents=0,
            emergency_fund_months=12,
            goal_timeline_years=15,
            existing_loans_emi_monthly=0,
            risk_appetite="Balanced",
            reaction_to_market_volatility="Very comfortable",
            investment_experience="Experienced",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Balanced")
        self.assertEqual(allocation["equity"], 50.0)

    def test_stated_critical_appetite_gets_debt_heavy_allocation(self) -> None:
        profile = customer(
            age=28,
            annual_income=2400000,
            number_of_dependents=0,
            emergency_fund_months=12,
            goal_timeline_years=15,
            existing_loans_emi_monthly=0,
            risk_appetite="Critical",
            reaction_to_market_volatility="Very comfortable",
            investment_experience="Experienced",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Critical")
        self.assertEqual(allocation["equity"], 20.0)
        self.assertEqual(allocation["debt"], 75.0)

    def test_age_50_very_critical_stays_preservation_first(self) -> None:
        profile = customer(
            age=50,
            risk_appetite="Very Critical",
            goal_timeline_years=10,
            investment_experience="Beginner",
            reaction_to_market_volatility="Cannot tolerate loss",
            need_for_early_withdrawal="High",
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Very Critical")
        self.assertEqual(allocation, {"equity": 5.0, "debt": 90.0, "gold": 5.0})

    def test_age_55_critical_stays_critical_allocation(self) -> None:
        profile = customer(
            age=55,
            risk_appetite="Critical",
            goal_timeline_years=5,
        )
        risk = calculate_risk_profile(profile)
        allocation = calculate_allocation(risk.bucket, profile).allocation
        self.assertEqual(risk.bucket, "Critical")
        self.assertEqual(allocation, {"equity": 20.0, "debt": 75.0, "gold": 5.0})

    def test_critical_recommendations_have_more_debt_than_equity_funds(self) -> None:
        profile = customer(
            age=36,
            annual_income=1800000,
            number_of_dependents=1,
            emergency_fund_months=6,
            goal_timeline_years=10,
            existing_loans_emi_monthly=25000,
            investment_amount_monthly=30000,
            risk_appetite="Critical",
            reaction_to_market_volatility="Neutral",
            investment_experience="Beginner",
            lock_in_acceptance="No",
        )
        result = RecommendationEngine().recommend(profile, top_n_per_bucket=3)
        counts = pd.Series([item["allocation_bucket"] for item in result["recommendations"]]).value_counts()
        self.assertEqual(result["customer_risk_bucket"], "Critical")
        self.assertGreater(counts.get("debt", 0), counts.get("equity", 0))
        self.assertEqual(result["recommended_asset_allocation"]["debt"], 75.0)

    def test_elss_removed_if_lock_in_not_accepted(self) -> None:
        profile = customer(lock_in_acceptance="No", tax_saving_requirements="Yes")
        filtered = filter_funds(self.funds, profile)
        self.assertFalse(filtered.eligible["sub_category"].str.contains("ELSS", case=False).any())

    def test_small_cap_removed_when_goal_timeline_below_7_years(self) -> None:
        profile = customer(goal_timeline_years=6)
        filtered = filter_funds(self.funds, profile)
        self.assertFalse(filtered.eligible["sub_category"].str.contains("Small Cap", case=False).any())

    def test_passive_funds_penalized_for_high_tracking_error(self) -> None:
        profile = customer(goal_timeline_years=10)
        sample = pd.DataFrame(
            [
                {
                    "fund_id": 1,
                    "mutual_fund_name": "Passive Clean Tracker",
                    "amc": "Test",
                    "category": "Passive",
                    "sub_category": "Index Fund - Large Cap",
                    "risk_level": "Very High",
                    "min_horizon_years": 5,
                    "expense_ratio": 0.2,
                    "exit_load_period_days": 0,
                    "lock_in_years": 0,
                    "minimum_investing_amount": 500,
                    "min_sip_investment": 500,
                    "return_3y": 12,
                    "return_5y": 13,
                    "sharpe_ratio": 1.0,
                    "sortino_ratio": 1.1,
                    "alpha": 0.1,
                    "calmar_ratio": 0.8,
                    "info_ratio": 0.2,
                    "capture_ratio": 100,
                    "standard_deviation": 12,
                    "downside_deviation": 7,
                    "max_drawdown": -15,
                    "beta": 1,
                    "tracking_error": 0.4,
                    "turnover": 20,
                },
                {
                    "fund_id": 2,
                    "mutual_fund_name": "Passive Loose Tracker",
                    "amc": "Test",
                    "category": "Passive",
                    "sub_category": "Index Fund - Large Cap",
                    "risk_level": "Very High",
                    "min_horizon_years": 5,
                    "expense_ratio": 0.2,
                    "exit_load_period_days": 0,
                    "lock_in_years": 0,
                    "minimum_investing_amount": 500,
                    "min_sip_investment": 500,
                    "return_3y": 12,
                    "return_5y": 13,
                    "sharpe_ratio": 1.0,
                    "sortino_ratio": 1.1,
                    "alpha": 0.1,
                    "calmar_ratio": 0.8,
                    "info_ratio": 0.2,
                    "capture_ratio": 100,
                    "standard_deviation": 12,
                    "downside_deviation": 7,
                    "max_drawdown": -15,
                    "beta": 1,
                    "tracking_error": 8.0,
                    "turnover": 20,
                },
            ]
        )
        scored = score_funds(sample, profile, "Aggressive").sort_values("fund_id")
        clean = scored.loc[scored["fund_id"] == 1].iloc[0]
        loose = scored.loc[scored["fund_id"] == 2].iloc[0]
        self.assertGreater(loose["risk_penalty"], clean["risk_penalty"])
        self.assertLess(loose["final_score"], clean["final_score"])

    def test_goal_below_3_years_rejects_high_risk_equity(self) -> None:
        profile = customer(goal_timeline_years=2, risk_appetite="Aggressive")
        sample = pd.DataFrame(
            [
                {
                    "fund_id": 11,
                    "mutual_fund_name": "High Risk Equity",
                    "category": "Equity",
                    "sub_category": "Large Cap",
                    "risk_level": "High",
                    "min_horizon_years": 3,
                    "lock_in_years": 0,
                    "min_sip_investment": 500,
                },
                {
                    "fund_id": 12,
                    "mutual_fund_name": "Short Debt",
                    "category": "Debt",
                    "sub_category": "Short Duration",
                    "risk_level": "Low to Moderate",
                    "min_horizon_years": 2,
                    "lock_in_years": 0,
                    "min_sip_investment": 500,
                },
            ]
        )
        filtered = filter_funds(sample, profile, "Balanced")
        self.assertFalse(filtered.eligible["mutual_fund_name"].str.contains("High Risk Equity").any())
        self.assertTrue(filtered.eligible["mutual_fund_name"].str.contains("Short Debt").any())

    def test_small_minimum_sip_mismatch_warns_without_rejection(self) -> None:
        profile = customer(investment_amount_monthly=1000)
        sample = pd.DataFrame(
            [
                {
                    "fund_id": 21,
                    "mutual_fund_name": "Slightly Higher SIP Fund",
                    "category": "Equity",
                    "sub_category": "Large Cap",
                    "risk_level": "Moderately High",
                    "min_horizon_years": 5,
                    "lock_in_years": 0,
                    "min_sip_investment": 1500,
                }
            ]
        )
        filtered = filter_funds(sample, profile, "Aggressive")
        self.assertEqual(len(filtered.eligible), 1)
        self.assertTrue(any("minimum investment slightly above" in warning for warning in filtered.warnings))

    def test_large_minimum_sip_mismatch_is_rejected(self) -> None:
        profile = customer(investment_amount_monthly=1000)
        sample = pd.DataFrame(
            [
                {
                    "fund_id": 22,
                    "mutual_fund_name": "Too High SIP Fund",
                    "category": "Equity",
                    "sub_category": "Large Cap",
                    "risk_level": "Moderately High",
                    "min_horizon_years": 5,
                    "lock_in_years": 0,
                    "min_sip_investment": 3000,
                }
            ]
        )
        filtered = filter_funds(sample, profile, "Aggressive")
        self.assertEqual(len(filtered.eligible), 0)

    def test_high_risk_adjusted_fund_beats_high_return_bad_drawdown(self) -> None:
        profile = customer(goal_timeline_years=10, risk_appetite="Aggressive")
        sample = pd.DataFrame(
            [
                {
                    "fund_id": 31,
                    "mutual_fund_name": "Consistent Compounder",
                    "category": "Equity",
                    "sub_category": "Large Cap",
                    "risk_level": "High",
                    "min_horizon_years": 5,
                    "expense_ratio": 0.7,
                    "exit_load_period_days": 30,
                    "lock_in_years": 0,
                    "minimum_investing_amount": 500,
                    "min_sip_investment": 500,
                    "return_3y": 13,
                    "return_5y": 14,
                    "sharpe_ratio": 1.4,
                    "sortino_ratio": 1.7,
                    "alpha": 2.5,
                    "calmar_ratio": 1.2,
                    "info_ratio": 0.5,
                    "capture_ratio": 103,
                    "standard_deviation": 10,
                    "downside_deviation": 5,
                    "max_drawdown": -12,
                    "beta": 0.9,
                    "tracking_error": 2,
                    "turnover": 25,
                    "aum_cr": 5000,
                },
                {
                    "fund_id": 32,
                    "mutual_fund_name": "Return Chaser",
                    "category": "Equity",
                    "sub_category": "Large Cap",
                    "risk_level": "High",
                    "min_horizon_years": 5,
                    "expense_ratio": 1.2,
                    "exit_load_period_days": 30,
                    "lock_in_years": 0,
                    "minimum_investing_amount": 500,
                    "min_sip_investment": 500,
                    "return_3y": 28,
                    "return_5y": 26,
                    "sharpe_ratio": 0.35,
                    "sortino_ratio": 0.4,
                    "alpha": -1.0,
                    "calmar_ratio": 0.2,
                    "info_ratio": -0.2,
                    "capture_ratio": 95,
                    "standard_deviation": 24,
                    "downside_deviation": 18,
                    "max_drawdown": -45,
                    "beta": 1.4,
                    "tracking_error": 7,
                    "turnover": 80,
                    "aum_cr": 5000,
                },
            ]
        )
        scored = score_funds(sample, profile, "Aggressive")
        self.assertEqual(scored.iloc[0]["mutual_fund_name"], "Consistent Compounder")

    def test_dbscan_assigns_cluster_labels(self) -> None:
        clustered, diagnostics = cluster_funds(self.funds)
        self.assertEqual(diagnostics["algorithm"], "DBSCAN")
        self.assertIn("dbscan_cluster_id", clustered.columns)
        self.assertIn("is_outlier", clustered.columns)
        self.assertEqual(len(clustered), len(self.funds))

    def test_dbscan_noise_funds_are_marked_outliers(self) -> None:
        sample = self.funds.head(20).copy()
        outlier = sample.iloc[0].copy()
        outlier["fund_id"] = 999999
        outlier["mutual_fund_name"] = "Extreme Outlier Fund"
        outlier["return_3y"] = 200
        outlier["return_5y"] = 180
        outlier["standard_deviation"] = 120
        outlier["max_drawdown"] = -95
        outlier["tracking_error"] = 90
        sample = pd.concat([sample, outlier.to_frame().T], ignore_index=True)
        clustered, _ = cluster_funds(sample, eps=1.2, min_samples=4)
        row = clustered[clustered["mutual_fund_name"].eq("Extreme Outlier Fund")].iloc[0]
        self.assertTrue(bool(row["is_outlier"]))

    def test_similar_funds_prefer_same_dbscan_cluster(self) -> None:
        clustered, _ = cluster_funds(self.funds, eps=2.2, min_samples=4)
        non_outliers = clustered[~clustered["is_outlier"]]
        self.assertFalse(non_outliers.empty)
        fund_id = non_outliers.iloc[0]["fund_id"]
        similar = cosine_similar_funds(clustered, fund_id, top_n=3)
        self.assertTrue(similar)
        self.assertTrue(all(item["similarity_scope"] == "same_dbscan_cluster" for item in similar))


if __name__ == "__main__":
    unittest.main()
