def check_shipping_cost(cart_total):
  """
  Calculates shipping cost. Free shipping for orders over $100.
  The bug is that it uses > instead of >=, so an order of exactly
  $100 is incorrectly charged for shipping.
  """
  if cart_total > 100:
    return 0 # Free shipping
  else:
    return 10 # Standard shipping
