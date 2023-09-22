"""
Contains validation logic for TripicaResourceLoaderDataSet
"""
import re

from bo4e.enum.sparte import Sparte
from ibims.datasets import TripicaResourceLoaderDataSet
from injector import Module, provider
from pvframework import PathMappedValidator, ValidationManager, Validator
from pvframework.utils import param

from .customer_loader import ValidatorType


def check_melo_id(messlokations_id: str) -> None:
    """
    Messlokations-ID is required and has to start with 'DE' followed by 11 digits and further 20 alphanumeric
    characters.
    See https://wiki.hochfrequenz.de/index.php/Markt-_und_Messlokation#Aufbau_der_Messlokation
    """
    if not re.match(r"^DE\d{11}[A-Z\d]{20}$", messlokations_id):
        raise ValueError(
            f"{param('messlokations_id').param_id} has to start with 'DE' followed by 11 "
            "digits and 20 alphanumeric characters."
        )


def check_malo_id(marktlokations_id: str) -> None:
    """
    Marktlokations-ID is required and has to consist of 11 digits
    """
    if not re.match(r"^\d{11}$", marktlokations_id):
        raise ValueError(f"{param('marktlokations_id').param_id} has to consist of 11 digits.")


def check_sparte(sparte: Sparte) -> None:
    """
    Sparte is required and has to be either `STROM` or `GAS`.
    Eventually `Sparte.STROM_UND_GAS` should also be possible but is invalid here at the moment.
    """
    if sparte not in (Sparte.STROM, Sparte.GAS):
        raise ValueError(f"{param('sparte').param_id} must be one of the following: 'STROM', 'GAS'")


def check_zaehlernummer(zaehlernummer: str) -> None:
    """
    Zählernummer is required and must not start with space.
    """
    if zaehlernummer.startswith(" "):
        raise ValueError(f"{param('zaehlernummer').param_id} must not start with whitespace")


validate_melo_id: ValidatorType = Validator(check_melo_id)
validate_malo_id: ValidatorType = Validator(check_malo_id)
validate_sparte: ValidatorType = Validator(check_sparte)
validate_zaehlernummer: ValidatorType = Validator(check_zaehlernummer)


class ValidationManagerProviderResource(Module):
    """
    This module provides a ValidationManager for network loader
    """

    @provider
    def resource_validation_manager(self) -> ValidationManager:
        """
        This method provides a ValidationManager for resource loader
        """
        resource_manager = ValidationManager[TripicaResourceLoaderDataSet]()
        resource_manager.register(
            PathMappedValidator(validate_melo_id, {"messlokations_id": "messlokation.messlokations_id"})
        )
        resource_manager.register(
            PathMappedValidator(validate_malo_id, {"marktlokations_id": "marktlokation.marktlokations_id"})
        )
        resource_manager.register(
            PathMappedValidator(validate_zaehlernummer, {"zaehlernummer": "zaehler.zaehlernummer"})
        )
        resource_manager.register(PathMappedValidator(validate_sparte, {"sparte": "vertrag.sparte"}))
        return resource_manager
