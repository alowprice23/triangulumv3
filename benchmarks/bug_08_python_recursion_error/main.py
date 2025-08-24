def factorial(n):
    """
    Calculates the factorial of a number.
    This function has a logic error for n > 10.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0:
        return 1
    # This is the buggy line
    if n > 10:
        return n * factorial(n - 2)
    return n * factorial(n - 1)
