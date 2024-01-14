from collections.abc import Sequence
from typing import Iterable, TypeVar

from pvframework.errors import ValidationError

SubT = TypeVar("SubT")
BaseT = TypeVar("BaseT")


def intersection_with_contains_str(
    set_sub_container: Iterable[SubT], set_base_container: Iterable[BaseT]
) -> tuple[list[SubT], list[BaseT]]:
    """
    Returns the intersection of two sets, but only if the intersection is not empty.
    :param set_sub_container: the set to be checked for intersection
    :param set_base_container: the set to be checked for intersection
    :return: the intersection of the two sets, if the intersection is not empty
    """
    set_sub_container = list(set_sub_container)
    set_base_container = list(set_base_container)
    set_sub_container_intersection = []
    set_base_container_intersection = []
    for item_sub in set_sub_container:
        set_base_remove_list = []
        for item_base in set_base_container:
            if str(item_sub) in str(item_base):
                set_sub_container_intersection.append(item_sub)
                set_base_container_intersection.append(item_base)
                set_base_remove_list.append(item_base)
                break
        for item_base in set_base_remove_list:
            set_base_container.remove(item_base)

    return set_sub_container_intersection, set_base_container_intersection


def assert_full_error_coverage(expected_errors: Sequence[str], all_errors: Sequence[ValidationError]):
    expected_errors_found, actual_errors_from_expected_list = intersection_with_contains_str(
        expected_errors, all_errors
    )
    if len(expected_errors) != len(expected_errors_found) or len(all_errors) != len(actual_errors_from_expected_list):
        expected_errors_not_found = list(set(expected_errors) - set(expected_errors_found))
        uncovered_actual_errors = list(set(all_errors) - set(actual_errors_from_expected_list))
        raise AssertionError(
            f"Expected errors not found: {expected_errors_not_found}\n"
            f"Actual errors not covered from expected list: {uncovered_actual_errors}"
        )
