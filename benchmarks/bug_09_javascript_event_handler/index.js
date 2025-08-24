document.addEventListener('DOMContentLoaded', function() {
    // This is the buggy line. It should be getElementById
    const button = document.getElementByTagName('button');
    const message = document.getElementById('message');

    button.addEventListener('click', function() {
        message.textContent = 'Button clicked!';
    });
});
