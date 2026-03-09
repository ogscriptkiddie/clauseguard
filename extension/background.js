/**
 * background.js — ClauseGuard Service Worker
 *
 * - Shows a red "!" badge on the extension icon when ToS is detected
 * - Clears the badge when the user opens the popup
 * - Relays page text requests from popup.js to content.js
 */

// Clear badge when popup opens (user has seen the alert)
chrome.action.onClicked.addListener((tab) => {
  chrome.action.setBadgeText({ text: "", tabId: tab.id });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

  // ToS/signup page detected — show red badge
  if (message.action === "signupDetected") {
    const tabId = sender.tab.id;

    // Store detection state
    chrome.storage.session.set({
      [`signup_${tabId}`]: {
        url:      message.url,
        tosUrl:   message.tosUrl,
        detected: true,
      }
    });

    // Red badge with "!" on the extension icon
    chrome.action.setBadgeText({ text: "!", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#e74c3c", tabId });
    chrome.action.setTitle({
      tabId,
      title: "ClauseGuard — Terms of Service detected! Click to scan."
    });
  }

  // Relay text extraction request from popup.js → content.js
  if (message.action === "getPageText") {
    chrome.tabs.sendMessage(message.tabId, { action: "extractText" }, (response) => {
      // Clear badge once user actively scans
      chrome.action.setBadgeText({ text: "", tabId: message.tabId });
      chrome.action.setTitle({
        tabId: message.tabId,
        title: "ClauseGuard — Analyze this page"
      });
      sendResponse(response);
    });
    return true;
  }
});
