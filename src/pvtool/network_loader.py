"""
Contains validation logic for TripicaNetworkLoaderDataSet
"""
import re
from typing import Iterator

from bo4e.com.zaehlwerk import Zaehlwerk
from bo4e.enum.kundentyp import Kundentyp
from bo4e.enum.rollencodetyp import Rollencodetyp
from bo4e.enum.sparte import Sparte
from bo4e.enum.tarifart import Tarifart
from bo4e.enum.zaehlerauspraegung import Zaehlerauspraegung
from ibims.datasets import TripicaNetworkLoaderDataSet
from injector import Module, provider
from pvframework import PathMappedValidator, Query, QueryMappedValidator, ValidationManager, Validator
from pvframework.utils import param

from .customer_loader import (
    ValidatorType,
    validate_address_deutsch,
    validate_address_fields,
    validate_geschaeftspartner_name3,
    validate_postleitzahl,
    validate_str_is_stripped,
)
from .resource_loader import validate_malo_id, validate_sparte


def check_netzbetreiber_code_nr(netzbetreiber_code_nr: str) -> None:
    """
    Netzbetreiber-Code-Nr is required and has to consist of 13 digits
    """
    if not re.match(r"^\d{13}$", netzbetreiber_code_nr):
        raise ValueError(f"{param('netzbetreiber_code_nr').param_id} has to consist of 13 digits.")


def check_kundentyp(kundentyp: list[Kundentyp]) -> None:
    """kundentyp must have exactly one element"""
    if not len(kundentyp) == 1:
        raise ValueError(f"{param('kundentyp').param_id} must have exactly one element")


# pylint: disable=unused-argument
def check_rollencodetyp(rollencodetyp: Rollencodetyp) -> None:
    """rollencodetyp is required'"""


def check_rollencodenr(rollencodenr: str) -> None:
    """rollencodenr is required. The last digit must fulfill the 'Lok- und Waggon-Kennzeichnungsverfahren'."""
    if not re.match(r"^\d{13}$", rollencodenr):
        raise ValueError(f"{param('rollencodenr').param_id} has to consist of 13 digits")
    rollencodenr_digits = [int(x) for x in rollencodenr]
    checksum = 10 - (sum(rollencodenr_digits[0::2]) + 2 * sum(rollencodenr_digits[1::2])) % 10
    if not int(rollencodenr[-1]) == checksum:
        raise ValueError(f"{param('rollencodenr').param_id} checksum digit is incorrect")


# pylint: disable=unused-argument
def check_zaehlernummer(zaehlernummer: str) -> None:
    """zaehlernummer is required"""


def check_zaehlerauspraegung(zaehlerauspraegung: Zaehlerauspraegung) -> None:
    """zaehlerauspraegung must be EINRICHTUNGSZAEHLER"""
    if not zaehlerauspraegung == Zaehlerauspraegung.EINRICHTUNGSZAEHLER:
        raise ValueError(f"{param('zaehlerauspraegung').param_id} must be EINRICHTUNGSZAEHLER")


def check_tarifart(tarifart: Tarifart) -> None:
    """tarifart must be EINTARIF, ZWEITARIF or MEHRTARIF"""
    if tarifart not in (Tarifart.EINTARIF, Tarifart.ZWEITARIF, Tarifart.MEHRTARIF):
        raise ValueError(f"{param('tarifart').param_id} must be EINTARIF, ZWEITARIF or MEHRTARIF")


OBIS_PATTERN = re.compile(
    r"((1)-((?:[0-5]?[0-9])|(?:6[0-5])):((?:[1-8]|99))\."
    r"((?:6|8|9|29))\."
    r"([0-9]{1,2})|(7)-((?:[0-5]?[0-9])|(?:6[0-5])):(.{1,2})\."
    r"(.{1,2})\."
    r"([0-9]{1,2}))"
)


def check_obis(obis: str, sparte: Sparte) -> None:
    r"""
    obis is required. It must match the pattern ^[17]-\d+:\d+\.\d+\.\d+$.
    For Sparte.STROM it must start with '1', for Sparte.GAS it must start with '7'.
    """
    if not re.match(OBIS_PATTERN, obis):
        raise ValueError(f"{param('obis').param_id} does not match the regex pattern")
    if sparte == Sparte.STROM and not obis.startswith("1"):
        raise ValueError(f"{param('obis').param_id} must start with '1' for Sparte.STROM")
    if sparte == Sparte.GAS and not obis.startswith("7"):
        raise ValueError(f"{param('obis').param_id} must start with '7' for Sparte.GAS")


def check_is_digit(string: str) -> None:
    """string is required and must be a number"""
    if not string.isdigit():
        raise ValueError(f"{param('nachkommastellen').param_id} has to be a number")


validate_netzbetreiber_code_nr: ValidatorType = Validator(check_netzbetreiber_code_nr)
validate_kundentyp: ValidatorType = Validator(check_kundentyp)
validate_rollencodetyp: ValidatorType = Validator(check_rollencodetyp)
validate_rollencodenr: ValidatorType = Validator(check_rollencodenr)
validate_zaehlernummer: ValidatorType = Validator(check_zaehlernummer)
validate_zaehlerauspraegung: ValidatorType = Validator(check_zaehlerauspraegung)
validate_tarifart: ValidatorType = Validator(check_tarifart)
validate_obis: ValidatorType = Validator(check_obis)
validate_is_digit: ValidatorType = Validator(check_is_digit)


def iter_zaehlwerke(zaehlwerke: list[Zaehlwerk]) -> Iterator[tuple[Zaehlwerk, str]]:
    """
    This function is used to iterate over a list of Zaehlwerke. The values of the list are returned
    and the index is used for tracking for proper `ValidationError`s.
    """
    return ((zaehlwerk, f"[{index}]") for index, zaehlwerk in enumerate(zaehlwerke))


class ValidationManagerProviderNetwork(Module):
    """
    This module provides a ValidationManager for network loader
    """

    @provider
    def network_validation_manager(self) -> ValidationManager:
        """
        This method provides a ValidationManager for network loader
        """
        network_manager = ValidationManager[TripicaNetworkLoaderDataSet]()
        network_manager.register(PathMappedValidator(validate_str_is_stripped, {"string": "kunde.name1"}))
        network_manager.register(PathMappedValidator(validate_str_is_stripped, {"string": "kunde.name2"}))
        network_manager.register(PathMappedValidator(validate_geschaeftspartner_name3, {"name3": "kunde.name3"}))
        network_manager.register(PathMappedValidator(validate_address_fields, {"address": "kunde.partneradresse"}))
        network_manager.register(
            PathMappedValidator(validate_postleitzahl, {"postleitzahl": "kunde.partneradresse.postleitzahl"})
        )
        network_manager.register(PathMappedValidator(validate_address_fields, {"address": "liefer_adresse"}))
        network_manager.register(PathMappedValidator(validate_address_deutsch, {"address": "liefer_adresse"}))
        network_manager.register(
            PathMappedValidator(
                validate_address_fields, {"address": "geschaeftspartner_mit_rechnungs_adresse.partneradresse"}
            )
        )
        network_manager.register(
            PathMappedValidator(
                validate_postleitzahl,
                {"postleitzahl": "geschaeftspartner_mit_rechnungs_adresse.partneradresse.postleitzahl"},
            )
        )
        network_manager.register(
            PathMappedValidator(validate_malo_id, {"marktlokations_id": "marktlokation.marktlokations_id"})
        )
        network_manager.register(PathMappedValidator(validate_sparte, {"sparte": "marktlokation.sparte"}))
        network_manager.register(
            PathMappedValidator(
                validate_netzbetreiber_code_nr, {"netzbetreiber_code_nr": "marktlokation.netzbetreibercodenr"}
            )
        )
        network_manager.register(PathMappedValidator(validate_kundentyp, {"kundentyp": "marktlokation.kundengruppen"}))
        network_manager.register(
            PathMappedValidator(
                validate_rollencodetyp,
                {"rollencodetyp": "netzbetreiber.rollencodetyp"},
                {"rollencodetyp": "messstellenbetreiber.rollencodetyp"},
            )
        )
        network_manager.register(
            PathMappedValidator(
                validate_str_is_stripped,
                {"string": "netzbetreiber.name1"},
                {"string": "messstellenbetreiber.name1"},
            )
        )
        network_manager.register(
            PathMappedValidator(
                validate_rollencodenr,
                {"rollencodenr": "netzbetreiber.rollencodenummer"},
                {"rollencodenr": "messstellenbetreiber.rollencodenummer"},
            )
        )
        network_manager.register(
            PathMappedValidator(validate_zaehlernummer, {"zaehlernummer": "zaehler.zaehlernummer"})
        )
        network_manager.register(
            PathMappedValidator(validate_zaehlerauspraegung, {"zaehlerauspraegung": "zaehler.zaehlerauspraegung"})
        )
        network_manager.register(PathMappedValidator(validate_tarifart, {"tarifart": "zaehler.tarifart"}))
        network_manager.register(
            QueryMappedValidator(
                validate_obis,
                {
                    "obis": Query().path("zaehler.zaehlwerke").iter(iter_zaehlwerke).path("obis"),
                    "sparte": Query().path("zaehler.sparte"),
                },
            )
        )
        network_manager.register(
            QueryMappedValidator(
                validate_is_digit,
                {
                    "string": Query().path("zaehler.zaehlwerke").iter(iter_zaehlwerke).path("nachkommastellen"),
                },
            )
        )
        network_manager.register(
            QueryMappedValidator(
                validate_is_digit,
                {
                    "string": Query().path("zaehler.zaehlwerke").iter(iter_zaehlwerke).path("vorkommastellen"),
                },
            )
        )
        return network_manager
