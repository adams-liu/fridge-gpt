const MONEY_PATTERN = /\$?\s*([0-9]+(?:[.,][0-9]{2})?)/;
const QUANTITY_PATTERN = /(?:qty|quantity)\D*([0-9]+(?:\.[0-9]+)?)/i;

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "SCRAPE_NOFRILLS_CHECKOUT") {
    return false;
  }

  try {
    sendResponse({ ok: true, payload: scrapeCheckout() });
  } catch (error) {
    sendResponse({
      ok: false,
      error: error instanceof Error ? error.message : "Unable to scrape checkout page"
    });
  }

  return true;
});

function scrapeCheckout() {
  const warnings = [];
  const items = collectItems(warnings);
  const totals = collectTotals();

  if (items.length === 0) {
    warnings.push("No checkout items were detected from visible page content.");
  }

  return {
    source: "nofrills",
    page_url: window.location.href,
    captured_at: new Date().toISOString(),
    delivered_at: null,
    subtotal: totals.subtotal,
    total: totals.total,
    items,
    raw_parser_warnings: warnings
  };
}

function collectItems(warnings) {
  const productsContainer = document.querySelector(".grocery-cart-products");
  if (!productsContainer) {
    warnings.push("Could not find .grocery-cart-products container.");
    return [];
  }

  const selectors = [
    ".product-tracking[data-track-products-array]",
    "li.cart-entry-list__item",
    "[data-testid*='cart'][data-testid*='item']",
    "[data-testid*='basket'][data-testid*='item']",
    "[data-testid*='checkout'][data-testid*='item']",
    "[class*='cart'][class*='item']",
    "[class*='basket'][class*='item']",
    "[class*='checkout'][class*='item']",
    "li"
  ];

  const candidates = uniqueElements(
    selectors.flatMap((selector) => Array.from(productsContainer.querySelectorAll(selector)))
  ).filter(isVisible);

  const items = [];
  const seen = new Set();

  for (const element of candidates) {
    const text = normalizeText(element.innerText || element.textContent || "");
    if (!looksLikeItem(text)) {
      continue;
    }

    const item = parseItem(element, text);
    if (!item.name || item.name.length < 2 || item.line_total === null) {
      continue;
    }

    const key = `${item.name}|${item.quantity ?? ""}|${item.line_total ?? ""}`;
    if (seen.has(key)) {
      continue;
    }

    seen.add(key);
    items.push(item);
  }

  if (items.length === 0) {
    warnings.push("The scraper could not identify item rows with the current selectors.");
  }

  return items;
}

function parseItem(element, text) {
  const trackedProduct = extractTrackedProduct(element);
  const prices = extractMoneyValues(text);
  const lineTotal = prices.length > 0 ? prices[prices.length - 1] : null;
  const unitPrice = prices.length > 1 ? prices[0] : null;
  const quantity = extractQuantity(element, text, trackedProduct);
  const name = trackedProduct?.productName || extractName(element, text);
  const trackedUnitPrice = parseMoney(trackedProduct?.productPrice);

  return {
    name,
    quantity,
    unit_price: trackedUnitPrice ?? unitPrice,
    line_total: lineTotal,
    shelf_life: null,
    amount: "full"
  };
}

function extractTrackedProduct(element) {
  const trackingElement = element.matches(".product-tracking[data-track-products-array]")
    ? element
    : element.querySelector(".product-tracking[data-track-products-array]");

  if (!trackingElement) {
    return null;
  }

  try {
    const products = JSON.parse(trackingElement.getAttribute("data-track-products-array") || "[]");
    return products[0] || null;
  } catch (_error) {
    return null;
  }
}

function extractName(element, fallbackText) {
  const nameSelectors = [
    "[data-testid*='name']",
    "[data-testid*='title']",
    "[class*='name']",
    "[class*='title']",
    "h1",
    "h2",
    "h3",
    "h4"
  ];

  for (const selector of nameSelectors) {
    const match = element.querySelector(selector);
    const text = normalizeText(match?.innerText || match?.textContent || "");
    if (text && !MONEY_PATTERN.test(text) && !/qty|quantity|subtotal|total/i.test(text)) {
      return text;
    }
  }

  return fallbackText
    .split(/\$|\bqty\b|\bquantity\b/i)[0]
    .replace(/\s{2,}/g, " ")
    .trim()
    .slice(0, 300);
}

function collectTotals() {
  const text = normalizeText(document.body.innerText || "");
  return {
    subtotal: findLabeledMoney(text, "subtotal"),
    total: findLabeledMoney(text, "total")
  };
}

function findLabeledMoney(text, label) {
  const regex = new RegExp(`${label}\\s*\\$?\\s*([0-9]+(?:[.,][0-9]{2})?)`, "i");
  const match = text.match(regex);
  return match ? parseMoney(match[1]) : null;
}

function looksLikeItem(text) {
  if (!text || text.length < 4) {
    return false;
  }

  if (!MONEY_PATTERN.test(text)) {
    return false;
  }

  if (/subtotal|total|tax|fees?|delivery|pickup|payment|pc optimum/i.test(text)) {
    return false;
  }

  return /[a-z]/i.test(text);
}

function extractMoneyValues(text) {
  return Array.from(text.matchAll(/\$?\s*([0-9]+(?:[.,][0-9]{2}))/g))
    .map((match) => parseMoney(match[1]))
    .filter((value) => value !== null);
}

function extractQuantity(element, text, trackedProduct) {
  const quantityInput = element.querySelector(".quantity-selector__quantity__input[aria-label='Quantity']");
  const inputQuantity = Number(quantityInput?.value);
  if (Number.isFinite(inputQuantity)) {
    return inputQuantity;
  }

  if (Number.isFinite(trackedProduct?.productQuantity)) {
    return trackedProduct.productQuantity;
  }

  const labeled = text.match(QUANTITY_PATTERN);
  if (labeled) {
    return Number(labeled[1]);
  }

  const compact = text.match(/\b([0-9]+)\s*(?:ea|each|x)\b/i);
  return compact ? Number(compact[1]) : null;
}

function parseMoney(value) {
  const parsed = Number(String(value).replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeText(text) {
  return text.replace(/\s+/g, " ").trim();
}

function uniqueElements(elements) {
  return Array.from(new Set(elements));
}

function isVisible(element) {
  const rect = element.getBoundingClientRect();
  const style = window.getComputedStyle(element);
  return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
}
