document.getElementById('autofillButton').addEventListener('click', function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        chrome.tabs.sendMessage(tabs[0].id, { action: "fillInputs" });

        // Show initial loading message
        updateStatusMessage("Processing inputs...", true);
    });
});

// Function to update status message and toggle loading cursor
function updateStatusMessage(message, isLoading) {
    document.getElementById('statusMessage').textContent = message;
    document.body.style.cursor = isLoading ? 'progress' : 'default';
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (message.statusUpdate) {
        updateStatusMessage(message.statusUpdate, message.isLoading);
    }
});