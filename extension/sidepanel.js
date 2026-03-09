/**
 * sidepanel.js — ClauseGuard Side Panel Logic
 *
 * Key design principle: Users don't want to read legal text.
 * Every risk is translated into a plain-English one-liner that explains
 * what it means in real life. The actual clause text is hidden behind
 * a "See clause" toggle for users who want the detail.
 */

const API_URL = "http://localhost:5000/analyze";

// ─── Plain-English translations ───────────────────────────────────────────────
// Maps category + risk_level → a human explanation + emoji + real-life impact

const PLAIN_ENGLISH = {
  data_sharing: {
    HIGH:   { icon: "🔴", title: "They can sell your data",         detail: "This company explicitly reserves the right to sell your personal information to advertisers or data brokers. Your data becomes their product." },
    MEDIUM: { icon: "🟠", title: "They share your data with others", detail: "Your personal information is shared with partner companies, affiliates, or advertisers. You may receive targeted ads or unsolicited contact from third parties." },
    LOW:    { icon: "🟡", title: "Limited data sharing",            detail: "They share some data, but it appears to be anonymized or limited to service providers who help run the platform." },
  },
  tracking_profiling: {
    HIGH:   { icon: "🔴", title: "They track you across the web",    detail: "This company tracks your activity beyond their own site — following you across other websites and apps to build a detailed behavioral profile." },
    MEDIUM: { icon: "🟠", title: "They use your data for targeted ads", detail: "Your browsing habits, purchases, and interests are analyzed to serve you personalized advertisements. Your behavior is being monetized." },
    LOW:    { icon: "🟡", title: "Basic usage tracking",             detail: "Standard analytics and cookies are in use. This is common but worth knowing — they can see how you use their service." },
  },
  third_party_access: {
    HIGH:   { icon: "🔴", title: "Third parties can access your account", detail: "External companies, partners, or potentially government agencies may be granted access to your account data, sometimes without notifying you." },
    MEDIUM: { icon: "🟠", title: "Partner companies can see your data", detail: "Integrated third-party services and business partners may have access to your personal information as part of using this platform." },
    LOW:    { icon: "🟡", title: "Some third-party integrations",    detail: "Links to external services exist, but access appears limited to what's needed to provide the service." },
  },
  data_retention: {
    HIGH:   { icon: "🔴", title: "They may keep your data forever",  detail: "Even after you delete your account, this company may retain your personal data indefinitely. There is no guaranteed deletion." },
    MEDIUM: { icon: "🟠", title: "Your data outlives your account",  detail: "Backup copies and certain records may persist even after you close your account. Full deletion is not guaranteed." },
    LOW:    { icon: "🟡", title: "Standard data retention",          detail: "Data is retained for a defined period, typically as required by law. This is relatively standard practice." },
  },
  arbitration: {
    HIGH:   { icon: "🔴", title: "You give up your right to sue",    detail: "By agreeing, you waive your right to take this company to court or join a class action lawsuit. Disputes must go through private arbitration — on their terms." },
    MEDIUM: { icon: "🟠", title: "Disputes go through arbitration",  detail: "If something goes wrong, you likely can't sue in a regular court. Arbitration typically favors large companies over individual users." },
    LOW:    { icon: "🟡", title: "Preferred dispute resolution",     detail: "The company prefers arbitration but may not fully waive your court rights. Check local laws — some of these clauses aren't enforceable everywhere." },
  },
  liability_limitation: {
    HIGH:   { icon: "🔴", title: "They're not responsible if things go wrong", detail: "The company disclaims all liability. If their service causes you harm, a data breach exposes you, or the product fails — you have limited legal recourse." },
    MEDIUM: { icon: "🟠", title: "Limited accountability",           detail: "Their liability to you is significantly capped. In most disputes, the maximum they owe you is a small dollar amount or the fees you paid." },
    LOW:    { icon: "🟡", title: "Standard liability limits",        detail: "Some limitations on liability exist, as is standard in most software agreements. Not unusually aggressive." },
  },
};

// Taglines for the score card
const SCORE_TAGLINES = {
  HIGH:   "This agreement has serious privacy concerns. Consider your options carefully before accepting.",
  MEDIUM: "Some concerning clauses found. Worth reviewing before you agree.",
  LOW:    "This agreement looks relatively standard. Minor items noted below.",
};


// ─── DOM references ───────────────────────────────────────────────────────────
const states = {
  idle:    document.getElementById("state-idle"),
  loading: document.getElementById("state-loading"),
  error:   document.getElementById("state-error"),
  results: document.getElementById("state-results"),
};

const els = {
  btnAnalyze:   document.getElementById("btn-analyze"),
  btnRetry:     document.getElementById("btn-retry"),
  btnReanalyze: document.getElementById("btn-reanalyze"),
  signupAlert:  document.getElementById("signup-alert"),
  errorMsg:     document.getElementById("error-msg"),
  errorHint:    document.getElementById("error-hint"),
  scoreCard:    document.getElementById("score-card"),
  scoreNumber:  document.getElementById("score-number"),
  scoreVerdict: document.getElementById("score-verdict"),
  scoreTagline: document.getElementById("score-tagline"),
  summaryPills: document.getElementById("summary-pills"),
  categoryGrid: document.getElementById("category-grid"),
  footerStats:  document.getElementById("footer-stats"),
};


// ─── State management ─────────────────────────────────────────────────────────
function showState(name) {
  Object.keys(states).forEach(k => states[k].classList.remove("active"));
  states[name].classList.add("active");
}

function showError(msg, hint = "") {
  els.errorMsg.textContent  = msg;
  els.errorHint.textContent = hint;
  showState("error");
}


// ─── Event listeners ──────────────────────────────────────────────────────────
els.btnAnalyze.addEventListener("click",   runAnalysis);
els.btnRetry.addEventListener("click",     runAnalysis);
els.btnReanalyze.addEventListener("click", runAnalysis);


// ─── Check for signup detection on load ──────────────────────────────────────
async function checkSignupDetection() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;

  chrome.storage.session.get(`signup_${tab.id}`, (result) => {
    const data = result[`signup_${tab.id}`];
    if (data && data.detected) {
      els.signupAlert.style.display = "block";
    }
  });
}

checkSignupDetection();


// ─── Main analysis flow ───────────────────────────────────────────────────────
async function runAnalysis() {
  showState("loading");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) { showError("Could not access the current tab."); return; }

  // Get text from content script via background worker
  let extractResult;
  try {
    extractResult = await chrome.runtime.sendMessage({
      action: "getPageText",
      tabId:  tab.id,
    });
  } catch (err) {
    showError("Cannot read this page.", "Try navigating to a Terms of Service or Privacy Policy page first.");
    return;
  }

  if (!extractResult?.success) {
    showError("Could not extract text from this page.", extractResult?.error || "");
    return;
  }

  if (!extractResult.text || extractResult.text.trim().length < 100) {
    showError("Not enough text found.", "Make sure you're on a Terms of Service or Privacy Policy page.");
    return;
  }

  // Send to Flask API
  let data;
  try {
    const res = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text: extractResult.text }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    if (err.message.includes("fetch") || err.message.includes("Network")) {
      showError(
        "Cannot connect to ClauseGuard backend.",
        "Make sure the Flask server is running: open Git Bash, go to the backend folder, and run 'python app.py'"
      );
    } else {
      showError("Analysis error.", err.message);
    }
    return;
  }

  renderResults(data);
}


// ─── Rendering ────────────────────────────────────────────────────────────────
function renderResults(data) {
  const {
    risk_score, risk_level, category_scores, clauses,
    total_clauses_analyzed, total_risk_clauses_detected, processing_time_ms
  } = data;

  // Score card
  els.scoreCard.className    = `score-card ${risk_level}`;
  els.scoreNumber.textContent = risk_score;
  els.scoreVerdict.textContent = `${risk_level} RISK`;
  els.scoreTagline.textContent = SCORE_TAGLINES[risk_level];

  // Plain-English pills — one per category that has findings
  els.summaryPills.innerHTML = "";
  const categoryOrder = [
    "data_sharing", "tracking_profiling", "third_party_access",
    "data_retention", "arbitration", "liability_limitation"
  ];

  // Collect categories with actual findings, sorted HIGH → MEDIUM → LOW
  const riskOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const foundCategories = categoryOrder
    .filter(cat => category_scores[cat]?.max_risk_level !== "NONE" && category_scores[cat]?.clause_count > 0)
    .sort((a, b) => {
      const ra = riskOrder[category_scores[a].max_risk_level] ?? 3;
      const rb = riskOrder[category_scores[b].max_risk_level] ?? 3;
      return ra - rb;
    });

  if (foundCategories.length === 0) {
    els.summaryPills.innerHTML = `
      <div style="text-align:center; padding: 16px; color: #27ae60; font-size: 12px; background: white; border-radius: 8px;">
        ✅ No significant risks detected in this document.
      </div>`;
  } else {
    foundCategories.forEach(catId => {
      const cat      = category_scores[catId];
      const riskLvl  = cat.max_risk_level;
      const trans    = PLAIN_ENGLISH[catId]?.[riskLvl];
      if (!trans) return;

      // Find the actual clause text for this category
      const matchingClause = clauses.find(c => c.primary_category === catId);
      const clauseSnippet  = matchingClause
        ? matchingClause.text.substring(0, 160) + (matchingClause.text.length > 160 ? "…" : "")
        : null;

      const pill = document.createElement("div");
      pill.className = `summary-pill ${riskLvl}`;

      pill.innerHTML = `
        <div class="pill-icon">${trans.icon}</div>
        <div class="pill-content">
          <div class="pill-title">${trans.title}</div>
          <div class="pill-detail">${trans.detail}</div>
          ${clauseSnippet ? `
            <div class="pill-expand" data-expanded="false">▸ See actual clause</div>
            <div class="pill-clause hidden" style="margin-top:6px; font-size:10px; color:#888; font-style:italic; line-height:1.5; border-top: 1px solid #f0f0f0; padding-top:6px;">${escapeHTML(clauseSnippet)}</div>
          ` : ""}
        </div>
      `;

      // Toggle actual clause text
      const expandBtn   = pill.querySelector(".pill-expand");
      const clauseBlock = pill.querySelector(".pill-clause");
      if (expandBtn && clauseBlock) {
        expandBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          const expanded = expandBtn.dataset.expanded === "true";
          clauseBlock.classList.toggle("hidden", expanded);
          expandBtn.textContent    = expanded ? "▸ See actual clause" : "▾ Hide clause";
          expandBtn.dataset.expanded = String(!expanded);
        });
      }

      els.summaryPills.appendChild(pill);
    });
  }

  // Category breakdown bars
  els.categoryGrid.innerHTML = "";
  categoryOrder.forEach(catId => {
    const cat = category_scores[catId];
    if (!cat) return;
    const riskClass = cat.max_risk_level === "NONE" ? "NONE" : cat.max_risk_level;

    const row = document.createElement("div");
    row.className = "cat-row";
    row.innerHTML = `
      <div class="cat-name">${cat.label}</div>
      <div class="cat-bar-bg">
        <div class="cat-bar-fill ${riskClass}" style="width:${cat.score}%"></div>
      </div>
      <div class="cat-badge ${riskClass}">${riskClass === "NONE" ? "Clean" : riskClass}</div>
    `;
    els.categoryGrid.appendChild(row);
  });

  // Footer
  els.footerStats.textContent =
    `${total_risk_clauses_detected} risks found in ${total_clauses_analyzed} clauses · ${processing_time_ms}ms`;

  showState("results");
}


// ─── Utils ────────────────────────────────────────────────────────────────────
function escapeHTML(str) {
  return str
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
