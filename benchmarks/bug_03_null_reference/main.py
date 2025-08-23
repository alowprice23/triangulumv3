class User:
    def __init__(self, name):
        self.name = name

def get_greeting(user):
  """Returns a greeting. Fails if user is None."""
  # Bug: No check for None user
  return f"Hello, {user.name}"
