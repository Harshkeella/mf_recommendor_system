from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_FUND_CSV = BASE_DIR / "dummy_mutual_funds.csv"
DEFAULT_ALLOCATION_CSV = BASE_DIR / "asset_allocation_rules.csv"
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'mf_recommender.db'}"
DBSCAN_EPS = 1.5
DBSCAN_MIN_SAMPLES = 5
DBSCAN_MIN_DATASET_SIZE = 12

DISCLAIMER = (
    "This is a decision-support prototype for financial advisors. It is not "
    "guaranteed investment advice. Final recommendations must be reviewed by "
    "a certified financial advisor before being shared with customers."
)
