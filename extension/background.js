/**
 * background.js — ClauseGuard Service Worker
 *
 * - Shows a red "!" badge on the extension icon when ToS is detected
 * - Clears the badge when the user opens the popup
 * - Relays page text requests from popup.js to content.js
 *
 * v2 — Re-injects content.js if the context is stale (fixes Meta/SPAs where
 *      the content script context is invalidated after client-side navigation).
 */

// Clear badge when popup opens (user has seen the alert)
chrome.action.onClicked.addListener((tab) => {
  chrome.action.setBadgeText({ text: "", tabId: tab.id });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  // ToS/signup page detected — show red badge
  if (message.action === "signupDetected") {
    const tabId = sender.tab.id;

    chrome.storage.session.set({
      [`signup_${tabId}`]: {
        url:      message.url,
        tosUrl:   message.tosUrl,
        detected: true,
      }
    });

    chrome.action.setBadgeText({ text: "!", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#e74c3c", tabId });
    chrome.action.setTitle({
      tabId,
      title: "ClauseGuard — Terms of Service detected! Click to scan."
    });
  }

  // Relay text extraction request from popup.js → content.js
  if (message.action === "getPageText") {
    const tabId = message.tabId;

    // Helper: clear badge after a successful scan
    function clearBadge() {
      chrome.action.setBadgeText({ text: "", tabId });
      chrome.action.setTitle({ tabId, title: "ClauseGuard — Analyze this page" });
    }

    // First attempt — send to existing content script context
    chrome.tabs.sendMessage(tabId, { action: "extractText" }, (response) => {

      // ── Happy path ───────────────────────────────────────────────────────
      if (!chrome.runtime.lastError && response) {
        clearBadge();
        sendResponse(response);
        return;
      }

      // ── Stale context (SPA navigation, Meta, etc.) ───────────────────────
      // Content script context was invalidated. Re-inject content.js and retry.
      const lastErr = chrome.runtime.lastError?.message || "unknown";
      console.warn(`[ClauseGuard] Content script stale (${lastErr}) — re-injecting…`);

      chrome.scripting.executeScript(
        { target: { tabId }, files: ["content.js"] },
        () => {
          if (chrome.runtime.lastError) {
            // Can't inject — probably a chrome:// or other restricted page
            sendResponse({
              success: false,
              error: "Cannot inject on this page: " + chrome.runtime.lastError.message,
            });
            return;
          }

          // Give the freshly injected script ~600ms to initialize
          setTimeout(() => {
            chrome.tabs.sendMessage(tabId, { action: "extractText" }, (retryResponse) => {
              // Always read lastError to prevent "unchecked" warning
              void chrome.runtime.lastError;
              clearBadge();
              sendResponse(
                retryResponse || {
                  success: false,
                  error: "Content script did not respond after re-injection.",
                }
              );
            });
          }, 600);
        }
      );
    });

    return true; // keeps message channel open for async sendResponse
  }
});