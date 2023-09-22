from datetime import datetime

import pytest
from bo4e.bo.marktlokation import Marktlokation
from bo4e.bo.messlokation import Messlokation
from bo4e.bo.vertrag import Vertrag
from bo4e.bo.zaehler import Zaehler
from bo4e.com.messlokationszuordnung import Messlokationszuordnung
from bo4e.enum.sparte import Sparte
from ibims.datasets import TripicaResourceLoaderDataSet
from injector import Injector
from pvframework import ValidationManager

from pvtool.resource_loader import ValidationManagerProviderResource


@pytest.fixture
def resource_validation_manager() -> ValidationManager:
    injector = Injector([ValidationManagerProviderResource()])
    return injector.get(ValidationManager)


class TestValidationResource:
    async def test_good_data_set(self, resource_validation_manager: ValidationManager):
        good_data_set = TripicaResourceLoaderDataSet(
            marktlokation=Marktlokation.model_construct(
                marktlokations_id="01234567890",
                zugehoerige_messlokation=Messlokationszuordnung.model_construct(gueltig_seit=datetime(2023, 2, 8)),
            ),
            messlokation=Messlokation.model_construct(messlokations_id="DE0123401234012340123401234012340"),
            vertrag=Vertrag.model_construct(sparte=Sparte.STROM),
            zaehler=Zaehler.model_construct(zaehlernummer="893824827395hhjbd0"),
        )
        validation_summary = await resource_validation_manager.validate(good_data_set)
        assert validation_summary.num_errors_total == 0

    @pytest.mark.parametrize(
        ["bad_data_set", "expected_errors"],
        [
            pytest.param(
                TripicaResourceLoaderDataSet(
                    marktlokation=Marktlokation.model_construct(
                        marktlokations_id="01237890",
                        zugehoerige_messlokation=Messlokationszuordnung.model_construct(
                            gueltig_seit=datetime(2023, 2, 10)
                        ),
                    ),
                    messlokation=Messlokation.model_construct(messlokations_id="EN0123401234012340123401234012340"),
                    vertrag=Vertrag.model_construct(sparte=Sparte.WASSER),
                    zaehler=Zaehler.model_construct(zaehlernummer=" 893824827395hhjbd0"),
                ),
                [
                    "messlokation.messlokations_id has to start with 'DE' followed by 11 digits and 20 "
                    "alphanumeric characters.",
                    "marktlokation.marktlokations_id has to consist of 11 digits.",
                    "vertrag.sparte must be one of the following: 'STROM', 'GAS'",
                    "zaehler.zaehlernummer must not start with whitespace",
                ],
                id="errors in validators",
            ),
            pytest.param(
                TripicaResourceLoaderDataSet(
                    marktlokation=Marktlokation.model_construct(),
                    messlokation=Messlokation.model_construct(messlokations_id="DE0123401234012340123401234012340"),
                    vertrag=Vertrag.model_construct(sparte=Sparte.STROM),
                    zaehler=Zaehler.model_construct(zaehlernummer="893824827395hhjbd0"),
                ),
                [
                    "'marktlokation.marktlokations_id' does not exist",
                ],
                id="missing fields",
            ),
        ],
    )
    async def test_bad_data_sets(
        self,
        resource_validation_manager: ValidationManager,
        bad_data_set: TripicaResourceLoaderDataSet,
        expected_errors: list[str],
    ):
        validation_summary = await resource_validation_manager.validate(bad_data_set)

        assert validation_summary.num_errors_total == len(expected_errors)
        for expected_error in expected_errors:
            exception_found = False
            for error in validation_summary.all_errors:
                if expected_error in str(error):
                    exception_found = True

            assert exception_found, f"No exception found for expected error '{expected_error}'"
