const DEFAULT_API_URL = "http://127.0.0.1:8000";
const DEFAULT_TOKEN = "dev-token";

const apiUrlInput = document.getElementById("apiUrl");
const tokenInput = document.getElementById("token");
const deliveryDateInput = document.getElementById("deliveryDate");
const saveButton = document.getElementById("saveButton");
const statusEl = document.getElementById("status");

document.addEventListener("DOMContentLoaded", restoreSettings);
saveButton.addEventListener("click", saveCheckout);
apiUrlInput.addEventListener("change", persistSettings);
tokenInput.addEventListener("change", persistSettings);
deliveryDateInput.addEventListener("change", persistSettings);

async function restoreSettings() {
  const settings = await chrome.storage.local.get({
    apiUrl: DEFAULT_API_URL,
    token: DEFAULT_TOKEN,
    deliveryDate: todayDateValue()
  });

  apiUrlInput.value = settings.apiUrl;
  tokenInput.value = settings.token;
  deliveryDateInput.value = settings.deliveryDate;
}

async function persistSettings() {
  await chrome.storage.local.set({
    apiUrl: normalizeApiUrl(apiUrlInput.value),
    token: tokenInput.value || DEFAULT_TOKEN,
    deliveryDate: deliveryDateInput.value
  });
}

async function saveCheckout() {
  setBusy(true);
  setStatus("Scraping checkout...", "");

  try {
    await persistSettings();
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab?.id || !isNoFrillsUrl(tab.url || "")) {
      throw new Error("Open a nofrills.ca checkout or cart page before saving.");
    }

    const scrapeResult = await chrome.tabs.sendMessage(tab.id, {
      type: "SCRAPE_NOFRILLS_CHECKOUT"
    });

    if (!scrapeResult?.ok) {
      throw new Error(scrapeResult?.error || "The page could not be scraped.");
    }

    if (!scrapeResult.payload.items || scrapeResult.payload.items.length === 0) {
      throw new Error("No checkout items were found on this page.");
    }

    scrapeResult.payload.delivered_at = deliveryDateToDateTime(deliveryDateInput.value);

    const saved = await postSnapshot(scrapeResult.payload);
    setStatus(`Saved snapshot #${saved.id}`, "success");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : "Save failed.", "error");
  } finally {
    setBusy(false);
  }
}

async function postSnapshot(payload) {
  const apiUrl = normalizeApiUrl(apiUrlInput.value || DEFAULT_API_URL);
  const token = tokenInput.value || DEFAULT_TOKEN;
  const response = await fetch(`${apiUrl}/api/checkout-snapshots`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(`Backend rejected the save (${response.status}): ${detail}`);
  }

  return response.json();
}

async function readError(response) {
  try {
    const body = await response.json();
    return body.detail || response.statusText;
  } catch (_error) {
    return response.statusText;
  }
}

function normalizeApiUrl(value) {
  return (value || DEFAULT_API_URL).trim().replace(/\/+$/, "");
}

function deliveryDateToDateTime(value) {
  return value ? `${value}T12:00:00` : null;
}

function todayDateValue() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isNoFrillsUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.hostname === "nofrills.ca" || parsed.hostname.endsWith(".nofrills.ca");
  } catch (_error) {
    return false;
  }
}

function setBusy(isBusy) {
  saveButton.disabled = isBusy;
  saveButton.textContent = isBusy ? "Saving..." : "Save checkout";
}

function setStatus(message, className) {
  statusEl.textContent = message;
  statusEl.className = className;
}
