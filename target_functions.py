# target_functions.py

"""
Target benchmark programs for zero-shot LLM-based fitness-function generation.

These 12 functions include different input types and condition types:
- int
- float
- bool
- str
- list[int]

Each function returns a branch label so that offline validation is easier.
"""


def sign_type(x):
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"


def number_kind(x):
    if x == 0:
        return "zero"
    elif x % 2 == 0:
        return "even"
    else:
        return "odd"


# def max_of_three(a, b, c):
#     if a >= b and a >= c:
#         return "a_is_max"
#     elif b >= a and b >= c:
#         return "b_is_max"
#     else:
#         return "c_is_max"


def triangle_type(a, b, c):
    if a <= 0 or b <= 0 or c <= 0:
        return "invalid_side"

    if a + b <= c or a + c <= b or b + c <= a:
        return "not_triangle"

    if a == b and b == c:
        return "equilateral"
    elif a == b or a == c or b == c:
        return "isosceles"
    else:
        return "scalene"


# def is_leap_year(year):
#     if year % 400 == 0:
#         return "divisible_by_400"
#     elif year % 100 == 0:
#         return "divisible_by_100_not_400"
#     elif year % 4 == 0:
#         return "divisible_by_4_not_100"
#     else:
#         return "not_leap_year"


# def grade_category(score):
#     if score < 0 or score > 100:
#         return "invalid"
#     elif score >= 90:
#         return "A"
#     elif score >= 80:
#         return "B"
#     elif score >= 70:
#         return "C"
#     elif score >= 60:
#         return "D"
#     else:
#         return "F"


def bmi_category(weight, height):
    if height <= 0:
        return "invalid_height"

    bmi = weight / (height * height)

    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"


# def loan_eligibility(age, income, employed):
#     if age < 18:
#         return "reject_underage"

#     if income >= 50000 and employed:
#         return "approve"
#     elif income >= 30000:
#         return "review"
#     else:
#         return "reject_low_income"


def password_strength(s):
    if len(s) < 6:
        return "weak_short"

    has_digit = any(ch.isdigit() for ch in s)
    has_upper = any(ch.isupper() for ch in s)

    if len(s) >= 10 and has_digit and has_upper:
        return "strong"
    elif has_digit or has_upper:
        return "medium"
    else:
        return "weak_no_digit_upper"


def string_category(s):
    if len(s) == 0:
        return "empty"
    elif s == s[::-1] and len(s) > 3:
        return "long_palindrome"
    elif s == s[::-1]:
        return "short_palindrome"
    elif len(s) > 5:
        return "long_non_palindrome"
    else:
        return "other"


# def list_score(nums):
#     if len(nums) == 0:
#         return "empty"

#     total = sum(nums)
#     avg = total / len(nums)

#     if avg > 10:
#         return "high"
#     elif avg >= 0:
#         return "medium"
#     else:
#         return "low"


def list_pattern(nums):
    if len(nums) < 2:
        return "too_short"

    if nums == sorted(nums):
        if len(nums) != len(set(nums)):
            return "sorted_with_duplicates"
        return "sorted_unique"
    else:
        if len(nums) != len(set(nums)):
            return "unsorted_with_duplicates"
        return "unsorted_unique"



#complex functions
def shipping_discount(order_total, distance, is_member):
    if order_total < 0 or distance < 0:
        return "invalid"

    if order_total >= 200 and distance <= 50 and is_member:
        return "free_express_shipping"

    if order_total >= 100 and distance <= 100:
        return "standard_discount"

    if order_total >= 50 or is_member:
        return "small_discount"

    return "no_discount"


def username_category(username):
    if len(username) == 0:
        return "empty"

    if len(username) < 5:
        return "too_short"

    has_digit = any(ch.isdigit() for ch in username)
    has_upper = any(ch.isupper() for ch in username)
    has_special = any(not ch.isalnum() for ch in username)

    if username[0].isdigit():
        return "starts_with_digit"

    if len(username) >= 10 and has_digit and has_upper and has_special:
        return "strong_username"

    if has_digit and has_upper:
        return "medium_username"

    return "weak_username"


def transaction_pattern(amounts):
    if len(amounts) == 0:
        return "empty"

    if any(x == 0 for x in amounts):
        return "contains_zero"

    positives = sum(1 for x in amounts if x > 0)
    negatives = sum(1 for x in amounts if x < 0)
    total = sum(amounts)

    if positives >= 3 and negatives == 0 and total > 100:
        return "many_large_deposits"

    if negatives >= 2 and total < -50:
        return "many_large_withdrawals"

    if positives > 0 and negatives > 0:
        return "mixed_transactions"

    return "simple_pattern"

def pin_pattern(a, b, c, d):
    if a == 7 and b == 3 and c == 9 and d == 1:
        return "secret_pin"
    elif a == b == c == d:
        return "all_same"
    elif a + b + c + d == 20 and a < b < c < d:
        return "ordered_sum_20"
    else:
        return "other"


if __name__ == "__main__":  # pragma: no cover
    print("sign_type:", sign_type(5), sign_type(-3), sign_type(0))
    print("number_kind:", number_kind(0), number_kind(8), number_kind(7))
    #print("max_of_three:", max_of_three(9, 3, 2), max_of_three(1, 7, 3), max_of_three(1, 2, 8))

    print(
        "triangle_type:",
        triangle_type(-1, 3, 4),
        triangle_type(1, 2, 10),
        triangle_type(5, 5, 5),
        triangle_type(5, 5, 3),
        triangle_type(3, 4, 5),
    )

    # print(
    #     "is_leap_year:",
    #     is_leap_year(2000),
    #     is_leap_year(1900),
    #     is_leap_year(2024),
    #     is_leap_year(2023),
    # )

    # print(
    #     "grade_category:",
    #     grade_category(-5),
    #     grade_category(95),
    #     grade_category(85),
    #     grade_category(75),
    #     grade_category(65),
    #     grade_category(50),
    # )

    print(
        "bmi_category:",
        bmi_category(70, 1.75),
        bmi_category(40, 1.75),
        bmi_category(90, 1.75),
        bmi_category(110, 1.75),
        bmi_category(70, 0),
    )

    # print(
    #     "loan_eligibility:",
    #     loan_eligibility(16, 10000, False),
    #     loan_eligibility(25, 60000, True),
    #     loan_eligibility(25, 40000, False),
    #     loan_eligibility(25, 10000, False),
    # )

    print(
        "password_strength:",
        password_strength("abc"),
        password_strength("abcdef"),
        password_strength("abc123"),
        password_strength("Abcdef1234"),
    )

    print(
        "string_category:",
        string_category(""),
        string_category("racecar"),
        string_category("aba"),
        string_category("abcdef"),
        string_category("abc"),
    )

    # print(
    #     "list_score:",
    #     list_score([]),
    #     list_score([20, 15]),
    #     list_score([1, 2, 3]),
    #     list_score([-5, -2]),
    # )

    print(
        "list_pattern:",
        list_pattern([1]),
        list_pattern([1, 2, 3]),
        list_pattern([1, 2, 2]),
        list_pattern([3, 1, 2]),
        list_pattern([3, 1, 1]),
    )

    print(
        "shipping_discount:",
        shipping_discount(-1, 10, True),
        shipping_discount(250, 20, True),
        shipping_discount(120, 80, False),
        shipping_discount(60, 200, False),
        shipping_discount(20, 200, False),
    )

    print(
        "username_category:",
        username_category(""),
        username_category("abc"),
        username_category("1abcde"),
        username_category("User123!xx"),
        username_category("User123"),
        username_category("abcdef"),
    )

    print(
        "transaction_pattern:",
        transaction_pattern([]),
        transaction_pattern([0, 5, 10]),
        transaction_pattern([50, 40, 30]),
        transaction_pattern([-30, -40, 5]),
        transaction_pattern([10, -5, 20]),
        transaction_pattern([5, 10]),
    )
    print(
        "pin_pattern:",
        pin_pattern(7, 3, 9, 1),      # secret_pin
        pin_pattern(5, 5, 5, 5),      # all_same
        pin_pattern(2, 4, 6, 8),      # ordered_sum_20
        pin_pattern(1, 2, 3, 4),      # other
    )