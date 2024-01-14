from typing import TypeVar

from pvframework.errors import ValidationError

SubT = TypeVar("SubT")
BaseT = TypeVar("BaseT")


def intersection_with_contains_str(
    set_sub_container: set[SubT], set_base_container: set[BaseT]
) -> tuple[set[SubT], set[BaseT]]:
    """
    Calculates all elements from both sets "intersecting" in the following manner:
    Let's call `set_sub_container` A and `set_base_container` B.
    A consists of elements a1, a2, a3, ...
    B consists of elements b1, b2, b3, ...

    It returns a tuple two sets:
    The first set contains all elements from A that are contained in at least one element of B.
    I.e. {a_i ∈ A | ∃ b_j ∈ B : a_i ⊆ b_j}
    LaTeX-Code: \left\{a_i \in A | \exists_{b_j \in B}: a_i \subseteq b_j\right\}
    The second set contains all elements from B that have at least one element of A being a substring of the element
    from B.
    I.e. {b_j ∈ B | ∃ a_i ∈ A : b_j ⊇ a_i}
    LaTeX-Code: \left\{b_j \in B | \exists_{a_i \in A}: b_j \supseteq a_i\right\}
    """
    set_sub_container_intersection = set()
    set_base_container_intersection = set()
    for item_base in set_base_container:
        for item_sub in set_sub_container:
            if str(item_sub) in str(item_base):
                set_sub_container_intersection.add(item_sub)
                set_base_container_intersection.add(item_base)
                break

    return set_sub_container_intersection, set_base_container_intersection


def assert_full_error_coverage(expected_errors: set[str], all_errors: set[ValidationError]):
    """
    Asserts that all expected errors are found in the actual errors and vice versa.
    The error messages in `expected_errors` don't have to be exact matches.
    Every actual error message must have at least one element in `expected_errors` being
    a substring of the actual error message.
    """
    expected_errors_found, actual_errors_in_expected_list = intersection_with_contains_str(expected_errors, all_errors)
    if len(expected_errors) != len(expected_errors_found) or len(all_errors) != len(actual_errors_in_expected_list):
        expected_errors_not_found = expected_errors - expected_errors_found
        uncovered_actual_errors = all_errors - actual_errors_in_expected_list
        raise AssertionError(
            f"Expected errors not found: {expected_errors_not_found}\n"
            f"Actual errors not covered from expected list: {uncovered_actual_errors}"
        )
