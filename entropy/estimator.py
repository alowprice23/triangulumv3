import math

def estimate_h0_from_loc(lines_of_code: int) -> float:
    """
    Estimates the initial entropy (H₀) of a bug based on the lines of code.
    This is a simple heuristic where the search space is proportional to the code size.
    """
    if lines_of_code <= 0:
        return 0.0
    return math.log2(lines_of_code)

def estimate_g_from_test_results(failed_before: int, failed_after: int) -> float:
    """
    Estimates the information gain (g) from the reduction in failing tests.
    """
    if failed_after >= failed_before:
        return 0.0
    if failed_after == 0:
        # If all tests pass, we have gained all the information.
        # We can consider this as a large gain. For simplicity, we can return
        # the entropy of the previous state.
        return math.log2(failed_before)
    return math.log2(failed_before / failed_after)

def calculate_n_star(h0: float, g: float) -> int | None:
    """
    Calculates the expected number of iterations (N*) to solve a bug.
    Returns None if g is zero, as convergence is not guaranteed.
    """
    if g <= 0:
        return None
    return math.ceil(h0 / g)
