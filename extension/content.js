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
 *
 * v2 — expandAllDisclosures() added:
 *   Programmatically expands accordions, <details>, aria-expanded elements
 *   before extraction so hidden clause text (e.g. Meta vendor lists) is captured.
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
    chrome.runtime.sendMessage(
      {
        action:   "signupDetected",
        url:      window.location.href,
        tosUrl:   findTosLink(),
        detected: true,
      },
      () => {
        // Suppress "Receiving end does not exist" — expected in MV3 when the
        // service worker is inactive. Accessing lastError marks it as handled.
        void chrome.runtime.lastError;
      }
    );
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


// ─── Disclosure Expansion ─────────────────────────────────────────────────────
//
// Expands all collapsed accordions, <details> elements, and aria-expanded
// sections in the LIVE DOM before we clone and extract text.
//
// Targets (in order of reliability):
//   1. <details> — native HTML, just set .open = true (no click needed)
//   2. [aria-expanded="false"] — standard ARIA accordion pattern
//   3. [data-state="closed"] — Radix UI / shadcn accordion pattern
//   4. [data-headlessui-state="closed"] — Headless UI (used by some React apps)
//
// Safety guards:
//   - Never clicks submit/reset buttons
//   - Never clicks buttons inside <form> without an explicit role
//   - Skips elements that are hidden or have zero dimensions (already invisible)
//   - Caps at 60 clicks to avoid infinite expansion loops on huge pages
//   - Waits 700ms after all clicks for re-renders to settle

async function expandAllDisclosures() {
  let clickCount = 0;
  const MAX_CLICKS = 60;

  // 1. Native <details> — open directly, no click event needed
  document.querySelectorAll('details:not([open])').forEach(d => {
    d.open = true;
  });

  // 2. ARIA / framework accordion triggers
  const COLLAPSED_SELECTORS = [
    '[aria-expanded="false"]',
    '[data-state="closed"]',
    '[data-headlessui-state="closed"]',
  ].join(',');

  const triggers = Array.from(document.querySelectorAll(COLLAPSED_SELECTORS));

  for (const el of triggers) {
    if (clickCount >= MAX_CLICKS) break;

    // Safety: skip form submit/reset buttons
    const type = (el.getAttribute('type') || '').toLowerCase();
    if (type === 'submit' || type === 'reset') continue;

    // Safety: skip plain <button> inside a <form> with no role (likely form submit)
    const tag  = el.tagName.toLowerCase();
    const role = (el.getAttribute('role') || '').toLowerCase();
    if (tag === 'button' && !role && el.closest('form')) continue;

    // Safety: skip elements with no visual presence (display:none etc.)
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) continue;

    try {
      el.click();
      clickCount++;
    } catch (e) {
      // Silently skip unclickable elements
    }
  }

  // Wait for React/Vue re-renders and CSS transitions to complete
  if (clickCount > 0 || document.querySelectorAll('details').length > 0) {
    await new Promise(r => setTimeout(r, 500));
  }

  return clickCount; // returned for debug logging
}


// ─── Text Extraction ──────────────────────────────────────────────────────────

// Async extraction — expands hidden content first, then extracts.
// Always calls sendResponse via timeout fallback so the port never closes silently.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "extractText") {

    // Safety net: if async path takes too long or throws without catching,
    // fall back to immediate synchronous extraction so popup always gets a response.
    let responded = false;
    const fallbackTimer = setTimeout(() => {
      if (!responded) {
        responded = true;
        try {
          sendResponse({ success: true, text: extractPageText(), url: window.location.href, expanded: 0 });
        } catch(e) {
          sendResponse({ success: false, error: 'Extraction timed out' });
        }
      }
    }, 7000);

    expandAndExtract()
      .then(({ text, expanded }) => {
        if (!responded) {
          responded = true;
          clearTimeout(fallbackTimer);
          sendResponse({ success: true, text, url: window.location.href, expanded });
        }
      })
      .catch(err => {
        if (!responded) {
          responded = true;
          clearTimeout(fallbackTimer);
          // Expansion failed — fall back to synchronous extraction
          try {
            sendResponse({ success: true, text: extractPageText(), url: window.location.href, expanded: 0 });
          } catch(e2) {
            sendResponse({ success: false, error: err.message || 'Extraction failed' });
          }
        }
      });
  }
  return true; // keeps message channel open for async sendResponse
});

async function expandAndExtract() {
  const expanded = await expandAllDisclosures();
  const text     = extractPageText();
  return { text, expanded };
}

function extractPageText() {
  // Clone the live DOM *after* expansions have happened
  const clone = document.body.cloneNode(true);

  // Strip noise elements
  [
    "script","style","noscript","nav","header","footer","iframe",
    "img","svg","button","[role='navigation']","[role='banner']",
    ".cookie-banner","#cookie-consent",".navbar","#header","#footer"
  ].forEach(sel => clone.querySelectorAll(sel).forEach(el => el.remove()));

  // Prefer a known legal content container
  let target = null;
  for (const sel of [
    "main","article","[role='main']",".legal-content",
    ".terms-content",".privacy-content","#legal","#terms","#privacy","#content",".content"
  ]) {
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