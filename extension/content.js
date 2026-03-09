/**
 * content.js — ClauseGuard Content Script
 *
 * Two jobs:
 *   1. Detect ToS/signup pages and notify background.js to show a badge
 *   2. Extract clean page text when asked by popup.js
 *
 * Detection runs on:
 *   - Initial page load
 *   - DOM mutations (catches React/SPA flows like Spotify's multi-step signup)
 */

// ─── ToS / Signup Detection ───────────────────────────────────────────────────

let lastDetectedUrl = null;
let detectionTimer  = null;

function detectTosPage() {
  const url      = window.location.href.toLowerCase();
  const bodyText = document.body.innerText.toLowerCase();
  const title    = document.title.toLowerCase();

  // --- Signal 1: URL patterns ---
  const urlSignals = [
    /signup/, /sign-up/, /register/, /create.account/, /join/,
    /new.account/, /get.started/, /terms/, /privacy/, /legal/,
    /policy/, /conditions/
  ];
  const urlMatch = urlSignals.some(p => p.test(url));

  // --- Signal 2: Visible text on page ---
  const textSignals = [
    "terms of service", "terms and conditions", "terms of use",
    "privacy policy", "i agree to the", "by signing up",
    "by creating an account", "by continuing", "by registering",
    "by clicking", "you agree to our", "accept our terms",
    "terms & conditions"
  ];
  const textMatch = textSignals.some(p => bodyText.includes(p));

  // --- Signal 3: Form with email + password (signup form) ---
  const inputs    = document.querySelectorAll("input");
  let hasEmail    = false;
  let hasPassword = false;
  inputs.forEach(inp => {
    const t = (inp.type || "").toLowerCase();
    const n = (inp.name || inp.id || inp.placeholder || "").toLowerCase();
    if (t === "email" || n.includes("email") || n.includes("mail")) hasEmail = true;
    if (t === "password") hasPassword = true;
  });
  const hasSignupForm = hasEmail && hasPassword;

  // --- Signal 4: ToS checkbox or link visible ---
  const tosLinkExists = !!findTosLink();
  const hasCheckbox   = Array.from(document.querySelectorAll("input[type=checkbox]"))
    .some(cb => {
      const label = (cb.closest("label") || cb.parentElement || document.body)
        .innerText.toLowerCase();
      return textSignals.some(p => label.includes(p));
    });

  // Trigger if we see ToS text AND at least one other signal
  const shouldAlert = textMatch && (urlMatch || hasSignupForm || tosLinkExists || hasCheckbox);

  if (shouldAlert && url !== lastDetectedUrl) {
    lastDetectedUrl = url;
    chrome.runtime.sendMessage({
      action:   "signupDetected",
      url:      window.location.href,
      tosUrl:   findTosLink(),
      detected: true,
    });
  }
}

function findTosLink() {
  const patterns = [
    "terms of service", "terms and conditions", "terms of use",
    "privacy policy", "user agreement", "terms & conditions"
  ];
  for (const link of document.querySelectorAll("a")) {
    const text = (link.innerText || link.textContent || "").toLowerCase();
    if (patterns.some(p => text.includes(p))) return link.href || null;
  }
  return null;
}

// Run on initial load (with delay for JS-rendered content)
setTimeout(detectTosPage, 1500);

// Watch for DOM changes — catches React SPA flows like Spotify signup step 3
const observer = new MutationObserver(() => {
  clearTimeout(detectionTimer);
  detectionTimer = setTimeout(detectTosPage, 800);
});
observer.observe(document.body, { childList: true, subtree: true });


// ─── Text Extraction ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "extractText") {
    try {
      sendResponse({ success: true, text: extractPageText(), url: window.location.href });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  }
  return true;
});

function extractPageText() {
  const clone = document.body.cloneNode(true);

  ["script","style","noscript","nav","header","footer","iframe",
   "img","svg","button","[role='navigation']","[role='banner']",
   ".cookie-banner","#cookie-consent",".navbar","#header","#footer"
  ].forEach(sel => clone.querySelectorAll(sel).forEach(el => el.remove()));

  let target = null;
  for (const sel of ["main","article","[role='main']",".legal-content",
    ".terms-content",".privacy-content","#legal","#terms","#privacy","#content",".content"]) {
    const el = clone.querySelector(sel);
    if (el && (el.innerText || "").trim().length > 500) { target = el; break; }
  }

  return cleanText((target || clone).innerText || "");
}

function cleanText(text) {
  return text
    .replace(/\r\n/g, "\n").replace(/\r/g, "\n")
    .split("\n")
    .filter(line => {
      const t = line.trim();
      return t.length >= 3 && !/^\d+$/.test(t) && /[a-zA-Z]/.test(t);
    })
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
