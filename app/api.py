from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import DISCLAIMER
from .data_loader import load_funds
from .database import initialize_database
from .recommender import RecommendationEngine
from .schemas import AdvisorContextRequest, AdvisorContextSimulationRequest, RecommendationRequest
from services.advisor_context_engine import generate_advisor_context, simulate_advisor_context


app = FastAPI(
    title="Indian Mutual Fund Recommender",
    description=DISCLAIMER,
    version="0.1.0",
)

engine = RecommendationEngine()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "disclaimer": DISCLAIMER}


@app.get("/funds")
def list_funds(limit: int = 20) -> dict[str, object]:
    funds = load_funds().head(limit)
    return {"count": len(funds), "funds": funds.to_dict(orient="records")}


@app.post("/recommendations")
def create_recommendation(payload: RecommendationRequest) -> dict[str, object]:
    try:
        return engine.recommend(payload.customer, top_n_per_bucket=payload.top_n_per_bucket)
    except Exception as exc:  # pragma: no cover - API boundary
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/advisor-context")
def create_advisor_context(payload: AdvisorContextRequest) -> dict[str, object]:
    try:
        return generate_advisor_context(payload.customer)
    except Exception as exc:  # pragma: no cover - API boundary
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/advisor-context/simulate")
def simulate_context(payload: AdvisorContextSimulationRequest) -> dict[str, object]:
    try:
        return simulate_advisor_context(
            payload.customer,
            payload.adjusted_scores,
            include_recommendation_preview=payload.include_recommendation_preview,
        )
    except Exception as exc:  # pragma: no cover - API boundary
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/admin/load-database")
def load_database() -> dict[str, object]:
    try:
        count = initialize_database()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"loaded_rows": count}
