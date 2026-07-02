from __future__ import annotations

import importlib

import pandas as pd
import streamlit as st

from app.config import DISCLAIMER
import app.filtering as filtering
import app.recommender as recommender
import app.schemas as schemas
import app.scoring as scoring
import services.advisor_context_engine as advisor_context_engine


# Streamlit keeps imported modules alive between reruns. Reload the modules most
# likely to change during this prototype so sidebar model fields do not go stale.
schemas = importlib.reload(schemas)
filtering = importlib.reload(filtering)
scoring = importlib.reload(scoring)
recommender = importlib.reload(recommender)
advisor_context_engine = importlib.reload(advisor_context_engine)
RecommendationEngine = recommender.RecommendationEngine
CustomerProfile = schemas.CustomerProfile
CONTEXT_SCORE_KEYS = advisor_context_engine.CONTEXT_SCORE_KEYS
generate_advisor_context = advisor_context_engine.generate_advisor_context


RISK_SCALE_FALLBACK = {
    "Very Critical": {"min": 0, "max": 20, "equity": 5, "debt": 90, "gold": 5},
    "Critical": {"min": 21, "max": 40, "equity": 20, "debt": 75, "gold": 5},
    "Balanced": {"min": 41, "max": 60, "equity": 50, "debt": 45, "gold": 5},
    "Aggressive": {"min": 61, "max": 80, "equity": 70, "debt": 20, "gold": 10},
    "Very Aggressive": {"min": 81, "max": 100, "equity": 90, "debt": 10, "gold": 0},
}


st.set_page_config(page_title="Indian MF Recommender", layout="wide")

st.title("Indian Mutual Fund Recommender")
st.caption("Advisor decision-support prototype")

with st.sidebar:
    st.header("Customer")
    name = st.text_input("Name", value="Rahul")
    age = st.number_input("Age", min_value=18, max_value=100, value=36)
    occupation = st.selectbox("Occupation", ["Salaried", "Business Owner", "Government Employee", "Professional", "Retired", "Student"])
    annual_income = st.number_input("Annual income", min_value=0.0, value=1800000.0, step=50000.0)
    dependents = st.number_input("Dependents", min_value=0, value=1)
    existing_investments = st.number_input("Existing investments", min_value=0.0, value=300000.0, step=25000.0)
    existing_emi = st.number_input("Existing loans/EMIs monthly", min_value=0.0, value=25000.0, step=5000.0)
    emergency_fund = st.number_input("Emergency fund months", min_value=0.0, value=6.0, step=0.5)

    st.header("Goal")
    goal_type = st.selectbox("Goal type", ["Wealth Creation", "Retirement", "Child Education", "Marriage", "House", "Emergency Corpus", "Tax Saving"])
    goal_amount = st.number_input("Goal amount", min_value=0.0, value=5000000.0, step=100000.0)
    timeline = st.number_input("Goal timeline years", min_value=0.5, value=10.0, step=0.5)
    monthly_amount = st.number_input("Monthly investment amount", min_value=0.0, value=30000.0, step=1000.0)

    st.header("Preferences")
    risk_appetite = st.selectbox("Risk appetite", ["Very Critical", "Critical", "Balanced", "Aggressive", "Very Aggressive"], index=2)
    experience = st.selectbox("Investment experience", ["Beginner", "Intermediate", "Experienced"])
    volatility = st.selectbox("Reaction to market volatility", ["Panic and sell", "Worried but hold", "Neutral", "Very comfortable"])
    early_withdrawal = st.selectbox("Need for early withdrawal", ["Low", "Medium", "High"], index=1)
    lock_in = st.selectbox("Lock-in acceptance", ["No", "Maybe", "Yes"])
    tax_slab = st.selectbox("Tax slab", [0, 5, 10, 20, 30], index=3)
    tax_saving = st.selectbox("Tax-saving requirement", ["No", "Yes"])
    international_pref = st.selectbox("International exposure preference", ["None", "Moderate", "High"])
    investment_mode = st.selectbox("Investment mode", ["SIP", "Lumpsum", "Monthly"], index=0)
    nomination_status = st.selectbox("Nomination status", ["Unknown", "Yes", "No", "Missing"], index=0)
    run = st.button("Generate recommendations", type="primary", use_container_width=True)


if run or "latest_customer_profile" in st.session_state:
    if run:
        customer = CustomerProfile(
            name=name,
            age=age,
            occupation=occupation,
            annual_income=annual_income,
            number_of_dependents=dependents,
            existing_investments_value=existing_investments,
            existing_loans_emi_monthly=existing_emi,
            emergency_fund_months=emergency_fund,
            goal_type=goal_type,
            goal_amount=goal_amount,
            goal_timeline_years=timeline,
            investment_amount_monthly=monthly_amount,
            investment_mode=investment_mode,
            risk_appetite=risk_appetite,
            investment_experience=experience,
            reaction_to_market_volatility=volatility,
            need_for_early_withdrawal=early_withdrawal,
            lock_in_acceptance=lock_in,
            tax_slab=tax_slab,
            tax_saving_requirements=tax_saving,
            preferred_equity_exposure=None,
            international_exposure_pref=international_pref,
            nomination_status=nomination_status,
        )
        st.session_state["latest_customer_profile"] = customer.model_dump()
    else:
        customer = CustomerProfile(**st.session_state["latest_customer_profile"])

    advisor_context = generate_advisor_context(customer)
    insight_items = advisor_context["advisor_context"]
    for key in CONTEXT_SCORE_KEYS:
        slider_key = f"advisor_context_slider_{key}"
        if run or slider_key not in st.session_state:
            st.session_state[slider_key] = int(insight_items[key]["score"])
    adjusted_scores = {
        key: float(st.session_state[f"advisor_context_slider_{key}"])
        for key in CONTEXT_SCORE_KEYS
    }
    advisor_context = generate_advisor_context(customer, adjusted_scores)
    insight_items = advisor_context["advisor_context"]
    result = RecommendationEngine().recommend(
        customer,
        top_n_per_bucket=3,
        advisor_context_scores=adjusted_scores,
    )

    left, middle, right = st.columns(3)
    left.metric("Risk bucket", result["customer_risk_bucket"])
    middle.metric("Risk score", result["risk_score"])
    right.metric("Monthly SIP", f"INR {customer.monthly_investment_amount:,.0f}")

    allocation = pd.DataFrame(
        [{"bucket": k.title(), "allocation_pct": v} for k, v in result["recommended_asset_allocation"].items()]
    )
    st.subheader("Recommended asset allocation")
    st.bar_chart(allocation, x="bucket", y="allocation_pct", horizontal=True)
    with st.expander("Risk score scale"):
        scale_rows = []
        for bucket, scale in result.get("risk_scale", RISK_SCALE_FALLBACK).items():
            scale_rows.append(
                {
                    "risk_bucket": bucket,
                    "score_range": f"{scale['min']}-{scale['max']}",
                    "equity_pct": scale["equity"],
                    "debt_pct": scale["debt"],
                    "gold_pct": scale["gold"],
                }
            )
        st.dataframe(pd.DataFrame(scale_rows), use_container_width=True, hide_index=True)

    if result["warnings"]:
        st.warning("\n".join(f"- {warning}" for warning in result["warnings"]))

    st.subheader("Advisor Context & Client Insight")
    st.caption("Move these sliders to adjust fund filtering and ranking. The recommendation table updates on every slider change.")

    insight_labels = {
        "life_stage_time_horizon": "Life Stage & Time Horizon",
        "financial_stability": "Financial Stability",
        "goal_feasibility": "Goal Feasibility & Investment Capacity",
        "behavioral_risk_tolerance": "Behavioral Risk Tolerance",
        "liquidity_commitment": "Liquidity & Commitment Flexibility",
        "portfolio_diversification": "Portfolio Diversification Need",
        "tax_documentation": "Tax & Documentation Readiness",
    }
    insight_cols = st.columns(2)
    for idx, key in enumerate(CONTEXT_SCORE_KEYS):
        insight = insight_items[key]
        slider_key = f"advisor_context_slider_{key}"
        with insight_cols[idx % 2]:
            st.markdown(f"**{insight_labels[key]}**")
            current_score = st.slider(
                insight_labels[key],
                min_value=0,
                max_value=100,
                key=slider_key,
                label_visibility="collapsed",
            )
            st.write(f"{current_score}/100 - {insight['label']}")
            st.caption(insight["explanation"])
            st.info(insight["advisor_note"])
            with st.expander("How this was calculated?"):
                st.write(insight["how_calculated"])
                if insight.get("warnings"):
                    st.warning("\n".join(f"- {warning}" for warning in insight["warnings"]))

    context_cols = st.columns(3)
    with context_cols[0]:
        st.markdown("**Positive signals**")
        for item in advisor_context["positive_signals"]:
            st.write(f"- {item}")
    with context_cols[1]:
        st.markdown("**Red flags**")
        for item in advisor_context["red_flags"]:
            st.write(f"- {item}")
    with context_cols[2]:
        st.markdown("**Questions to ask**")
        for item in advisor_context["advisor_questions"]:
            st.write(f"- {item}")
    st.info(advisor_context["overall_summary"])
    st.caption(advisor_context["disclaimer"])

    recommendations = pd.DataFrame(result["recommendations"])
    rejected = pd.DataFrame(result["rejected_funds"])
    clustered = pd.DataFrame(result["clustered_funds"])

    tabs = st.tabs([
        "Recommendation Result",
        "Fund Comparison",
        "DBSCAN Cluster View",
        "Similar Funds View",
        "Rejected Funds and Warnings",
        "Diagnostics",
    ])

    with tabs[0]:
        visible_cols = [
            "allocation_bucket",
            "allocation_amount_monthly",
            "mutual_fund_name",
            "amc",
            "category",
            "sub_category",
            "risk_level",
            "final_score",
            "customer_fit_score",
            "performance_score",
            "suitability_score",
            "risk_penalty",
            "dbscan_cluster_id",
            "is_outlier",
            "expense_ratio",
            "return_3y",
            "return_5y",
            "sharpe_ratio",
        ]
        st.dataframe(recommendations[[c for c in visible_cols if c in recommendations.columns]], use_container_width=True)

    with tabs[1]:
        comparison_cols = [
            "mutual_fund_name",
            "category",
            "sub_category",
            "final_score",
            "customer_fit_score",
            "performance_score",
            "risk_penalty",
            "return_3y",
            "return_5y",
            "sharpe_ratio",
            "sortino_ratio",
            "standard_deviation",
            "max_drawdown",
            "expense_ratio",
        ]
        st.dataframe(recommendations[[c for c in comparison_cols if c in recommendations.columns]], use_container_width=True)

    with tabs[2]:
        if not clustered.empty:
            st.scatter_chart(clustered, x="pca_x", y="pca_y", color="dbscan_cluster_id", size="final_score")
            st.dataframe(clustered, use_container_width=True, hide_index=True)

    with tabs[3]:
        for item in result["recommendations"]:
            st.markdown(f"**{item['mutual_fund_name']}**")
            st.write(item["explanation"])
            similar = item.get("similar_funds", [])
            if similar:
                st.caption("Similar funds")
                st.dataframe(pd.DataFrame(similar), use_container_width=True, hide_index=True)

    with tabs[4]:
        if result["warnings"]:
            st.warning("\n".join(f"- {warning}" for warning in result["warnings"]))
        st.dataframe(rejected, use_container_width=True, hide_index=True)

    with tabs[5]:
        st.json(result["risk_components"])
        st.write("Selected cluster metrics:", result["cluster_diagnostics"].get("selected_metrics", []))
        st.write("DBSCAN eps:", result["cluster_diagnostics"].get("eps"))
        st.write("DBSCAN min samples:", result["cluster_diagnostics"].get("min_samples"))
        st.write("DBSCAN clusters:", result["cluster_diagnostics"].get("cluster_count"))
        st.write("DBSCAN outliers:", result["cluster_diagnostics"].get("noise_count"))
        st.write("Tuned eps suggestion:", result["cluster_diagnostics"].get("tuned_eps_suggestion"))

st.divider()
st.caption(DISCLAIMER)
