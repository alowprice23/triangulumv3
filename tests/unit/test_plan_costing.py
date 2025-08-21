import pytest
from entropy.plan_costing import estimate_cost, DEFAULT_AVG_TICK_DURATION_SECONDS

def test_estimate_cost_valid():
    """Tests estimating cost with valid inputs."""
    cost = estimate_cost(h0=10.0, g=1.0)
    assert cost["iterations"] == 10
    assert cost["time_to_fix_seconds"] == 10 * DEFAULT_AVG_TICK_DURATION_SECONDS
    assert "Estimated 10 iterations" in cost["message"]

def test_estimate_cost_zero_g():
    """Tests estimating cost with zero information gain."""
    cost = estimate_cost(h0=10.0, g=0.0)
    assert cost["iterations"] is None
    assert cost["time_to_fix_seconds"] is None
    assert "Convergence not guaranteed" in cost["message"]

def test_estimate_cost_negative_g():
    """Tests estimating cost with negative information gain."""
    cost = estimate_cost(h0=10.0, g=-1.0)
    assert cost["iterations"] is None
    assert cost["time_to_fix_seconds"] is None
    assert "Convergence not guaranteed" in cost["message"]

def test_estimate_cost_custom_tick_duration():
    """Tests estimating cost with a custom average tick duration."""
    cost = estimate_cost(h0=10.0, g=1.0, avg_tick_duration=2.0)
    assert cost["iterations"] == 10
    assert cost["time_to_fix_seconds"] == 20.0
