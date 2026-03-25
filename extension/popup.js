/**
 * popup.js — ClauseGuard Popup Logic
 * Plain-English risk summaries with optional clause detail toggle.
 */

const API_URL = 'https://clauseguard-production-183f.up.railway.app';

const PLAIN_ENGLISH = {
  content_rights: {
    HIGH:   { icon: "🔴", title: "They own your content forever",      detail: "You've granted this company a permanent, irrevocable, royalty-free license to use everything you post — including for commercial purposes or AI training. Even if you delete it, the license may remain." },
    MEDIUM: { icon: "🟠", title: "They have broad rights to your content", detail: "The company can reproduce, modify, and distribute your posts globally as part of running the service. This is common, but the scope varies — some agreements are far broader than needed." },
    LOW:    { icon: "🟡", title: "Standard content hosting license",    detail: "A limited license to host and display your content, as needed to operate the service. This is expected and relatively low risk." },
  },
  data_sharing: {
    HIGH:   { icon: "🔴", title: "They can sell your data",              detail: "This company explicitly reserves the right to sell your personal information to advertisers or data brokers. Your data becomes their product." },
    MEDIUM: { icon: "🟠", title: "They share your data with others",     detail: "Your personal information is shared with partner companies or advertisers. You may receive targeted ads or contact from third parties." },
    LOW:    { icon: "🟡", title: "Limited data sharing",                 detail: "Some data is shared, but it appears to be anonymized or limited to service providers who help run the platform." },
  },
  tracking_profiling: {
    HIGH:   { icon: "🔴", title: "They track you across the web",        detail: "This company follows your activity beyond their own site — across other websites and apps — to build a detailed behavioral profile." },
    MEDIUM: { icon: "🟠", title: "They use your behavior for targeted ads", detail: "Your browsing habits and interests are analyzed to serve you personalized ads. Your behavior is being monetized." },
    LOW:    { icon: "🟡", title: "Basic usage tracking",                 detail: "Standard analytics and cookies are in use. They can see how you use their service." },
  },
  third_party_access: {
    HIGH:   { icon: "🔴", title: "Others can access your account",       detail: "External companies, partners, or potentially government agencies may access your account data, sometimes without notifying you." },
    MEDIUM: { icon: "🟠", title: "Partner companies can see your data",  detail: "Integrated third-party services and business partners may have access to your personal information." },
    LOW:    { icon: "🟡", title: "Some third-party integrations",        detail: "External service links exist, but access appears limited to what's needed to provide the service." },
  },
  data_retention: {
    HIGH:   { icon: "🔴", title: "They may keep your data forever",      detail: "Even after you delete your account, this company may retain your personal data indefinitely. There is no guaranteed deletion." },
    MEDIUM: { icon: "🟠", title: "Your data outlives your account",      detail: "Backup copies may persist even after you close your account. Full deletion is not guaranteed." },
    LOW:    { icon: "🟡", title: "Standard data retention",              detail: "Data is retained for a defined period, typically as required by law." },
  },
  arbitration: {
    HIGH:   { icon: "🔴", title: "You give up your right to sue",        detail: "By agreeing, you waive your right to take this company to court or join a class action lawsuit. Disputes go through private arbitration — on their terms." },
    MEDIUM: { icon: "🟠", title: "Disputes go through arbitration",      detail: "If something goes wrong, you likely can't sue in a regular court. Arbitration typically favors large companies." },
    LOW:    { icon: "🟡", title: "Preferred dispute resolution",         detail: "The company prefers arbitration but may not fully waive your court rights." },
  },
  liability_limitation: {
    HIGH:   { icon: "🔴", title: "They're not responsible if things go wrong", detail: "The company disclaims all liability. If their service causes you harm or a data breach exposes you — you have very limited legal recourse." },
    MEDIUM: { icon: "🟠", title: "Limited accountability",               detail: "Their liability to you is capped. In most disputes the maximum they owe you is a small amount or fees paid." },
    LOW:    { icon: "🟡", title: "Standard liability limits",            detail: "Some liability limitations exist, as is common in most software agreements." },
  },
};

const SCORE_TAGLINES = {
  HIGH:   "Serious privacy concerns found. Think carefully before accepting.",
  MEDIUM: "Some concerning clauses found. Worth reviewing before you agree.",
  LOW:    "This agreement looks relatively standard. Minor items noted below.",
};

const CAT_ORDER = [
  "data_sharing", "tracking_profiling", "third_party_access",
  "data_retention", "arbitration", "liability_limitation", "content_rights"
];

// ── DOM ──────────────────────────────────────────────────────
const states = {
  idle:    document.getElementById("state-idle"),
  loading: document.getElementById("state-loading"),
  error:   document.getElementById("state-error"),
  results: document.getElementById("state-results"),
};

function showState(name) {
  Object.keys(states).forEach(k => states[k].classList.remove("active"));
  states[name].classList.add("active");
}

function showError(msg, hint = "") {
  document.getElementById("error-msg").textContent  = msg;
  document.getElementById("error-hint").textContent = hint;
  showState("error");
}

// ── Signup detection ─────────────────────────────────────────
async function checkSignup() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  chrome.storage.session.get(`signup_${tab.id}`, (res) => {
    if (res[`signup_${tab.id}`]?.detected) {
      document.getElementById("signup-alert").style.display = "block";
    }
  });
}
checkSignup();

// ── Buttons ──────────────────────────────────────────────────
document.getElementById("btn-analyze").addEventListener("click",   run);
document.getElementById("btn-retry").addEventListener("click",     run);
document.getElementById("btn-reanalyze").addEventListener("click", run);

// ── Main flow ────────────────────────────────────────────────
async function run() {
  showState("loading");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) { showError("Could not access the current tab."); return; }

  // Ask background.js to relay to content.js
  let extracted;
  try {
    extracted = await chrome.runtime.sendMessage({ action: "getPageText", tabId: tab.id });
  } catch (e) {
    showError("Cannot read this page.", "Navigate to a Terms of Service or Privacy Policy page and try again.");
    return;
  }

  if (!extracted?.success) {
    showError("Could not extract text.", extracted?.error || "Unknown error.");
    return;
  }

  if (!extracted.text || extracted.text.trim().length < 100) {
    showError("Not enough text found.", "Make sure you are on a Terms of Service or Privacy Policy page.");
    return;
  }

  // Call Flask API
  let data;
  try {
    const res = await fetch(`${API_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: extracted.text }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (e) {
    if (e.message.includes("fetch") || e.message.includes("Network")) {
      showError("Cannot connect to ClauseGuard backend.", "Make sure the Flask server is running: open Git Bash, go to the backend folder, and run 'python app.py'");
    } else {
      showError("Analysis failed.", e.message);
    }
    return;
  }

  render(data);
}

// ── Render results ───────────────────────────────────────────
function render(data) {
  const { risk_score, risk_level, category_scores, clauses,
          total_clauses_analyzed, total_risk_clauses_detected, processing_time_ms } = data;

  // Score card
  const scoreCard = document.getElementById("score-card");
  scoreCard.className = `score-card ${risk_level}`;
  document.getElementById("score-number").textContent  = risk_score;
  document.getElementById("score-verdict").textContent = `${risk_level} RISK`;
  document.getElementById("score-tagline").textContent = SCORE_TAGLINES[risk_level];

  // Pills — one per category with findings, HIGH first
  const pillsEl = document.getElementById("pills");
  pillsEl.innerHTML = "";

  const found = CAT_ORDER
    .filter(c => category_scores[c]?.max_risk_level !== "NONE" && category_scores[c]?.clause_count > 0)
    .sort((a, b) => ({ HIGH: 0, MEDIUM: 1, LOW: 2 }[category_scores[a].max_risk_level] ?? 3)
                  - ({ HIGH: 0, MEDIUM: 1, LOW: 2 }[category_scores[b].max_risk_level] ?? 3));

  if (found.length === 0) {
    pillsEl.innerHTML = `<div style="text-align:center;padding:14px;color:#27ae60;font-size:12px;background:white;border-radius:8px;">✅ No significant risks detected.</div>`;
  } else {
    found.forEach(catId => {
      const cat   = category_scores[catId];
      const lvl   = cat.max_risk_level;
      const trans = PLAIN_ENGLISH[catId]?.[lvl];
      if (!trans) return;

      const clauseMatch   = clauses.find(c => c.primary_category === catId);
      const snippetText   = clauseMatch
        ? clauseMatch.text.substring(0, 160) + (clauseMatch.text.length > 160 ? "…" : "")
        : null;
      const clauseNum = clauseMatch?.clause_number ?? null;
      const totalClauses = total_clauses_analyzed ?? null;
      const clauseRef = clauseNum
        ? `Clause ${clauseNum}${totalClauses ? " of " + totalClauses : ""}`
        : null;

      const pill = document.createElement("div");
      pill.className = `pill ${lvl}`;
      pill.innerHTML = `
        <div class="pill-icon">${trans.icon}</div>
        <div style="flex:1">
          <div class="pill-title">${trans.title}</div>
          <div class="pill-detail">${trans.detail}</div>
          ${snippetText ? `
            <div class="pill-expand" data-open="false">▸ See clause${clauseRef ? " (" + clauseRef + ")" : ""}</div>
            <div class="pill-clause hidden">
              ${clauseRef ? '<span style="font-size:9px;font-weight:700;color:#2e75b6;text-transform:uppercase;letter-spacing:0.5px;">' + clauseRef + ' — use Ctrl+F on the page to find it</span><br><br>' : ""}
              ${esc(snippetText)}
            </div>
          ` : ""}
        </div>`;

      const btn = pill.querySelector(".pill-expand");
      const txt = pill.querySelector(".pill-clause");
      if (btn && txt) {
        btn.addEventListener("click", () => {
          const open = btn.dataset.open === "true";
          txt.classList.toggle("hidden", open);
          btn.textContent    = open ? "▸ See actual clause" : "▾ Hide clause";
          btn.dataset.open   = String(!open);
        });
      }
      pillsEl.appendChild(pill);
    });
  }

  // Category bars
  const catGrid = document.getElementById("cat-grid");
  catGrid.innerHTML = "";
  CAT_ORDER.forEach(catId => {
    const cat = category_scores[catId];
    if (!cat) return;
    const rc = cat.max_risk_level === "NONE" ? "NONE" : cat.max_risk_level;
    const row = document.createElement("div");
    row.className = "cat-row";
    row.innerHTML = `
      <div class="cat-name">${cat.label}</div>
      <div class="cat-bar-bg"><div class="cat-bar-fill ${rc}" style="width:${cat.score}%"></div></div>
      <div class="cat-badge ${rc}">${rc === "NONE" ? "Clean" : rc}</div>`;
    catGrid.appendChild(row);
  });

  document.getElementById("footer-stats").textContent =
    `${total_risk_clauses_detected} risks · ${total_clauses_analyzed} clauses · ${processing_time_ms}ms`;

  showState("results");
}

function esc(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
