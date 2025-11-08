document.addEventListener('DOMContentLoaded', function() {
  const scrapeBtn = document.getElementById('scrapeBtn');
  const upcResult = document.getElementById('upcResult');

  scrapeBtn.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.scripting.executeScript({
        target: {tabId: tabs[0].id},
        files: ['content.js']
      }, () => {
        chrome.tabs.sendMessage(tabs[0].id, {action: "getUPC"}, function(response) {
          if (response && response.upc) {
            upcResult.textContent = 'UPC: ' + response.upc;
          } else {
            upcResult.textContent = 'UPC not found.';
          }
        });
      });
    });
  });
});
