const createGreeting = require('./index');

describe('createGreeting', () => {
  test('should return a greeting for a string name', () => {
    expect(createGreeting('World')).toBe('Hello, WORLD');
  });

  test('should not throw an error for a numeric input', () => {
    // This test will fail because toUpperCase() cannot be called on a number.
    expect(createGreeting(123)).toBe('Hello, 123');
  });
});
