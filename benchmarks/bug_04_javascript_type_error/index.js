// This function is supposed to concatenate a greeting with a name,
// but it fails if the name is not a string.
function createGreeting(name) {
  return "Hello, " + name.toUpperCase();
}

module.exports = createGreeting;
