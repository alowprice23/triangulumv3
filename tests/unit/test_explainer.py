import pytest
from entropy.explainer import explain_entropy_metrics

def test_explain_entropy_metrics_valid():
    """Tests the explanation with valid metrics."""
    explanation = explain_entropy_metrics(h0=10.0, g=1.0, n_star=10)
    assert "Initial Entropy (H₀): 10.00 bits" in explanation
    assert "Information Gain (g): 1.00 bits per iteration" in explanation
    assert "Estimated Iterations (N*): 10" in explanation
    assert "solve this bug in about 10 iterations" in explanation

def test_explain_entropy_metrics_none_n_star():
    """Tests the explanation when N* is not available."""
    explanation = explain_entropy_metrics(h0=10.0, g=0.0, n_star=None)
    assert "Initial Entropy (H₀): 10.00 bits" in explanation
    assert "Information Gain (g): 0.00 bits per iteration" in explanation
    assert "Estimated Iterations (N*): Not available" in explanation
    assert "Convergence is not guaranteed" in explanation
