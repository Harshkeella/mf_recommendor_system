# Indian Mutual Fund Recommender Prototype

Production-quality prototype for financial advisors to generate decision-support mutual fund recommendations from customer risk capacity, asset allocation rules, fund filters, weighted fund scoring, DBSCAN behavior clustering, and similar-fund analysis.

The included `dummy_mutual_funds.csv` data is synthetic and only suitable for testing the workflow.

## Setup

Use a Python 3.10+ environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the API

```powershell
uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

The requested backend wrapper also works:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Run the Streamlit Advisor UI

```powershell
streamlit run streamlit_app.py
```

## Run Tests

```powershell
python -m pytest
```

or, without pytest:

```powershell
python -m unittest discover -s tests
```

## Main Modules

- `app/data_loader.py`: CSV schema validation and loading
- `app/preprocessing.py`: median imputation and category-relative metric normalization
- `app/risk_profile.py` / `app/risk_profiler.py`: weighted customer risk capacity scoring
- `app/allocation.py` / `app/asset_allocator.py`: risk-bucket allocation plus caps for short timelines, low emergency fund, and high EMI burden
- `app/filtering.py` / `app/fund_filter.py`: hard rejection rules with reasons; soft mismatches become score penalties or warnings
- `app/scoring.py` / `app/fund_scorer.py`: customer fit, fund performance, fund risk penalty, and final score
- `app/clustering.py` / `app/fund_similarity.py`: DBSCAN behavior clusters, outlier detection, PCA coordinates, same-cluster cosine-similar funds
- `app/recommender.py` / `app/recommendation_engine.py`: end-to-end orchestration
- `app/explanations.py` / `app/explanation_generator.py`: advisor-readable recommendation reasons
- `app/api.py`: FastAPI backend
- `streamlit_app.py`: advisor-facing frontend

The `backend/` and `services/` packages are compatibility wrappers around the working `app/` modules, matching the requested structure without duplicating logic.

## DBSCAN Behavior Clustering

DBSCAN is used only for mutual-fund behavior grouping, not supervised prediction. It uses fund metrics such as `return_3y`, `return_5y`, `sharpe_ratio`, `sortino_ratio`, `alpha`, `beta`, drawdown, volatility, expense, tracking error, capture ratio, and turnover. Customer data is not used to fit DBSCAN.

Configuration lives in [app/config.py](D:/mf_recommender_starter_pack/app/config.py):

```python
DBSCAN_EPS = 1.5
DBSCAN_MIN_SAMPLES = 5
```

Cluster label `-1` means DBSCAN noise/outlier. Recommended outlier funds receive a manual-review warning. Similar funds are found inside the same DBSCAN cluster where possible; outlier similarity falls back to global approximate cosine similarity.

The engine starts with the configured eps and automatically relaxes it if the synthetic dataset produces too many noise points. Diagnostics report both `configured_eps` and the effective `eps`.

## Disclaimer

This is a decision-support prototype for financial advisors. It is not guaranteed investment advice. Final recommendations must be reviewed by a certified financial advisor before being shared with customers.
