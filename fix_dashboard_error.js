// Quick fix for dashboard textContent errors
// Add this to the top of your dashboard.js file

function safeSetTextContent(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    } else {
        console.warn(`Element not found: ${elementId}`);
    }
}

// Replace all instances of:
// document.getElementById('someId').textContent = value;
// With:
// safeSetTextContent('someId', value);

// Or add this check before any textContent assignment:
function checkElementExists(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error(`Missing HTML element: ${elementId}`);
        return false;
    }
    return true;
}

// Example usage:
// if (checkElementExists('totalReports')) {
//     document.getElementById('totalReports').textContent = totalReports;
// }