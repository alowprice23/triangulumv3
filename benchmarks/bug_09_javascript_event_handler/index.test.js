const fs = require('fs');
const path = require('path');

// Load the HTML and JS file into the JSDOM environment
const html = fs.readFileSync(path.resolve(__dirname, './index.html'), 'utf8');
document.body.innerHTML = html;

// Mock the DOMContentLoaded event
const domContentLoadedEvent = new Event('DOMContentLoaded');
document.dispatchEvent(domContentLoadedEvent);

// Now, require the JS file
require('./index.js');

describe('Button Click', () => {
    test('should display a message when the button is clicked', () => {
        const button = document.getElementById('myButton');
        const message = document.getElementById('message');

        // Simulate a click
        button.click();

        // Check if the message is updated
        // This will fail because the event listener is not attached correctly
        expect(message.textContent).toBe('Button clicked!');
    });
});
