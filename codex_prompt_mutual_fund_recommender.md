# Build a Mutual Fund Recommender System for Financial Advisors

You are Codex. Build a production-quality prototype for an Indian mutual fund recommendation system used by financial advisors.

## Goal
The advisor enters customer information. The system filters and ranks suitable mutual funds across Equity, Debt, Gold/Commodity, Hybrid, Passive, and International categories. It returns:
1. Customer risk bucket
2. Suggested asset allocation
3. Top recommended funds per asset bucket
4. Mathematical reasoning and explanation
5. Suitability warnings
6. Charts/tables comparing funds

This is a decision-support tool, not a guaranteed investment engine. Add a disclaimer: "For educational/advisory support only; final advice must be verified by a SEBI-registered investment adviser or qualified advisor."

## Tech Stack
Use:
- Python 3.11+
- FastAPI backend
- Pandas + NumPy for preprocessing
- Scikit-learn for ML/ranking/clustering
- SQLAlchemy + PostgreSQL or SQLite for local prototype
- Streamlit or React frontend; choose Streamlit for fastest MVP unless otherwise specified
- Pydantic schemas for request/response validation
- pytest unit tests

## Input: Customer Parameters
Create a form with:
- age
- occupation
- annual_income
- number_of_dependents
- existing_investments_value
- existing_loans_emi_monthly
- emergency_fund_months
- goal_type
- goal_amount
- goal_timeline_years
- investment_amount_monthly
- risk_appetite
- investment_experience
- reaction_to_market_volatility
- need_for_early_withdrawal
- lock_in_acceptance
- tax_slab
- tax_saving_requirements
- preferred_equity_exposure
- international_exposure_pref

## Input: Mutual Fund Parameters
Load `dummy_mutual_funds.csv` with:
- mutual_fund_name, amc, category, sub_category, plan_type, benchmark, risk_level
- min_horizon_years, expense_ratio, exit_load_period_days, lock_in_years
- minimum_investing_amount, aum_cr, nav
- return_1y, return_3y, return_5y, return_since_launch
- sharpe_ratio, sortino_ratio, alpha, beta, calmar_ratio
- downside_deviation, standard_deviation, max_drawdown
- r_squared, info_ratio, tracking_error, capture_ratio
- ttm_yield, monthly_net_expense_ratio, turnover
- inception_date, equity_style_box, load
- min_sip_investment, min_withdrawal, min_no_of_cheques, min_addl_investment, min_balance
- risk_grade, return_grade

## Core Flow

### Step 1: Validate user financial readiness
Create hard-gate warnings:
- If emergency_fund_months < 3: warn "Build emergency fund first"; cap equity allocation.
- If existing_loans_emi_monthly / monthly_income > 0.40: reduce equity allocation.
- If goal_timeline_years < 3: avoid high equity and small/mid-cap funds.
- If need_for_early_withdrawal = High: avoid lock-in funds and long exit-load funds.
- If tax_saving_requirements = Yes and lock_in_acceptance = Yes: include ELSS bucket.

### Step 2: Calculate Risk Capacity Score
Use a weighted score from 0 to 100.

Suggested weights:
- age: 20%
- goal_timeline_years: 25%
- income_surplus_after_emi: 15%
- emergency_fund_months: 15%
- dependents: 10%
- investment_experience: 5%
- market_volatility_reaction: 10%

Convert to risk bucket:
- 0–20: Very Critical
- 21–40: Critical
- 41–60: Balanced
- 61–80: Aggressive
- 81–100: Very Aggressive

Important rules:
- Younger age + far goal = higher equity capacity.
- Older age + near goal = shift to debt/capital preservation.
- User's stated risk appetite should not override objective risk capacity. Use min(stated_risk, computed_capacity) when conflicts are dangerous.

### Step 3: Asset Allocation
Use these default buckets:
- Very Aggressive: 90% equity, 10% debt, 0% gold
- Aggressive: 70% equity, 20% debt, 10% gold
- Balanced: 50% equity, 45% debt, 5% gold
- Critical: 20% equity, 75% debt, 5% gold
- Very Critical: 5% equity, 90% debt, 5% gold

If international_exposure_pref is Moderate/High and timeline >= 5:
- carve out 5–15% from equity allocation into International.

### Step 4: Category-level filtering
For each fund:
- Exclude if minimum investment > user's investment amount
- Exclude if fund min_horizon_years > user's goal_timeline_years + 1
- Exclude ELSS if lock_in_acceptance != Yes
- Exclude high exit load if need_for_early_withdrawal = High
- Exclude Very High risk funds for Very Critical/Critical users except small capped equity allocation
- For goal_timeline < 3, prefer Debt: Liquid, Money Market, Short Duration, Arbitrage
- For timeline >= 7 and risk high, include Flexi Cap, Large & Mid Cap, Mid Cap, Small Cap

### Step 5: Feature Engineering for Fund Performance
Normalize all numeric features by category/sub_category using z-score or robust scaler:
Positive features:
- return_3y, return_5y, sharpe_ratio, sortino_ratio, alpha, calmar_ratio, info_ratio, capture_ratio, aum_cr, return_since_launch

Negative features:
- expense_ratio, standard_deviation, downside_deviation, max_drawdown absolute value, beta above 1.2, tracking_error for passive funds, turnover if very high

Category-specific logic:
- Equity: Sharpe, Sortino, Alpha, 3Y/5Y Return, Drawdown, Expense Ratio
- Debt: Expense Ratio, Downside Deviation, Standard Deviation, TTM Yield, AUM, Drawdown
- Passive: Tracking Error, Expense Ratio, R-squared, AUM, benchmark fit
- Hybrid: Sortino, Calmar, Drawdown, Sharpe, Return consistency
- Gold/Commodity: Drawdown, volatility, correlation/diversification value more than pure return
- International: volatility, drawdown, currency/geography diversification, tracking error for FoF/index

### Step 6: N-dimensional fund similarity and clustering
Implement:
1. Build feature matrix with selected metrics.
2. Impute missing numeric values using median by sub_category.
3. Scale with RobustScaler.
4. Run correlation matrix to remove redundant metrics where |corr| > 0.90.
5. Use PCA/UMAP for visualization.
6. Use KMeans or HDBSCAN/DBSCAN to group funds behaving similarly.
7. Return cluster label and show "similar funds" in each category.

Default MVP:
- Use KMeans with silhouette score from k=3..10.
- Store cluster labels in output dataframe.
- Use cosine similarity to find funds similar to top-ranked funds.

### Step 7: Scoring Formula
Create final score 0–100.

Example:
performance_score =
  0.18 * z(return_3y)
+ 0.18 * z(return_5y)
+ 0.18 * z(sharpe_ratio)
+ 0.14 * z(sortino_ratio)
+ 0.12 * z(alpha)
+ 0.10 * z(calmar_ratio)
+ 0.10 * z(info_ratio)

risk_penalty =
  0.20 * z(expense_ratio)
+ 0.20 * z(standard_deviation)
+ 0.20 * z(downside_deviation)
+ 0.20 * z(abs(max_drawdown))
+ 0.10 * z(beta)
+ 0.10 * z(tracking_error)

suitability_score =
  timeline_match
+ risk_level_match
+ liquidity_match
+ tax_match
+ min_investment_match

final_score =
  0.50 * performance_score
+ 0.35 * suitability_score
- 0.15 * risk_penalty

Scale final score to 0–100.

### Step 8: Output Recommendation
Return:
- recommended asset allocation
- top 5 funds per recommended bucket
- allocation amount per fund
- why recommended
- what risk exists
- what to avoid
- similar fund cluster
- advisor notes

Example:
"Customer is Balanced because age is 42, goal timeline is 6 years, emergency fund is 6 months, and EMI burden is 22%. Recommended allocation: 50% equity, 45% debt, 5% gold."

### Step 9: UI
Create:
- Landing page with customer form
- Fund data upload option
- Recommendation output page
- Category comparison page
- Similar funds/clusters page
- Explainability panel

### Step 10: Testing
Add tests:
- Near-goal older user should not get high equity allocation.
- Young user with 15-year goal can get aggressive allocation.
- High EMI and no emergency fund should cap equity.
- ELSS should not appear if lock-in not accepted.
- Small cap should not appear for goal timeline < 7 years.
- Passive ranking should strongly penalize high tracking error.

## Deliverables
Create files:
- app.py or streamlit_app.py
- recommender/
  - config.py
  - data_loader.py
  - preprocessing.py
  - risk_profiler.py
  - allocation.py
  - fund_filter.py
  - scoring.py
  - clustering.py
  - explain.py
- data/
  - dummy_mutual_funds.csv
  - dummy_customer_profiles.csv
  - asset_allocation_rules.csv
- tests/
  - test_risk_profiler.py
  - test_filtering.py
  - test_scoring.py
- README.md with setup and usage

## Real Data Integration Later
Design data loaders so dummy data can be replaced by:
- AMFI daily NAV data
- MF API scheme/NAV history
- Paid/commercial data for ratios such as Sharpe, Sortino, Alpha, Beta, Capture Ratio, Expense Ratio, Holdings, Risk Grade and Return Grade
Do not hardcode dummy assumptions into production scoring.