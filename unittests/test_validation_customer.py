from datetime import UTC, datetime

import pytest
import pytz
from bomf import MigrationConfig
from ibims.bo4e import (
    Adresse,
    Anrede,
    Bankverbindung,
    ExterneReferenz,
    Geschaeftspartner,
    Kontaktart,
    Landescode,
    SepaInfo,
    Vertrag,
    VertragskontoCBA,
    VertragskontoMBA,
)
from ibims.datasets import TripicaCustomerLoaderDataSet
from injector import Injector
from pvframework import ValidationManager

from pvtool.customer_loader import ValidationManagerProviderCustomer

from .conftest import assert_full_error_coverage


@pytest.fixture
def customer_validation_manager():
    injector = Injector(
        [
            lambda binder: binder.bind(
                MigrationConfig, to=MigrationConfig(migration_key_date=datetime(2023, 6, 1, tzinfo=UTC))
            ),
            ValidationManagerProviderCustomer(),
        ]
    )
    return injector.get(ValidationManager)


class TestValidationCustomer:
    async def test_good_data_set(self, customer_validation_manager):
        good_data_set = TripicaCustomerLoaderDataSet.model_construct(
            powercloud_customer_id="209876543",
            geschaeftspartner=Geschaeftspartner.model_construct(
                externe_referenzen=[ExterneReferenz(ex_ref_name="customerID", ex_ref_wert="209876543")],
                name1="Mustermann",
                name2="Max",
                name3="Prof.",
                anrede=Anrede.HERR,
                e_mail_adresse="test@test.com",
                telefonnummer_mobil="+49 (0) 1324832749",
                telefonnummer_geschaeft="(01575) 01294673",
                telefonnummer_privat="0221 937436",
                erstellungsdatum=datetime(2023, 1, 1, tzinfo=pytz.UTC),
                geburtstag=datetime(2004, 2, 29, tzinfo=pytz.UTC),
            ),
            liefer_adressen={
                "contract_id_1": Adresse(postleitzahl="50564", ort="Köln", strasse="Gigastr.", hausnummer="5c"),
                "contract_id_2": Adresse(
                    postleitzahl="10238", ort="Gibt's nicht", strasse="Good Boi Straße", hausnummer="1245"
                ),
            },
            rechnungs_adressen={
                "contract_id_1": Adresse(postleitzahl="50564", ort="Köln", strasse="Gigastr.", hausnummer="5c"),
                "contract_id_2": Adresse(
                    postleitzahl="10238", ort="Gibt's nicht", strasse="Good Boi Straße", hausnummer="1245"
                ),
            },
            banks={
                "contract_id_1": Bankverbindung(
                    iban="DE52940594210000082271",
                    bic="TESTDETT421",
                    bankname="Sparkasse WelcheAuchImmer",
                    ouid=1,
                    kontoinhaber="Hochfrequenz",
                    gueltig_seit=datetime(2023, 1, 1, tzinfo=pytz.UTC),
                    sepa_info=SepaInfo(
                        sepa_id="123456789",
                        sepa_zahler=True,
                    ),
                )
            },
            vertragskonten_mbas=[
                VertragskontoMBA.model_construct(
                    ouid=1,
                    vertrags_adresse=Adresse(postleitzahl="50564", ort="Köln", strasse="Gigastr.", hausnummer="571234"),
                    vertragskontonummer="300010000",
                    rechnungsstellung=Kontaktart.E_MAIL,
                    cbas=[
                        VertragskontoCBA.model_construct(
                            ouid=11,
                            vertrags_adresse=Adresse(
                                postleitzahl="50564", ort="Köln", strasse="Gigastr.", hausnummer="571234"
                            ),
                            vertragskontonummer="300010001",
                            rechnungsstellung=Kontaktart.ANSCHREIBEN,
                            vertrag=Vertrag.model_construct(vertragsnummer="300010002"),
                            erstellungsdatum=datetime(2023, 1, 1, tzinfo=pytz.UTC),
                            rechnungsdatum_start=datetime(2023, 2, 1, tzinfo=pytz.UTC),
                            rechnungsdatum_naechstes=datetime(2023, 10, 1, tzinfo=pytz.UTC),
                        )
                    ],
                )
            ],
        )
        validation_summary = await customer_validation_manager.validate(good_data_set)
        assert validation_summary.num_fails == 0

    @pytest.mark.parametrize(
        ["bad_data_set", "expected_errors"],
        [
            pytest.param(
                TripicaCustomerLoaderDataSet.model_construct(
                    powercloud_customer_id="",
                    geschaeftspartner=Geschaeftspartner.model_construct(
                        externe_referenzen=[],
                        name1=" Mustermann",
                        name2=" Max",
                        name3="No Prof.",
                        anrede=Anrede.INDIVIDUELL,
                        e_mail_adresse="test@test",
                        telefonnummer_mobil="0392ujdi",
                        erstellungsdatum=datetime(2482, 1, 1, tzinfo=pytz.UTC),
                        geburtstag=datetime(2012, 2, 29, tzinfo=pytz.UTC),
                    ),
                    liefer_adressen={
                        "contract_id_1": Adresse(
                            postleitzahl="50564", ort="Köln", landescode=Landescode.GB  # type:ignore[attr-defined]
                        ),
                        "contract_id_2": Adresse(
                            postleitzahl="102384", ort="Gibt's nicht", strasse="Good Boi Straße", hausnummer="1245"
                        ),
                    },
                    rechnungs_adressen={
                        "contract_id_1": Adresse(postleitzahl="34-65c", ort="Köln", strasse="Gigastr.", hausnummer="5"),
                        "contract_id_2": Adresse(
                            postleitzahl="10238", ort="Gibt's nicht", strasse="Good Boi Straße", hausnummer="1245"
                        ),
                    },
                    banks={
                        "contract_id_1": Bankverbindung.model_construct(
                            iban="DE42940594210000082271",
                            bic="TESTDETT4321",
                            ouid=1,
                            kontoinhaber=" ",
                            gueltig_seit=datetime(2200, 1, 1, tzinfo=pytz.UTC),
                            gueltig_bis=datetime(2023, 1, 1, tzinfo=pytz.UTC),
                            sepa_info=SepaInfo(
                                sepa_id="", sepa_zahler=True, gueltig_seit=datetime(2200, 1, 1, tzinfo=pytz.UTC)
                            ),
                        )
                    },
                    vertragskonten_mbas=[
                        VertragskontoMBA.model_construct(
                            ouid=1,
                            vertrags_adresse=Adresse(
                                postleitzahl="50564", ort="Köln", strasse="Gigastr.", hausnummer="571234"
                            ),
                            vertragskontonummer="300010",
                            rechnungsstellung=Kontaktart.E_MAIL,
                            cbas=[
                                VertragskontoCBA.model_construct(
                                    ouid=11,
                                    vertrags_adresse=Adresse(
                                        postleitzahl="50564", ort="Köln", strasse="Gigastr.", hausnummer="571234"
                                    ),
                                    vertragskontonummer="3000100",
                                    rechnungsstellung=Kontaktart.ANSCHREIBEN,
                                    vertrag=Vertrag.model_construct(vertragsnummer="2000100"),
                                    erstellungsdatum=datetime(2223, 1, 1, tzinfo=pytz.UTC),
                                    rechnungsdatum_start=datetime(2023, 2, 1, tzinfo=pytz.UTC),
                                    rechnungsdatum_naechstes=datetime(2023, 10, 1, tzinfo=pytz.UTC),
                                )
                            ],
                        )
                    ],
                ),
                [
                    "geschaeftspartner.name1 must not start or end with whitespace.",
                    "geschaeftspartner.name2 must not start or end with whitespace.",
                    "geschaeftspartner.name3 must be one of the following",
                    "The part after the @-sign is not valid. It should have a period",  # E-Mail
                    "No ExterneReferenz with name customerID",
                    "geschaeftspartner.geburtstag must be in the range of",
                    "geschaeftspartner.erstellungsdatum must be in the past",
                    "geschaeftspartner.anrede must be one of the following",
                    "geschaeftspartner.telefonnummer_mobil does not match the regex pattern for phone numbers",
                    "liefer_adressen[contract_id=contract_id_1].landescode must be 'DE'",
                    "liefer_adressen[contract_id=contract_id_2].postleitzahl must consist of 5 digits",
                    "rechnungs_adressen[contract_id=contract_id_1].postleitzahl is invalid",
                    "banks[contract_id=contract_id_1].bankname is required for sepa_zahler",
                    "banks[contract_id=contract_id_1].kontoinhaber must be non-empty",
                    "banks[contract_id=contract_id_1].gueltig_seit must be in the past",
                    "banks[contract_id=contract_id_1].gueltig_bis must be in the future",
                    "banks[contract_id=contract_id_1].sepa_info.gueltig_seit must be in the past",
                    "Invalid length '12'",  # BIC
                    "Invalid checksum digits",  # IBAN
                    "vertragskonten_mbas[ouid=1].cbas[ouid=11].vertrag.vertragsnummer must consist of 9 digits",
                ],
                id="errors in validators",
            ),
            pytest.param(
                TripicaCustomerLoaderDataSet.model_construct(
                    powercloud_customer_id="",
                    geschaeftspartner=Geschaeftspartner.model_construct(),
                    rechnungs_adressen={
                        "contract_id_1": Adresse.model_construct(),
                    },
                    banks={
                        "contract_id_1": Bankverbindung.model_construct(
                            sepa_info=SepaInfo.model_construct(sepa_zahler=True)
                        )
                    },
                    vertragskonten_mbas=[
                        VertragskontoMBA.model_construct(
                            ouid=1,
                            cbas=[VertragskontoCBA.model_construct(ouid=11)],
                        )
                    ],
                ),
                [
                    "geschaeftspartner.anrede: None is not an instance of ibims.bo4e.enum.anrede.Anrede",
                    "geschaeftspartner.name1: None is not an instance of str",
                    "geschaeftspartner.name2: None is not an instance of str",
                    "geschaeftspartner.geburtstag: None is not an instance of datetime.datetime",
                    "geschaeftspartner.erstellungsdatum: None is not an instance of datetime.datetime",
                    "geschaeftspartner.externe_referenzen: None is not a list",
                    "rechnungs_adressen[contract_id=contract_id_1].ort: None is not an instance of str",
                    "rechnungs_adressen[contract_id=contract_id_1].postleitzahl: None is not an instance of str",
                    "vertragskonten_mbas[ouid=1].cbas[ouid=11].erstellungsdatum: value not provided",
                    "vertragskonten_mbas[ouid=1].cbas[ouid=11].vertrag.vertragsnummer: value not provided",
                    "banks[contract_id=contract_id_1].bic is required for sepa_zahler",
                    "banks[contract_id=contract_id_1].iban is required for sepa_zahler",
                    "liefer_adressen: value not provided",
                    "liefer_adressen: value not provided",
                    "banks[contract_id=contract_id_1].bankname is required for sepa_zahler",
                    "banks[contract_id=contract_id_1].kontoinhaber is required for sepa_zahler",
                    "banks[contract_id=contract_id_1].gueltig_seit is required for sepa_zahler",
                ],
                id="missing fields",
            ),
        ],
    )
    async def test_bad_data_sets(
        self, customer_validation_manager, bad_data_set: TripicaCustomerLoaderDataSet, expected_errors: list[str]
    ):
        validation_summary = await customer_validation_manager.validate(bad_data_set)

        assert validation_summary.num_errors_total == len(expected_errors)
        assert_full_error_coverage(expected_errors, validation_summary.all_errors)
