"""
Contains validation logic for TripicaCustomerLoaderDataSet
"""
import re
from datetime import date, datetime
from typing import Any, Generator, Iterator, Optional, TypeAlias

from bo4e.com.adresse import Adresse
from bo4e.com.externereferenz import ExterneReferenz
from bo4e.enum.anrede import Anrede
from bo4e.enum.landescode import Landescode
from bomf.config import MigrationConfig
from dateutil.relativedelta import relativedelta
from email_validator import validate_email
from ibims.com import Vertragskonto
from ibims.datasets import TripicaCustomerLoaderDataSet
from injector import Module, provider
from more_itertools import first_true
from pvframework import PathMappedValidator, Query, QueryMappedValidator, ValidationManager, Validator
from pvframework.mapped_validators.query_map import QueryIterable
from pvframework.types import DataSetT, SyncValidatorFunction, ValidatorFunctionT
from pvframework.utils import param, required_field
from pytz import timezone
from schwifty import BIC, IBAN

from .utils import migration_config
from .validation_manager import ValidationManagerWithConfig

_berlin = timezone("Europe/Berlin")


def get_externe_referenz(ex_ref_name: str, externe_referenzen: list[ExterneReferenz]) -> Optional[str]:
    """
    Extracts a value from a list of `ExterneReferenz`. Returns None if there doesn't exist an `ExterneReferenz` of
    name `ex_ref_name`.
    """
    externe_referenz = first_true(
        externe_referenzen, default=None, pred=lambda ex_ref: ex_ref.ex_ref_name == ex_ref_name
    )
    return externe_referenz.ex_ref_wert if externe_referenz is not None else None


def check_geschaeftspartner_anrede(anrede: Anrede):
    """
    geschaeftspartner_erw.anrede must be one of the following: HERR, FRAU, FIRMA, EHELEUTE
    """
    valid_values_strings = {Anrede.HERR, Anrede.FRAU, Anrede.FIRMA, Anrede.EHELEUTE}
    if anrede not in valid_values_strings:
        raise ValueError(
            f"{param('anrede').param_id} must be one of the following: " f"{', '.join(valid_values_strings)}"
        )


def check_str_is_stripped(string: str):
    """
    geschaeftspartner_erw.name1 must not start with whitespace. Further validation is difficult because e.g.
    there exist names with characters like '.
    And if the name is a company it could even contain digits or other characters e.g. 'edi@energy'.
    """
    if string.strip() != string:
        raise ValueError(f"{param('string').param_id} must not start or end with whitespace.")


def check_geschaeftspartner_name3(name3: Optional[str] = None):
    """
    geschaeftspartner_erw.name2 must not start with whitespace. Further validation is difficult because e.g.
    there exist names with characters like '.
    And if the name is a company it could even contain digits or other characters e.g. 'edi@energy'.
    """
    allowed_values = {"Dr.", "Prof.", "Prof. Dr."}
    if name3 and name3 not in allowed_values:
        raise ValueError(f"{param('name3').param_id} must be one of the following: " f"{', '.join(allowed_values)}")


def check_e_mail(e_mail: Optional[str] = None):
    """
    geschaeftspartner_erw.e_mail_adresse must match the regex pattern `REGEX_E_MAIL`.
    """
    if not e_mail:
        return
    validate_email(e_mail, check_deliverability=False)


def check_extern_customer_id(externe_referenzen: list[ExterneReferenz]):
    """
    geschaeftspartner_erw.externe_referenzen -> customerID has to start with 2 followed by 8 digits.
    """
    customer_id = get_externe_referenz("customerID", externe_referenzen)
    if customer_id is None:
        raise ValueError("No ExterneReferenz with name customerID")
    if re.match(r"^2\d{8}$", customer_id) is None:
        raise ValueError(
            f"{param('externe_referenzen').param_id} -> customerID has to start with 2 followed by 8 digits."
        )


def check_date_in_past_required(past_date: datetime):
    """
    The date is required and must be in the past as of the migration_key_date
    """
    config = migration_config()
    if past_date.astimezone(_berlin).date() > config.migration_key_date.astimezone(_berlin).date():
        raise ValueError(
            f"{param('past_date').param_id} must be in the past as of " + str(config.migration_key_date.isoformat())
        )


def check_date_in_future_required(future_date: datetime):
    """
    The date is required and must be in the future as of the migration_key_date
    """
    config = migration_config()
    if future_date < config.migration_key_date:
        raise ValueError(
            f"{param('future_date').param_id} must be in the future as of " + str(config.migration_key_date.isoformat())
        )


def check_date_in_past_optional(past_date: Optional[datetime] = None):
    """
    The date is optional and must be in the past as of the migration_key_date
    """
    config = migration_config()
    if (
        past_date is not None
        and past_date.astimezone(_berlin).date() > config.migration_key_date.astimezone(_berlin).date()
    ):
        raise ValueError(
            f"{param('past_date').param_id} must be in the past as of " + str(config.migration_key_date.isoformat())
        )


def check_date_in_future_optional(future_date: Optional[datetime] = None):
    """
    The date is optional and must be in the future as of the migration_key_date
    """
    config = migration_config()
    if future_date is not None and future_date < config.migration_key_date:
        raise ValueError(
            f"{param('future_date').param_id} must be in the future as of " + str(config.migration_key_date.isoformat())
        )


def check_date_in_past_bankverbindung(is_sepa_zahler: bool, past_date: Optional[datetime] = None):
    """
    The date is required if customer is sepa_zahler, and must be in the past as of the migration_key_date
    """
    config = migration_config()
    if is_sepa_zahler:
        if past_date is None:
            raise ValueError(f"{param('past_date').param_id} is required for sepa_zahler")
        if past_date.astimezone(_berlin).date() > config.migration_key_date.astimezone(_berlin).date():
            raise ValueError(
                f"{param('past_date').param_id} must be in the past as of " + str(config.migration_key_date.isoformat())
            )


def check_geschaeftspartner_geburtsdatum(geburtsdatum: datetime):
    """
    geschaeftspartner_erw.geburtsdatum must be at least 18 years ago in the past but not earlier than 1900-01-01.
    """
    config = migration_config()
    birthday_date = geburtsdatum.astimezone(_berlin).date()
    latest_18 = config.migration_key_date.astimezone(_berlin).date() - relativedelta(years=18)
    earliest_birthday = date(1900, 1, 1)
    if birthday_date > latest_18 or birthday_date < earliest_birthday:
        # Had to use dateutil here, because I didn't want to manually catch the case if somebody was born on 29th
        # stdlib timedelta doesn't support years as kwarg
        # February.
        raise ValueError(
            f"{param('geburtsdatum').param_id} must be in the range of " f"{earliest_birthday} to {latest_18}."
        )


REGEX_TEL_NR = re.compile(r"^(\+?[1-9]|0)[0-9]{7,14}$")


def check_telefonnummer(telefonnummer: Optional[str] = None):
    r"""
    telefonnummer must match the regex pattern `REGEX_TEL_NR` (ignoring all following characters: r"[-.\s()]").
    """
    if telefonnummer and re.match(REGEX_TEL_NR, re.sub(r"[-.\s()]", "", telefonnummer)) is None:
        raise ValueError(f"{param('telefonnummer').param_id} does not match the regex pattern " "for phone numbers.")


def check_address_deutsch(address: Adresse):
    """
    address must be in germany.
    """
    if required_field(address, "landescode", Landescode) != Landescode.DE:  # type:ignore[attr-defined]
        raise ValueError(f"{param('address').param_id}.landescode must be 'DE'")
    if not re.match(r"^\d{5}$", required_field(address, "postleitzahl", str)):
        raise ValueError(f"{param('address').param_id}.postleitzahl must consist of 5 digits")


def check_address_fields(address: Adresse):
    """
    This function reuses the pydantic validator function `strasse_xor_postfach` of the bo4e model `Addresse`.
    We use it here again to prevent any unwanted errors which can occur when bypassing the validator with `construct`.

    An address is valid if it contains a postfach XOR (a strasse AND hausnummer).
    This functions checks for these conditions of a valid address.

    Nur folgende Angabekombinationen sind (nach der Abfrage) möglich:
    Straße           w   f   f
    Hausnummer       w   f   f
    Postfach         f   w   f
    Postleitzahl     w   w   w
    Ort              w   w   w
    """
    _ = (
        required_field(address, "ort", str),
        required_field(address, "postleitzahl", str),
    )
    # pylint: disable=protected-access
    Adresse._strasse_xor_postfach(address.model_dump())  # type:ignore[operator]


def check_postleitzahl(postleitzahl: str):
    """
    Check that `postleitzahl` consists of only digits and letters (case-insensitive).
    """
    if not re.match(r"^[\dA-Za-z]+$", postleitzahl):
        raise ValueError(f"{param('postleitzahl').param_id} is invalid")


def check_iban(sepa_zahler: bool, iban: Optional[str] = None):
    r"""
    Check IBAN Syntax. It must match the pattern ^([A-Z]{2})(\d{11,30})$ where the first two character must form a
    valid country code. Additionally, the 'Prüfziffern' are used to validate the IBAN according to
    https://ibanvalidieren.de/verifikation.html.
    """
    if sepa_zahler:
        if iban is None:
            raise ValueError(f"{param('iban').param_id} is required for sepa_zahler")
        IBAN(iban).validate()


def check_bic(sepa_zahler: bool, bic: Optional[str] = None):
    """
    bic must consist of 8 or 11 alphanumeric characters.
    """
    if sepa_zahler:
        if bic is None:
            raise ValueError(f"{param('bic').param_id} is required for sepa_zahler")
        BIC(bic).validate()


def check_kontoinhaber(is_sepa_zahler: bool, kontoinhaber: Optional[str] = None):
    """
    Checks if the kontoinhaber has the syntax 'firstname lastname'. Since names are always difficult it actually only
    checks that there are no starting or ending spaces but contains at least one space in the middle of the string.
    """
    if is_sepa_zahler:
        if kontoinhaber is None:
            raise ValueError(f"{param('kontoinhaber').param_id} is required for sepa_zahler")
        if kontoinhaber.strip() == "":
            raise ValueError(f"{param('kontoinhaber').param_id} must be non-empty")


def check_bankname(is_sepa_zahler: bool, bankname: Optional[str] = None):
    """
    bankname is required for sepa_zahler and must not be empty.
    """
    if is_sepa_zahler:
        if bankname is None:
            raise ValueError(f"{param('bankname').param_id} is required for sepa_zahler")
        if not bankname.strip():
            raise ValueError(f"{param('bankname').param_id} must not be empty")


def check_vertragskontonummer(vertragskontonummer: str):
    """
    vertragskontonummer of every cba must consist of 9 digits.
    """
    if re.match(r"^\d{9}$", vertragskontonummer) is None:
        raise ValueError(f"{param('vertragskontonummer').param_id} must consist of 9 digits")


def is_datetime(date_to_check: datetime):
    """
    Check if date_to_check is of type datetime
    """
    if not isinstance(date_to_check, datetime):
        raise ValueError(f"{param('date_to_check').param_id} must be of type datetime")


ValidatorType: TypeAlias = Validator[TripicaCustomerLoaderDataSet, SyncValidatorFunction]

validate_geschaeftspartner_anrede: ValidatorType = Validator(check_geschaeftspartner_anrede)
validate_str_is_stripped: ValidatorType = Validator(check_str_is_stripped)
validate_geschaeftspartner_name3: ValidatorType = Validator(check_geschaeftspartner_name3)
validate_e_mail: ValidatorType = Validator(check_e_mail)
validate_extern_customer_id: ValidatorType = Validator(check_extern_customer_id)
validate_date_in_past_required: ValidatorType = Validator(check_date_in_past_required)
validate_date_in_future_required: ValidatorType = Validator(check_date_in_future_required)
validate_date_in_past_optional: ValidatorType = Validator(check_date_in_past_optional)
validate_date_in_future_optional: ValidatorType = Validator(check_date_in_future_optional)
validate_date_in_past_bankverbindung: ValidatorType = Validator(check_date_in_past_bankverbindung)
validate_geschaeftspartner_geburtsdatum: ValidatorType = Validator(check_geschaeftspartner_geburtsdatum)
validate_telefonnummer: ValidatorType = Validator(check_telefonnummer)
validate_address_deutsch: ValidatorType = Validator(check_address_deutsch)
validate_address_fields: ValidatorType = Validator(check_address_fields)
validate_postleitzahl: ValidatorType = Validator(check_postleitzahl)
validate_iban: ValidatorType = Validator(check_iban)
validate_bic: ValidatorType = Validator(check_bic)
validate_kontoinhaber: ValidatorType = Validator(check_kontoinhaber)
validate_bankname: ValidatorType = Validator(check_bankname)
validate_vertragskontonummer: ValidatorType = Validator(check_vertragskontonummer)
validate_is_datetime: ValidatorType = Validator(is_datetime)


def iter_contract_id_dict(some_dict: dict[str, Any]) -> Generator[tuple[Any, str], None, None]:
    """
    This function is used for `Query().iter()` to iterate over a dictionary. The values of the dictionary are returned
    and the key is used for tracking for proper `ValidationError`s.
    """
    return ((value, f"[contract_id={key}]") for key, value in some_dict.items())


def iter_vertragskonten(vertragskonten: list[Vertragskonto]) -> Generator[tuple[Vertragskonto, str], None, None]:
    """
    This function is used for `Query().iter()` to iterate over a dictionary. The values of the dictionary are returned
    and `vertragskonto.ouid` is used for tracking for proper `ValidationError`s.
    """
    return ((vertragskonto, f"[ouid={vertragskonto.ouid}]") for vertragskonto in vertragskonten)


class ParallelQueryMappedValidator(QueryMappedValidator[DataSetT, ValidatorFunctionT]):
    """
    This mapped validator class supplies the parameter combinations not as cartesian product but as parallel.
    I.e. each iterator must yield the same number of values or have to be scalar.
    => For every parameter pair p_i, p_j: len(p_i) == len(p_j) or len(p_i) == 1 or len(p_j) == 1
    """

    def param_sets(self, param_iterables: dict[str, QueryIterable]) -> Iterator[dict[str, Any] | Exception]:
        """
        This method is a generator which yields a dict of parameter sets. Each parameter set is a dict of parameter
        names and values. The parameter sets are yielded in parallel. It behaves similar to zip.
        """
        for param_iterable in param_iterables.values():
            param_iterable.include_exceptions = True
        param_sets = {param_name: list(param_iterable) for param_name, param_iterable in param_iterables.items()}
        lengths = [len(param_set) for param_set in param_sets.values()]
        iter_count = 1
        for length in lengths:
            if 1 < iter_count != length:
                raise ValueError("All parameter sets must have the same length or be scalar")
            if length != iter_count:
                iter_count = length
        for i in range(iter_count):
            param_set: Optional[dict[str, Any]] = {
                param_name: param_values[0] if len(param_values) == 1 else param_values[i]
                for param_name, param_values in param_sets.items()
            }
            assert param_set is not None
            for param_name, param_value in param_set.items():
                if param_name in self.validator.required_param_names and isinstance(param_value, Exception):
                    yield param_value
                    param_set = None
                    break
            if param_set is not None:
                yield param_set


class ValidationManagerProviderCustomer(Module):
    """
    This module provides a ValidationManager for customer loader with an injected MigrationConfig
    """

    @provider
    def customer_validation_manager(self, config: MigrationConfig) -> ValidationManager:
        """
        This method provides a ValidationManager for customer loader with an injected MigrationConfig
        """
        customer_manager = ValidationManagerWithConfig[TripicaCustomerLoaderDataSet](config)
        customer_manager.register(
            PathMappedValidator(validate_geschaeftspartner_anrede, {"anrede": "geschaeftspartner_erw.anrede"})
        )
        customer_manager.register(
            PathMappedValidator(validate_str_is_stripped, {"string": "geschaeftspartner_erw.name1"})
        )
        customer_manager.register(
            PathMappedValidator(validate_str_is_stripped, {"string": "geschaeftspartner_erw.name2"})
        )
        customer_manager.register(
            PathMappedValidator(validate_geschaeftspartner_name3, {"name3": "geschaeftspartner_erw.name3"})
        )
        customer_manager.register(
            PathMappedValidator(validate_e_mail, {"e_mail": "geschaeftspartner_erw.e_mail_adresse"})
        )
        customer_manager.register(
            PathMappedValidator(
                validate_extern_customer_id, {"externe_referenzen": "geschaeftspartner_erw.externe_referenzen"}
            )
        )
        customer_manager.register(
            PathMappedValidator(validate_date_in_past_required, {"past_date": "geschaeftspartner_erw.erstellungsdatum"})
        )
        customer_manager.register(
            PathMappedValidator(
                validate_geschaeftspartner_geburtsdatum, {"geburtsdatum": "geschaeftspartner_erw.geburtstag"}
            )
        )
        customer_manager.register(
            PathMappedValidator(validate_telefonnummer, {"telefonnummer": "geschaeftspartner_erw.telefonnummer_privat"})
        )
        customer_manager.register(
            PathMappedValidator(
                validate_telefonnummer, {"telefonnummer": "geschaeftspartner_erw.telefonnummer_geschaeft"}
            )
        )
        customer_manager.register(
            PathMappedValidator(validate_telefonnummer, {"telefonnummer": "geschaeftspartner_erw.telefonnummer_mobil"})
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_address_deutsch, {"address": Query().path("liefer_adressen").iter(iter_contract_id_dict)}
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_address_fields, {"address": Query().path("liefer_adressen").iter(iter_contract_id_dict)}
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_address_fields, {"address": Query().path("rechnungs_adressen").iter(iter_contract_id_dict)}
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_postleitzahl,
                {"postleitzahl": Query().path("rechnungs_adressen").iter(iter_contract_id_dict).path("postleitzahl")},
            )
        )
        customer_manager.register(
            ParallelQueryMappedValidator(
                validate_iban,
                {
                    "iban": Query().path("banks").iter(iter_contract_id_dict).path("iban"),
                    "sepa_zahler": Query().path("banks").iter(iter_contract_id_dict).path("sepa_info.sepa_zahler"),
                },
            )
        )
        customer_manager.register(
            ParallelQueryMappedValidator(
                validate_bic,
                {
                    "bic": Query().path("banks").iter(iter_contract_id_dict).path("bic"),
                    "sepa_zahler": Query().path("banks").iter(iter_contract_id_dict).path("sepa_info.sepa_zahler"),
                },
            )
        )
        customer_manager.register(
            ParallelQueryMappedValidator(
                validate_kontoinhaber,
                {
                    "kontoinhaber": Query().path("banks").iter(iter_contract_id_dict).path("kontoinhaber"),
                    "is_sepa_zahler": Query().path("banks").iter(iter_contract_id_dict).path("sepa_info.sepa_zahler"),
                },
            )
        )
        customer_manager.register(
            ParallelQueryMappedValidator(
                validate_date_in_past_bankverbindung,
                {
                    "past_date": Query().path("banks").iter(iter_contract_id_dict).path("gueltig_seit"),
                    "is_sepa_zahler": Query().path("banks").iter(iter_contract_id_dict).path("sepa_info.sepa_zahler"),
                },
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_date_in_future_optional,
                {"future_date": Query().path("banks").iter(iter_contract_id_dict).path("gueltig_bis")},
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_date_in_past_optional,
                {"past_date": Query().path("banks").iter(iter_contract_id_dict).path("sepa_info.gueltig_seit")},
            )
        )
        customer_manager.register(
            ParallelQueryMappedValidator(
                validate_bankname,
                {
                    "bankname": Query().path("banks").iter(iter_contract_id_dict).path("bankname"),
                    "is_sepa_zahler": Query().path("banks").iter(iter_contract_id_dict).path("sepa_info.sepa_zahler"),
                },
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_vertragskontonummer,
                {
                    "vertragskontonummer": Query()
                    .path("vertragskonten_mbas")
                    .iter(iter_vertragskonten)
                    .path("cbas")
                    .iter(iter_vertragskonten)
                    .path("vertrag.vertragsnummer")
                },
            )
        )
        customer_manager.register(
            QueryMappedValidator(
                validate_is_datetime,
                {
                    "date_to_check": Query()
                    .path("vertragskonten_mbas")
                    .iter(iter_vertragskonten)
                    .path("cbas")
                    .iter(iter_vertragskonten)
                    .path("erstellungsdatum")
                },
            )
        )
        return customer_manager
