from typing import Optional

def explain_entropy_metrics(h0: float, g: float, n_star: Optional[int]) -> str:
    """
    Generates a human-readable explanation of the entropy metrics.

    :param h0: The initial entropy of the bug.
    :param g: The estimated information gain per iteration.
    :param n_star: The estimated number of iterations to fix the bug.
    :return: A string explaining the metrics.
    """
    explanation = f"Entropy-based cost estimation:\n"
    explanation += f"  - Initial Entropy (H₀): {h0:.2f} bits\n"
    explanation += f"    This represents the initial complexity or uncertainty of the bug.\n"
    explanation += f"    A higher H₀ means a larger search space for the solution.\n"
    explanation += f"  - Information Gain (g): {g:.2f} bits per iteration\n"
    explanation += f"    This is the estimated amount of uncertainty we reduce in each iteration.\n"

    if n_star is not None:
        explanation += f"  - Estimated Iterations (N*): {n_star}\n"
        explanation += f"    Based on H₀ and g, we expect to solve this bug in about {n_star} iterations.\n"
    else:
        explanation += f"  - Estimated Iterations (N*): Not available\n"
        explanation += f"    Convergence is not guaranteed because the information gain (g) is zero or negative.\n"

    return explanation
