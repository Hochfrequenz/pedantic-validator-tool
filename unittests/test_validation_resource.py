from datetime import datetime

import pytest
from ibims.bo4e import Marktlokation, Messlokation, Messlokationszuordnung, Sparte, Vertrag, Zaehler
from ibims.datasets import TripicaResourceLoaderDataSet
from injector import Injector
from pvframework import ValidationManager

from pvtool.resource_loader import ValidationManagerProviderResource

from .conftest import assert_full_error_coverage


@pytest.fixture
def resource_validation_manager() -> ValidationManager:
    injector = Injector([ValidationManagerProviderResource()])
    return injector.get(ValidationManager)


class TestValidationResource:
    async def test_good_data_set(self, resource_validation_manager: ValidationManager):
        good_data_set = TripicaResourceLoaderDataSet.model_construct(
            marktlokation=Marktlokation.model_construct(  # type: ignore[call-arg]
                marktlokations_id="01234567890",
                zugehoerige_messlokation=Messlokationszuordnung.model_construct(  # type: ignore[call-arg]
                    gueltig_seit=datetime(2023, 2, 8)
                ),
            ),
            messlokation=Messlokation.model_construct(messlokations_id="DE0123401234012340123401234012340"),
            vertrag=Vertrag.model_construct(sparte=Sparte.STROM),  # type: ignore[call-arg]
            zaehler=Zaehler.model_construct(zaehlernummer="893824827395hhjbd0"),  # type: ignore[call-arg]
        )
        validation_summary = await resource_validation_manager.validate(good_data_set)
        assert validation_summary.num_errors_total == 0

    @pytest.mark.parametrize(
        ["bad_data_set", "expected_errors"],
        [
            pytest.param(
                TripicaResourceLoaderDataSet.model_construct(
                    marktlokation=Marktlokation.model_construct(  # type: ignore[call-arg]
                        marktlokations_id="01237890",
                        zugehoerige_messlokation=Messlokationszuordnung.model_construct(  # type: ignore[call-arg]
                            gueltig_seit=datetime(2023, 2, 10)
                        ),
                    ),
                    messlokation=Messlokation.model_construct(messlokations_id="EN0123401234012340123401234012340"),
                    vertrag=Vertrag.model_construct(sparte=Sparte.WASSER),  # type: ignore[call-arg]
                    zaehler=Zaehler.model_construct(zaehlernummer=" 893824827395hhjbd0"),  # type: ignore[call-arg]
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
                TripicaResourceLoaderDataSet.model_construct(
                    marktlokation=Marktlokation.model_construct(),  # type: ignore[call-arg]
                    messlokation=Messlokation.model_construct(messlokations_id="DE0123401234012340123401234012340"),
                    vertrag=Vertrag.model_construct(sparte=Sparte.STROM),  # type: ignore[call-arg]
                    zaehler=Zaehler.model_construct(zaehlernummer="893824827395hhjbd0"),  # type: ignore[call-arg]
                ),
                [
                    "marktlokation.marktlokations_id: value not provided",
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
        assert_full_error_coverage(set(expected_errors), set(validation_summary.all_errors))
