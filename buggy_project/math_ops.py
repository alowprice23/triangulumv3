# This file contains a simple function with a bug.

def add(a, b):
    # The bug is here: it should be a + b
    return a + b + 1
