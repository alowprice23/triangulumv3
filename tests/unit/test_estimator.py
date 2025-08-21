import pytest
import math
from entropy.estimator import (
    estimate_h0_from_loc,
    estimate_g_from_test_results,
    calculate_n_star,
)

def test_estimate_h0_from_loc():
    """Tests the H₀ estimation from lines of code."""
    assert estimate_h0_from_loc(1024) == 10.0
    assert estimate_h0_from_loc(1) == 0.0
    assert estimate_h0_from_loc(0) == 0.0
    assert estimate_h0_from_loc(-10) == 0.0

def test_estimate_g_from_test_results():
    """Tests the information gain (g) estimation from test results."""
    assert estimate_g_from_test_results(10, 5) == 1.0
    assert estimate_g_from_test_results(10, 10) == 0.0
    assert estimate_g_from_test_results(5, 10) == 0.0
    assert estimate_g_from_test_results(10, 0) == math.log2(10)

def test_calculate_n_star():
    """Tests the N* calculation."""
    assert calculate_n_star(10.0, 1.0) == 10
    assert calculate_n_star(10.0, 2.0) == 5
    assert calculate_n_star(10.5, 1.0) == 11
    assert calculate_n_star(10.0, 0.0) is None
    assert calculate_n_star(10.0, -1.0) is None
