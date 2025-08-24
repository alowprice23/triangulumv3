def get_last_element(items):
  """
  This function is supposed to return the last element of a list,
  but it has an IndexError for empty lists.
  """
  if not items:
    # The bug is that it doesn't handle the empty list case before indexing.
    pass
  return items[len(items) - 1]
