from main import check_shipping_cost
import pytest

def test_shipping_for_low_total():
  assert check_shipping_cost(50) == 10

def test_shipping_for_high_total():
  assert check_shipping_cost(150) == 0

def test_shipping_for_exact_total():
  # This test will fail because the logic is `> 100` not `>= 100`
  assert check_shipping_cost(100) == 0
