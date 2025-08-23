def count_items(items):
  """Counts items in a list. Has an off-by-one error."""
  count = 0
  for i in range(len(items) - 1): # Bug: should be range(len(items))
    count += 1
  return count
