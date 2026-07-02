from __future__ import annotations


HOME_PAGE_HTML = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FinOne MF Advisor</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --surface: #ffffff;
      --surface-soft: #f9fafb;
      --ink: #111827;
      --muted: #5b6776;
      --line: #d9e0e8;
      --green: #0f766e;
      --blue: #1d4ed8;
      --amber: #b45309;
      --red: #b42318;
      --shadow: 0 14px 36px rgba(17, 24, 39, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, Segoe UI, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    button, input, select { font: inherit; }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px clamp(16px, 4vw, 48px);
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(10px);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .mark {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      color: #fff;
      background: linear-gradient(135deg, #0f766e, #1d4ed8);
      font-weight: 800;
    }

    .brand h1 {
      margin: 0;
      font-size: 18px;
      letter-spacing: 0;
    }

    .brand p {
      margin: 2px 0 0;
      color: var(--muted);
      font-size: 12px;
    }

    .top-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .status-pill {
      border: 1px solid #b7e2d8;
      color: #075c53;
      background: #e7f7f4;
      padding: 7px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
    }

    .app {
      width: min(1440px, calc(100% - 28px));
      margin: 18px auto 44px;
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 16px;
    }

    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }

    .sidebar {
      align-self: start;
      position: sticky;
      top: 78px;
      padding: 18px;
      display: grid;
      gap: 16px;
    }

    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 12px;
    }

    h2 {
      margin: 0;
      font-size: 17px;
      letter-spacing: 0;
    }

    h3 {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }

    p {
      color: var(--muted);
      line-height: 1.5;
    }

    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.25;
    }

    input, select {
      min-width: 0;
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px 9px;
      background: #fff;
      color: var(--ink);
      outline: none;
    }

    input:focus, select:focus {
      border-color: var(--blue);
      box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12);
    }

    .full { grid-column: 1 / -1; }

    .button-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }

    button, a.button {
      min-height: 40px;
      border: 0;
      border-radius: 6px;
      padding: 9px 12px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      font-weight: 750;
      text-decoration: none;
      cursor: pointer;
      white-space: nowrap;
    }

    .primary { background: var(--green); color: #fff; }
    .secondary { background: #e9eef6; color: #17365f; }
    .ghost { background: #fff; color: var(--blue); border: 1px solid var(--line); }

    .content {
      display: grid;
      gap: 16px;
    }

    .hero {
      padding: clamp(18px, 3vw, 26px);
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      align-items: center;
    }

    .hero h2 {
      font-size: clamp(22px, 3vw, 34px);
      line-height: 1.1;
      max-width: 760px;
    }

    .hero-copy {
      margin: 10px 0 0;
      max-width: 760px;
    }

    .hero-aside {
      border: 1px solid var(--line);
      background: var(--surface-soft);
      border-radius: 8px;
      padding: 14px;
      display: grid;
      gap: 12px;
    }

    .quick-facts {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .fact, .metric, .card, .allocation-card {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 8px;
      padding: 13px;
    }

    .fact span, .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
    }

    .fact strong, .metric strong {
      display: block;
      margin-top: 5px;
      font-size: 20px;
      letter-spacing: 0;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }

    .allocation-wrap {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .bars {
      display: grid;
      gap: 12px;
      margin-top: 12px;
    }

    .bar-row {
      display: grid;
      gap: 6px;
    }

    .bar-label {
      display: flex;
      justify-content: space-between;
      color: var(--muted);
      font-size: 12px;
      gap: 8px;
    }

    .track {
      height: 10px;
      border-radius: 999px;
      background: #edf1f5;
      overflow: hidden;
    }

    .fill {
      height: 100%;
      border-radius: inherit;
      background: var(--green);
      width: 0%;
      transition: width 280ms ease;
    }

    .fill.debt { background: var(--blue); }
    .fill.gold { background: var(--amber); }

    .warning-list {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .warning-list li {
      border-left: 4px solid var(--amber);
      background: #fff7ed;
      color: #7c2d12;
      border-radius: 6px;
      padding: 9px 10px;
      font-size: 13px;
    }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      padding: 16px 18px 0;
    }

    .tabs {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fff;
    }

    .tab {
      border-radius: 0;
      background: #fff;
      color: var(--muted);
      min-height: 36px;
      padding: 7px 12px;
    }

    .tab.active {
      background: #e7f7f4;
      color: #075c53;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      padding: 16px 18px 18px;
    }

    .card {
      display: grid;
      gap: 10px;
      min-height: 230px;
    }

    .card-top {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 8px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 3px 8px;
      background: #edf1f7;
      color: #243b53;
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .score {
      color: var(--green);
      font-weight: 850;
      font-size: 18px;
    }

    .card p {
      margin: 0;
      font-size: 13px;
    }

    .mini-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .mini {
      background: var(--surface-soft);
      border-radius: 6px;
      padding: 8px;
      font-size: 12px;
    }

    .mini span {
      display: block;
      color: var(--muted);
      margin-bottom: 3px;
    }

    .table-wrap {
      padding: 0 18px 18px;
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }

    th, td {
      text-align: left;
      padding: 11px 12px;
      border-bottom: 1px solid var(--line);
      font-size: 13px;
      vertical-align: top;
    }

    th {
      background: #f5f7fa;
      color: #334155;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
    }

    tr:last-child td { border-bottom: 0; }

    details {
      padding: 0 18px 18px;
    }

    summary {
      cursor: pointer;
      color: var(--blue);
      font-weight: 750;
      margin-bottom: 10px;
    }

    pre {
      max-height: 360px;
      overflow: auto;
      margin: 0;
      padding: 13px;
      border-radius: 8px;
      background: #111827;
      color: #e5e7eb;
      font-size: 12px;
      line-height: 1.45;
    }

    .empty {
      padding: 20px;
      color: var(--muted);
    }

    .client-note {
      padding: 12px;
      border-radius: 8px;
      background: #fffbeb;
      color: #713f12;
      font-size: 13px;
      line-height: 1.45;
    }

    @media (max-width: 1100px) {
      .app { grid-template-columns: 1fr; }
      .sidebar { position: static; }
      .hero { grid-template-columns: 1fr; }
      .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

    @media (max-width: 720px) {
      .topbar { align-items: flex-start; }
      .app { width: min(100% - 20px, 1440px); }
      .form-grid, .quick-facts, .allocation-wrap, .cards, .metrics {
        grid-template-columns: 1fr;
      }
      .button-row { grid-template-columns: 1fr; }
      .brand h1 { font-size: 16px; }
    }
  </style>
</head>
<body>
  <nav class="topbar">
    <div class="brand">
      <div class="mark">MF</div>
      <div>
        <h1>FinOne MF Advisor</h1>
        <p>Client-ready mutual fund recommendation demo</p>
      </div>
    </div>
    <div class="top-actions">
      <span class="status-pill" id="serviceStatus">Live on Vercel</span>
      <a class="button ghost" href="/docs" target="_blank" rel="noreferrer">API Docs</a>
    </div>
  </nav>

  <div class="app">
    <aside class="panel sidebar">
      <section>
        <div class="section-title">
          <h2>Seeded Client</h2>
          <span class="badge">Demo</span>
        </div>
        <div class="form-grid">
          <label>Name <input id="name" value="Rahul Mehta"></label>
          <label>Age <input id="age" type="number" value="35"></label>
          <label>Annual income <input id="annual_income" type="number" value="1800000"></label>
          <label>Monthly SIP <input id="monthly_investment_amount" type="number" value="30000"></label>
          <label>Goal amount <input id="goal_amount" type="number" value="5000000"></label>
          <label>Timeline years <input id="goal_timeline_years" type="number" value="10"></label>
          <label>Emergency fund months <input id="emergency_fund_months" type="number" value="6"></label>
          <label>Monthly EMI <input id="existing_loans_emi_monthly" type="number" value="20000"></label>
          <label class="full">Risk appetite
            <select id="risk_appetite">
              <option>Very Critical</option>
              <option>Critical</option>
              <option selected>Balanced</option>
              <option>Aggressive</option>
              <option>Very Aggressive</option>
            </select>
          </label>
          <label class="full">Investment experience
            <select id="investment_experience">
              <option>Beginner</option>
              <option selected>Intermediate</option>
              <option>Experienced</option>
            </select>
          </label>
          <label class="full">Market volatility reaction
            <select id="reaction_to_market_volatility">
              <option>Panic and sell</option>
              <option>Worried but hold</option>
              <option selected>Neutral</option>
              <option>Very comfortable</option>
            </select>
          </label>
        </div>
      </section>
      <div class="button-row">
        <button class="primary" onclick="generateRecommendations()">Run Analysis</button>
        <button class="secondary" onclick="resetSeed()">Reset Seed</button>
      </div>
      <button class="ghost" onclick="loadFunds()">View Fund Universe</button>
      <div class="client-note">
        This is a decision-support prototype using synthetic sample data. It is suitable for product demonstration, not final investment advice.
      </div>
    </aside>

    <main class="content">
      <section class="panel hero">
        <div>
          <h2>Advisor-ready recommendations for a seeded Indian mutual fund client profile.</h2>
          <p class="hero-copy">The application evaluates risk capacity, stated appetite, goal timeline, liquidity, EMI pressure, DBSCAN fund behavior clusters, and suitability scores before producing an allocation and fund shortlist.</p>
        </div>
        <div class="hero-aside">
          <div class="quick-facts">
            <div class="fact"><span>Profile</span><strong id="profileFact">Rahul</strong></div>
            <div class="fact"><span>Goal</span><strong id="goalFact">50L</strong></div>
            <div class="fact"><span>SIP</span><strong id="sipFact">30K</strong></div>
          </div>
          <p id="lastUpdated">Loading seeded recommendation...</p>
        </div>
      </section>

      <section class="metrics" id="metrics"></section>

      <section class="allocation-wrap">
        <div class="panel allocation-card">
          <div class="section-title">
            <h2>Recommended Allocation</h2>
            <span class="badge" id="allocationBadge">Pending</span>
          </div>
          <div class="bars" id="allocationBars"></div>
        </div>
        <div class="panel allocation-card">
          <div class="section-title">
            <h2>Suitability Notes</h2>
            <span class="badge">Rules</span>
          </div>
          <ul class="warning-list" id="warnings"></ul>
        </div>
      </section>

      <section class="panel">
        <div class="toolbar">
          <div>
            <h2>Recommendation Shortlist</h2>
            <p id="recommendationSummary" style="margin: 5px 0 0;">Generating shortlist...</p>
          </div>
          <div class="tabs">
            <button class="tab active" id="cardsTab" onclick="showView('cards')">Cards</button>
            <button class="tab" id="tableTab" onclick="showView('table')">Table</button>
            <button class="tab" id="jsonTab" onclick="showView('json')">JSON</button>
          </div>
        </div>
        <div id="cardsView" class="cards"></div>
        <div id="tableView" class="table-wrap" style="display:none;"></div>
        <details id="jsonView" style="display:none;">
          <summary>Raw API response</summary>
          <pre id="raw">{}</pre>
        </details>
      </section>
    </main>
  </div>

  <script>
    const numberFields = [
      "age", "annual_income", "monthly_investment_amount", "goal_amount",
      "goal_timeline_years", "emergency_fund_months", "existing_loans_emi_monthly"
    ];

    const seedProfile = {
      name: "Rahul Mehta",
      age: 35,
      annual_income: 1800000,
      monthly_investment_amount: 30000,
      goal_amount: 5000000,
      goal_timeline_years: 10,
      emergency_fund_months: 6,
      existing_loans_emi_monthly: 20000,
      risk_appetite: "Balanced",
      investment_experience: "Intermediate",
      reaction_to_market_volatility: "Neutral"
    };

    function byId(id) {
      return document.getElementById(id);
    }

    function value(id) {
      return numberFields.includes(id) ? Number(byId(id).value) : byId(id).value;
    }

    function formatINR(value) {
      const amount = Number(value || 0);
      return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0
      }).format(amount);
    }

    function compactINR(value) {
      const amount = Number(value || 0);
      if (amount >= 10000000) return `${(amount / 10000000).toFixed(1)}Cr`;
      if (amount >= 100000) return `${(amount / 100000).toFixed(1)}L`;
      if (amount >= 1000) return `${Math.round(amount / 1000)}K`;
      return `${amount}`;
    }

    function resetSeed() {
      Object.entries(seedProfile).forEach(([key, val]) => {
        if (byId(key)) byId(key).value = val;
      });
      generateRecommendations();
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

    function setLoading(message) {
      byId("serviceStatus").textContent = "Working";
      byId("recommendationSummary").textContent = message;
      byId("cardsView").innerHTML = `<div class="empty">${message}</div>`;
      byId("tableView").innerHTML = "";
      byId("raw").textContent = "{}";
    }

    function showError(error) {
      byId("serviceStatus").textContent = "Needs attention";
      byId("cardsView").innerHTML = `<div class="empty">${error.message}</div>`;
      byId("raw").textContent = String(error.stack || error.message);
    }

    function renderMetrics(data) {
      const score = data.final_risk_score ?? data.risk_score ?? "N/A";
      const rawScore = data.raw_risk_score ?? "N/A";
      const bucket = data.customer_risk_bucket || "N/A";
      const count = (data.recommendations || []).length;
      byId("metrics").innerHTML = `
        <div class="metric"><span>Risk bucket</span><strong>${bucket}</strong></div>
        <div class="metric"><span>Final risk score</span><strong>${score}</strong></div>
        <div class="metric"><span>Raw capacity score</span><strong>${rawScore}</strong></div>
        <div class="metric"><span>Shortlisted funds</span><strong>${count}</strong></div>
      `;
      byId("allocationBadge").textContent = bucket;
    }

    function renderAllocation(data) {
      const allocation = data.recommended_asset_allocation || {};
      const labels = [
        ["equity", "Equity", "fill"],
        ["debt", "Debt", "fill debt"],
        ["gold", "Gold", "fill gold"]
      ];
      byId("allocationBars").innerHTML = labels.map(([key, label, cls]) => {
        const pct = Number(allocation[key] || 0);
        return `
          <div class="bar-row">
            <div class="bar-label"><span>${label}</span><strong>${pct}%</strong></div>
            <div class="track"><div class="${cls}" style="width:${pct}%"></div></div>
          </div>
        `;
      }).join("");

      const notes = [
        ...(data.applied_safety_rules || []),
        ...(data.warnings || [])
      ].filter(Boolean);
      byId("warnings").innerHTML = (notes.length ? notes : ["No blocking rule conflicts for this seeded profile."])
        .slice(0, 5)
        .map((note) => `<li>${note}</li>`)
        .join("");
    }

    function renderCards(items) {
      byId("cardsView").innerHTML = items.map((item) => {
        const score = Number(item.final_score || 0).toFixed(1);
        const monthly = formatINR(item.allocation_amount_monthly || 0);
        const bucket = item.allocation_bucket || item.asset_bucket || item.category || "fund";
        const category = [item.category, item.sub_category].filter(Boolean).join(" / ");
        const explanation = item.explanation || "Suitable for the selected customer profile.";
        return `
          <article class="card">
            <div class="card-top">
              <div>
                <h3>${item.mutual_fund_name || "Recommended fund"}</h3>
                <p>${category}</p>
              </div>
              <span class="badge">${bucket}</span>
            </div>
            <div class="mini-grid">
              <div class="mini"><span>Final score</span><strong>${score}</strong></div>
              <div class="mini"><span>Monthly allocation</span><strong>${monthly}</strong></div>
              <div class="mini"><span>3Y return</span><strong>${item.return_3y ?? "N/A"}%</strong></div>
              <div class="mini"><span>Risk</span><strong>${item.risk_level || item.risk_grade || "N/A"}</strong></div>
            </div>
            <p>${explanation}</p>
          </article>
        `;
      }).join("") || `<div class="empty">No recommendations returned for this profile.</div>`;
    }

    function renderTable(items) {
      byId("tableView").innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Fund</th>
              <th>Bucket</th>
              <th>Score</th>
              <th>Monthly</th>
              <th>3Y</th>
              <th>Expense</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            ${items.map((item) => `
              <tr>
                <td><strong>${item.mutual_fund_name || "Recommended fund"}</strong><br><span>${item.category || ""} ${item.sub_category || ""}</span></td>
                <td>${item.allocation_bucket || item.asset_bucket || "N/A"}</td>
                <td>${Number(item.final_score || 0).toFixed(1)}</td>
                <td>${formatINR(item.allocation_amount_monthly || 0)}</td>
                <td>${item.return_3y ?? "N/A"}%</td>
                <td>${item.expense_ratio ?? "N/A"}%</td>
                <td>${item.risk_level || item.risk_grade || "N/A"}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      `;
    }

    function renderRecommendations(data) {
      const items = data.recommendations || [];
      const p = profile();
      byId("serviceStatus").textContent = "Ready";
      byId("profileFact").textContent = p.name.split(" ")[0] || "Client";
      byId("goalFact").textContent = compactINR(p.goal_amount);
      byId("sipFact").textContent = compactINR(p.monthly_investment_amount);
      byId("lastUpdated").textContent = `Seeded demo generated ${items.length} recommendations for ${p.name}.`;
      byId("recommendationSummary").textContent = `${items.length} funds mapped to a ${data.customer_risk_bucket} profile with ${formatINR(p.monthly_investment_amount)} monthly SIP.`;
      byId("raw").textContent = JSON.stringify(data, null, 2);
      renderMetrics(data);
      renderAllocation(data);
      renderCards(items);
      renderTable(items);
    }

    async function generateRecommendations() {
      setLoading("Generating seeded recommendation output...");
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
      setLoading("Loading fund universe preview...");
      try {
        const response = await fetch("/funds?limit=12");
        const data = await response.json();
        byId("serviceStatus").textContent = "Ready";
        byId("recommendationSummary").textContent = `${data.count} sample funds loaded from the seeded universe.`;
        byId("metrics").innerHTML = `
          <div class="metric"><span>Preview count</span><strong>${data.count}</strong></div>
          <div class="metric"><span>Endpoint</span><strong>/funds</strong></div>
          <div class="metric"><span>Status</span><strong>Ready</strong></div>
          <div class="metric"><span>Dataset</span><strong>Seeded</strong></div>
        `;
        byId("allocationBars").innerHTML = `<p>Run analysis to view allocation bars.</p>`;
        byId("warnings").innerHTML = `<li>Fund data is synthetic and seeded for demonstration.</li>`;
        byId("cardsView").innerHTML = (data.funds || []).map((fund) => `
          <article class="card">
            <div class="card-top">
              <div>
                <h3>${fund.mutual_fund_name || "Fund"}</h3>
                <p>${fund.category || ""} / ${fund.sub_category || ""}</p>
              </div>
              <span class="badge">${fund.risk_level || "fund"}</span>
            </div>
            <div class="mini-grid">
              <div class="mini"><span>3Y return</span><strong>${fund.return_3y ?? "N/A"}%</strong></div>
              <div class="mini"><span>5Y return</span><strong>${fund.return_5y ?? "N/A"}%</strong></div>
              <div class="mini"><span>Expense</span><strong>${fund.expense_ratio ?? "N/A"}%</strong></div>
              <div class="mini"><span>AUM</span><strong>${compactINR((fund.aum_cr || 0) * 10000000)}</strong></div>
            </div>
          </article>
        `).join("");
        byId("tableView").innerHTML = "";
        byId("raw").textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        showError(error);
      }
    }

    function showView(view) {
      const views = ["cards", "table", "json"];
      views.forEach((name) => {
        byId(`${name}View`).style.display = name === view ? (name === "json" ? "block" : name === "table" ? "block" : "grid") : "none";
        byId(`${name}Tab`).classList.toggle("active", name === view);
      });
    }

    generateRecommendations();
  </script>
</body>
</html>
"""
