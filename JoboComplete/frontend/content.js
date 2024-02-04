// Warning: hackathon level spaghetti code

chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    if (request.action === "fillInputs") {
        var allInputs = document.querySelectorAll('input[type="text"], input[type="email"], textarea, input[type="radio"]');

        // Objects to hold details
        var textInputDetails = []; // Array for text input details
        var radioButtonDetails = {};
        var textareaDetails = []; // Array for textarea details

        Array.from(allInputs).filter(input => input.offsetParent !== null).forEach(input => {
            if (input.type === "radio") {
                // Handling for radio buttons
                if (!radioButtonDetails[input.name]) {
                    radioButtonDetails[input.name] = {
                        type: input.type,
                        name: input.name,
                        options: [],
                        labelOrText: findLabelOrText(input) // Only fetch label once for each group
                    };
                }
                radioButtonDetails[input.name].options.push({
                    value: input.value,
                    checked: input.checked
                });
            } else if (input.tagName.toLowerCase() === "textarea") {
                // Handling for textarea inputs
                textareaDetails.push({
                    id: input.id,
                    name: input.name,
                    placeholder: input.placeholder
                });
            } else {
                // Handling for text and email inputs (focusing only on the name attribute)
                textInputDetails.push({
                    name: input.name
                });
            }
        });

        // Convert radioButtonDetails object into an array
        var radioButtonDetailsArray = Object.values(radioButtonDetails);

        console.log(textInputDetails);
        console.log(radioButtonDetailsArray);
        console.log(textareaDetails);

        sendResponse({ status: "Inputs processed" });

        // Handle text inputs
        fillTextInputs(textInputDetails).then(() => {
            // Send message to popup
            chrome.runtime.sendMessage({ statusUpdate: "Text inputs handled.", isLoading: true });

            // After handling text inputs, handle radio buttons
            return fillRadioButtons(radioButtonDetailsArray);
        }).then(() => {
            // Send another message to popup
            chrome.runtime.sendMessage({ statusUpdate: "Radio buttons handled.", isLoading: true });

            // After handling radio buttons, handle textarea inputs
            fillTextareas(textareaDetails);
        }).then(() => {
            // Final message
            chrome.runtime.sendMessage({ statusUpdate: "Textarea inputs handled.", isLoading: false });
        }).catch(error => {
            console.error('Error:', error);
            // Send error message
            chrome.runtime.sendMessage({ statusUpdate: "Error occurred: " + error, isLoading: false });
        });

        return true; // Indicates that the response is sent asynchronously
    }
});

function findLabelOrText(input) {
    if (input.labels && input.labels.length > 0) {
        return input.labels[0].innerText.trim();
    }

    var parentDiv = input.closest('.application-question');
    if (parentDiv) {
        var descriptiveText = parentDiv.querySelector('.text');
        if (descriptiveText) {
            return descriptiveText.innerText.trim();
        }
    }

    var siblingSpan = input.nextElementSibling;
    if (siblingSpan && (siblingSpan.tagName.toLowerCase() === 'span' || siblingSpan.tagName.toLowerCase() === 'div')) {
        return siblingSpan.innerText.trim();
    }

    return null;
}

async function sendDataToBackend(details, url) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(details)
    });
    return await response.json();
}

function fillRadioButtons(radioButtonDetails) {
    sendDataToBackend(radioButtonDetails, 'http://localhost:8000/generate_radio_response')
        .then(radioResponses => {
            console.log("Radio Responses:", radioResponses); // Keep this line for debugging
            radioResponses.forEach(item => {
                let radioOption = document.querySelector(`input[name="${item.name}"][value="${item.selectedValue}"]`);
                if (radioOption) {
                    radioOption.checked = true;
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function fillTextInputs(textInputDetails) {
    return sendDataToBackend(textInputDetails, 'http://localhost:8000/generate_text_response')
        .then(textInputResponses => {
            textInputResponses.forEach(item => {
                let inputElement = document.querySelector(`input[name="${item.identifier}"]`);
                if (inputElement) {
                    inputElement.value = item.value;
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function fillTextareas(textareaDetails) {
    sendDataToBackend(textareaDetails, 'http://localhost:8000/generate_textarea_response')
        .then(textareaResponses => {
            textareaResponses.forEach(item => {
                let textarea = document.querySelector(`textarea[name="${item.identifier}"]`);
                if (!textarea) {
                    textarea = document.querySelector(`textarea[id="${item.identifier}"]`);
                }
                if (textarea) {
                    textarea.value = item.value;
                }
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}