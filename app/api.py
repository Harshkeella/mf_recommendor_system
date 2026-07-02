from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from .config import DISCLAIMER
from .data_loader import load_funds
from .database import initialize_database
from .recommender import RecommendationEngine
from .schemas import AdvisorContextRequest, AdvisorContextSimulationRequest, RecommendationRequest
from .web_home import HOME_PAGE_HTML
from services.advisor_context_engine import generate_advisor_context, simulate_advisor_context


app = FastAPI(
    title="Indian Mutual Fund Recommender",
    description=DISCLAIMER,
    version="0.1.0",
)

engine = RecommendationEngine()


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return HOME_PAGE_HTML
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Indian Mutual Fund Recommender</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #17202a;
      --muted: #5e6b78;
      --line: #d8dee6;
      --accent: #0f766e;
      --accent-2: #1d4ed8;
      --warn: #9a3412;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, Segoe UI, system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 22px clamp(18px, 4vw, 48px);
    }
    main {
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto 48px;
      display: grid;
      grid-template-columns: minmax(260px, 360px) 1fr;
      gap: 18px;
    }
    h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: 0; }
    h2 { margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }
    p { color: var(--muted); line-height: 1.55; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .stack { display: grid; gap: 12px; }
    label { display: grid; gap: 6px; font-size: 13px; color: var(--muted); }
    input, select {
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 10px;
      font: inherit;
      color: var(--ink);
      background: #fff;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    button, a.button {
      border: 0;
      border-radius: 6px;
      min-height: 40px;
      padding: 9px 12px;
      font: inherit;
      font-weight: 650;
      cursor: pointer;
      text-align: center;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    button.primary { background: var(--accent); color: white; }
    button.secondary, a.button { background: #e8eef7; color: #17365f; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; }
    .summary {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
    }
    .metric span { display: block; color: var(--muted); font-size: 12px; }
    .metric strong { display: block; margin-top: 6px; font-size: 20px; }
    .cards { display: grid; gap: 12px; }
    .card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fff;
    }
    .card h3 { margin: 0 0 6px; font-size: 16px; }
    .meta { color: var(--muted); font-size: 13px; }
    pre {
      max-height: 360px;
      overflow: auto;
      margin: 0;
      padding: 12px;
      border-radius: 8px;
      background: #111827;
      color: #e5e7eb;
      font-size: 12px;
      line-height: 1.45;
    }
    .notice {
      border-left: 4px solid var(--warn);
      background: #fff7ed;
      padding: 10px 12px;
      color: #7c2d12;
      border-radius: 6px;
    }
    @media (max-width: 840px) {
      main { grid-template-columns: 1fr; }
      .summary { grid-template-columns: 1fr; }
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Indian Mutual Fund Recommender</h1>
    <p>Advisor decision-support API deployed on Vercel. Generate a sample recommendation or adjust the profile below.</p>
  </header>
  <main>
    <section class="panel stack">
      <h2>Customer Profile</h2>
      <div class="grid">
        <label>Name <input id="name" value="Rahul"></label>
        <label>Age <input id="age" type="number" value="35"></label>
        <label>Annual income <input id="annual_income" type="number" value="1800000"></label>
        <label>Monthly investment <input id="monthly_investment_amount" type="number" value="30000"></label>
        <label>Goal amount <input id="goal_amount" type="number" value="5000000"></label>
        <label>Timeline years <input id="goal_timeline_years" type="number" value="10"></label>
        <label>Emergency fund months <input id="emergency_fund_months" type="number" value="6"></label>
        <label>Monthly EMI <input id="existing_loans_emi_monthly" type="number" value="20000"></label>
      </div>
      <label>Risk appetite
        <select id="risk_appetite">
          <option>Very Critical</option>
          <option>Critical</option>
          <option selected>Balanced</option>
          <option>Aggressive</option>
          <option>Very Aggressive</option>
        </select>
      </label>
      <label>Investment experience
        <select id="investment_experience">
          <option>Beginner</option>
          <option selected>Intermediate</option>
          <option>Experienced</option>
        </select>
      </label>
      <label>Volatility reaction
        <select id="reaction_to_market_volatility">
          <option>Panic and sell</option>
          <option>Worried but hold</option>
          <option selected>Neutral</option>
          <option>Very comfortable</option>
        </select>
      </label>
      <div class="actions">
        <button class="primary" onclick="generateRecommendations()">Generate recommendations</button>
        <button class="secondary" onclick="loadFunds()">Preview funds</button>
        <a class="button" href="/docs">API docs</a>
      </div>
      <p class="notice">Prototype only. Final investment advice must be reviewed by a certified financial advisor.</p>
    </section>
    <section class="stack">
      <div class="panel stack">
        <h2>Output</h2>
        <div id="summary" class="summary"></div>
        <div id="cards" class="cards"></div>
      </div>
      <div class="panel stack">
        <h2>Raw API Response</h2>
        <pre id="raw">{}</pre>
      </div>
    </section>
  </main>
  <script>
    const numberFields = [
      "age", "annual_income", "monthly_investment_amount", "goal_amount",
      "goal_timeline_years", "emergency_fund_months", "existing_loans_emi_monthly"
    ];

    function value(id) {
      return numberFields.includes(id)
        ? Number(document.getElementById(id).value)
        : document.getElementById(id).value;
    }

    function profile() {
      return {
        name: value("name"),
        age: value("age"),
        occupation: "Salaried",
        annual_income: value("annual_income"),
        number_of_dependents: 1,
        existing_investments_value: 250000,
        existing_loans_emi_monthly: value("existing_loans_emi_monthly"),
        emergency_fund_months: value("emergency_fund_months"),
        goal_type: "Wealth Creation",
        goal_amount: value("goal_amount"),
        goal_timeline_years: value("goal_timeline_years"),
        investment_amount_monthly: value("monthly_investment_amount"),
        investment_mode: "SIP",
        risk_appetite: value("risk_appetite"),
        investment_experience: value("investment_experience"),
        reaction_to_market_volatility: value("reaction_to_market_volatility"),
        need_for_early_withdrawal: "Medium",
        lock_in_acceptance: "Yes",
        tax_slab: 20,
        tax_saving_requirements: "No",
        preferred_equity_exposure: 60,
        international_exposure_pref: "Moderate",
        nomination_status: "Yes"
      };
    }

    async function postJson(path, payload) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      return data;
    }

    function allocationText(allocation) {
      if (!allocation) return "Not available";
      return Object.entries(allocation).map(([key, val]) => `${key}: ${val}%`).join(" | ");
    }

    function renderRecommendations(data) {
      document.getElementById("raw").textContent = JSON.stringify(data, null, 2);
      const allocation = data.recommended_asset_allocation || {};
      document.getElementById("summary").innerHTML = `
        <div class="metric"><span>Risk bucket</span><strong>${data.customer_risk_bucket || "N/A"}</strong></div>
        <div class="metric"><span>Risk score</span><strong>${data.customer_risk_score ?? "N/A"}</strong></div>
        <div class="metric"><span>Allocation</span><strong>${allocationText(allocation)}</strong></div>
      `;
      const recommendations = data.recommendations || [];
      document.getElementById("cards").innerHTML = recommendations.slice(0, 8).map((item) => {
        const name = item.mutual_fund_name || item.fund_name || item.scheme_name || "Recommended fund";
        const score = item.final_score ?? item.score ?? item.customer_fit_score ?? "N/A";
        const bucket = item.allocation_bucket || item.category || "fund";
        const reason = item.explanation || item.recommendation_reason || item.reason || "";
        return `
          <article class="card">
            <h3>${name}</h3>
            <div class="meta">${bucket} | score: ${score}</div>
            <p>${reason}</p>
          </article>
        `;
      }).join("") || "<p>No recommendations returned.</p>";
    }

    async function generateRecommendations() {
      setLoading("Generating recommendations...");
      try {
        const data = await postJson("/recommendations", {
          customer: profile(),
          top_n_per_bucket: 3
        });
        renderRecommendations(data);
      } catch (error) {
        showError(error);
      }
    }

    async function loadFunds() {
      setLoading("Loading fund universe...");
      try {
        const response = await fetch("/funds?limit=8");
        const data = await response.json();
        document.getElementById("raw").textContent = JSON.stringify(data, null, 2);
        document.getElementById("summary").innerHTML = `
          <div class="metric"><span>Funds loaded</span><strong>${data.count}</strong></div>
          <div class="metric"><span>Endpoint</span><strong>/funds</strong></div>
          <div class="metric"><span>Status</span><strong>ok</strong></div>
        `;
        document.getElementById("cards").innerHTML = (data.funds || []).map((fund) => `
          <article class="card">
            <h3>${fund.mutual_fund_name || fund.scheme_name || "Fund"}</h3>
            <div class="meta">${fund.category || ""} ${fund.sub_category || ""}</div>
          </article>
        `).join("");
      } catch (error) {
        showError(error);
      }
    }

    function setLoading(message) {
      document.getElementById("summary").innerHTML = "";
      document.getElementById("cards").innerHTML = `<p>${message}</p>`;
      document.getElementById("raw").textContent = "{}";
    }

    function showError(error) {
      document.getElementById("cards").innerHTML = `<p class="notice">${error.message}</p>`;
      document.getElementById("raw").textContent = String(error.stack || error.message);
    }

    generateRecommendations();
  </script>
</body>
</html>
"""


@app.get("/api-info")
def api_info() -> dict[str, object]:
    return {
        "service": "Indian Mutual Fund Recommender",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


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
