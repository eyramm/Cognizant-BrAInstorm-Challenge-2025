function scrapeUPC() {
  // Look for any element in modal that contains this label
  const elements = document.querySelectorAll('div, span, p, li, strong, b');
  for (let el of elements) {
    if (el.textContent.trim() === 'Universal Product Code (UPC check)') {
      // Possible parent structure: label then value as next sibling or parent/next child
      let valueNode = el.nextElementSibling;
      if (valueNode && /\d{8,}/.test(valueNode.textContent)) {
        return valueNode.textContent.match(/\d{8,}/)[0];
      }
      // Or, sometimes value is in the parent
      if (el.parentNode && el.parentNode.childNodes.length >= 2) {
        let s = Array.from(el.parentNode.childNodes)
          .map(n => n.textContent)
          .join(' ');
        let match = s.match(/Universal Product Code \(UPC check\)\s*(\d{8,})/);
        if (match) return match[1];
      }
    }
  }
  const upcFallback = document.body.innerText.match(/UPC[^\d]*(\d{8,})/);
  if (upcFallback) return upcFallback[1];
  return null;
}


chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getUPC") {
    const upc = scrapeUPC();
    sendResponse({ upc });
  }
});
