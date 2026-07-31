# benchmark_registry.py

"""
Benchmark registry for the zero-shot LLM branch coverage project.

This file is used after LLM generation for:
1. offline validation,
2. input generation,
3. GA search,
4. result analysis,
5. pytest generation.

In the zero-shot prompting setting, we do NOT use this registry to give
detailed branch-distance rules to the LLM.
"""

from target_functions import (
    sign_type,
    number_kind,
    max_of_three,
    triangle_type,
    is_leap_year,
    grade_category,
    bmi_category,
    loan_eligibility,
    password_strength,
    string_category,
    list_score,
    list_pattern,
)


BENCHMARKS = {
    "sign_type": {
        "function": sign_type,
        "args": ["x"],
        "input_schema": [
            {"type": "int", "min": -100, "max": 100},
        ],
        "targets": ["positive", "negative", "zero"],
        "known_valid_inputs": {
            "positive": [5],
            "negative": [-3],
            "zero": [0],
        },
    },

    "number_kind": {
        "function": number_kind,
        "args": ["x"],
        "input_schema": [
            {"type": "int", "min": -100, "max": 100},
        ],
        "targets": ["zero", "even", "odd"],
        "known_valid_inputs": {
            "zero": [0],
            "even": [8],
            "odd": [7],
        },
    },

    "max_of_three": {
        "function": max_of_three,
        "args": ["a", "b", "c"],
        "input_schema": [
            {"type": "int", "min": -100, "max": 100},
            {"type": "int", "min": -100, "max": 100},
            {"type": "int", "min": -100, "max": 100},
        ],
        "targets": ["a_is_max", "b_is_max", "c_is_max"],
        "known_valid_inputs": {
            "a_is_max": [9, 3, 2],
            "b_is_max": [1, 7, 3],
            "c_is_max": [1, 2, 8],
        },
    },

    "triangle_type": {
        "function": triangle_type,
        "args": ["a", "b", "c"],
        "input_schema": [
            {"type": "int", "min": -20, "max": 100},
            {"type": "int", "min": -20, "max": 100},
            {"type": "int", "min": -20, "max": 100},
        ],
        "targets": [
            "invalid_side",
            "not_triangle",
            "equilateral",
            "isosceles",
            "scalene",
        ],
        "known_valid_inputs": {
            "invalid_side": [-1, 3, 4],
            "not_triangle": [1, 2, 10],
            "equilateral": [5, 5, 5],
            "isosceles": [5, 5, 3],
            "scalene": [3, 4, 5],
        },
    },

    "is_leap_year": {
        "function": is_leap_year,
        "args": ["year"],
        "input_schema": [
            {"type": "int", "min": 0, "max": 3000},
        ],
        "targets": [
            "divisible_by_400",
            "divisible_by_100_not_400",
            "divisible_by_4_not_100",
            "not_leap_year",
        ],
        "known_valid_inputs": {
            "divisible_by_400": [2000],
            "divisible_by_100_not_400": [1900],
            "divisible_by_4_not_100": [2024],
            "not_leap_year": [2023],
        },
    },

    "grade_category": {
        "function": grade_category,
        "args": ["score"],
        "input_schema": [
            {"type": "int", "min": -20, "max": 120},
        ],
        "targets": ["invalid", "A", "B", "C", "D", "F"],
        "known_valid_inputs": {
            "invalid": [-5],
            "A": [95],
            "B": [85],
            "C": [75],
            "D": [65],
            "F": [50],
        },
    },

    "bmi_category": {
        "function": bmi_category,
        "args": ["weight", "height"],
        "input_schema": [
            {"type": "float", "min": 30.0, "max": 150.0},
            {"type": "float", "min": 0.0, "max": 2.5},
        ],
        "targets": [
            "invalid_height",
            "underweight",
            "normal",
            "overweight",
            "obese",
        ],
        "known_valid_inputs": {
            "invalid_height": [70.0, 0.0],
            "underweight": [40.0, 1.75],
            "normal": [70.0, 1.75],
            "overweight": [85.0, 1.75],
            "obese": [110.0, 1.75],
        },
    },

    "loan_eligibility": {
        "function": loan_eligibility,
        "args": ["age", "income", "employed"],
        "input_schema": [
            {"type": "int", "min": 0, "max": 100},
            {"type": "int", "min": 0, "max": 100000},
            {"type": "bool"},
        ],
        "targets": [
            "reject_underage",
            "approve",
            "review",
            "reject_low_income",
        ],
        "known_valid_inputs": {
            "reject_underage": [16, 10000, False],
            "approve": [25, 60000, True],
            "review": [25, 40000, False],
            "reject_low_income": [25, 10000, False],
        },
    },

    "password_strength": {
        "function": password_strength,
        "args": ["s"],
        "input_schema": [
            {"type": "str", "min_len": 0, "max_len": 15},
        ],
        "targets": [
            "weak_short",
            "strong",
            "medium",
            "weak_no_digit_upper",
        ],
        "known_valid_inputs": {
            "weak_short": ["abc"],
            "strong": ["Abcdef1234"],
            "medium": ["abc123"],
            "weak_no_digit_upper": ["abcdef"],
        },
    },

    "string_category": {
        "function": string_category,
        "args": ["s"],
        "input_schema": [
            {"type": "str", "min_len": 0, "max_len": 12},
        ],
        "targets": [
            "empty",
            "long_palindrome",
            "short_palindrome",
            "long_non_palindrome",
            "other",
        ],
        "known_valid_inputs": {
            "empty": [""],
            "long_palindrome": ["racecar"],
            "short_palindrome": ["aba"],
            "long_non_palindrome": ["abcdef"],
            "other": ["abc"],
        },
    },

    "list_score": {
        "function": list_score,
        "args": ["nums"],
        "input_schema": [
            {"type": "list_int", "min_len": 0, "max_len": 6, "min": -20, "max": 20},
        ],
        "targets": ["empty", "high", "medium", "low"],
        "known_valid_inputs": {
            "empty": [[]],
            "high": [[20, 15]],
            "medium": [[1, 2, 3]],
            "low": [[-5, -2]],
        },
    },

    "list_pattern": {
        "function": list_pattern,
        "args": ["nums"],
        "input_schema": [
            {"type": "list_int", "min_len": 0, "max_len": 6, "min": -10, "max": 10},
        ],
        "targets": [
            "too_short",
            "sorted_with_duplicates",
            "sorted_unique",
            "unsorted_with_duplicates",
            "unsorted_unique",
        ],
        "known_valid_inputs": {
            "too_short": [[1]],
            "sorted_with_duplicates": [[1, 2, 2]],
            "sorted_unique": [[1, 2, 3]],
            "unsorted_with_duplicates": [[3, 1, 1]],
            "unsorted_unique": [[3, 1, 2]],
        },
    },
}