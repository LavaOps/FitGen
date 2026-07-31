# validation.py

"""
Validation utilities for generated test inputs.

Each target function returns a unique branch label.
So we validate branch coverage by running the original function
and checking whether the returned label equals the target.
"""

from benchmark_registry import BENCHMARKS


def get_reached_branch(function_name, chromosome):
    """
    Run the original target function and return the reached branch label.
    """

    if function_name not in BENCHMARKS:
        raise ValueError(f"Unknown function name: {function_name}")

    target_function = BENCHMARKS[function_name]["function"]

    return target_function(*chromosome)


def validate_branch(function_name, chromosome, target):
    """
    Return True if chromosome reaches the intended target branch.
    """

    reached_branch = get_reached_branch(function_name, chromosome)

    return reached_branch == target