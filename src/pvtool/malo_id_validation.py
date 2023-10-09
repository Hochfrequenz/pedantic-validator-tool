"""
validators that were included in the bo4e package prior to version 0.6.0
"""
import re

from pydantic_core.core_schema import ValidationInfo


def _get_malo_id_checksum(malo_id: str) -> str:
    """
    Get the checksum of a marktlokations id.
    a) Quersumme aller Ziffern in ungerader Position
    b) Quersumme aller Ziffern auf gerader Position multipliziert mit 2
    c) Summe von a) und b) d) Differenz von c) zum nächsten Vielfachen von 10 (ergibt sich hier 10, wird die
       Prüfziffer 0 genommen
    https://bdew-codes.de/Content/Files/MaLo/2017-04-28-BDEW-Anwendungshilfe-MaLo-ID_Version1.0_FINAL.PDF
    :return: the checksum as string
    """
    odd_checksum: int = 0
    even_checksum: int = 0
    # start counting at 1 to be consistent with the above description
    # of "even" and "odd" but stop at tenth digit.
    for i in range(1, 11):
        digit = malo_id[i - 1 : i]
        if i % 2 - 1 == 0:
            odd_checksum += int(digit)
        else:
            even_checksum += 2 * int(digit)
    result: int = (10 - ((even_checksum + odd_checksum) % 10)) % 10
    return str(result)


_malo_id_pattern = re.compile(r"^[1-9]\d{10}$")


# pylint:disable=unused-argument
def validate_marktlokations_id(  # type: ignore[no-untyped-def]
    cls, marktlokations_id: str, values: ValidationInfo
) -> str:
    """
    A validator for marktlokations IDs
    """
    if not marktlokations_id:
        raise ValueError("The marktlokations_id must not be empty.")
    if not _malo_id_pattern.match(marktlokations_id):
        raise ValueError(f"The Marktlokations-ID '{marktlokations_id}' does not match {_malo_id_pattern.pattern}")
    expected_checksum = _get_malo_id_checksum(marktlokations_id)
    actual_checksum = marktlokations_id[10:11]
    if expected_checksum != actual_checksum:
        # pylint: disable=line-too-long
        raise ValueError(
            f"The Marktlokations-ID '{marktlokations_id}' has checksum '{actual_checksum}' but '{expected_checksum}' was expected."
        )
    return marktlokations_id
