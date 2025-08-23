from main import get_greeting, User

def test_greeting_with_none():
  # This test will fail with an AttributeError
  assert "Hello, Guest" in get_greeting(None)

def test_greeting_with_user():
  user = User("Alice")
  assert "Hello, Alice" in get_greeting(user)
