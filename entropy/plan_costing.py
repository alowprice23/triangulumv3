from entropy.estimator import calculate_n_star

DEFAULT_AVG_TICK_DURATION_SECONDS = 0.5  # 500ms

def estimate_cost(
    h0: float,
    g: float,
    avg_tick_duration: float = DEFAULT_AVG_TICK_DURATION_SECONDS
) -> dict:
    """
    Estimates the cost to fix a bug based on entropy estimates.

    :param h0: The initial entropy of the bug.
    :param g: The estimated information gain per iteration.
    :param avg_tick_duration: The average duration of a single tick in seconds.
    :return: A dictionary with the estimated number of iterations and time to fix.
    """
    n_star = calculate_n_star(h0, g)

    if n_star is None:
        return {
            "iterations": None,
            "time_to_fix_seconds": None,
            "message": "Convergence not guaranteed (g <= 0).",
        }

    time_to_fix_seconds = n_star * avg_tick_duration

    return {
        "iterations": n_star,
        "time_to_fix_seconds": time_to_fix_seconds,
        "message": f"Estimated {n_star} iterations to fix the bug.",
    }
