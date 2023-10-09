import pytest
from pydantic import BaseModel, ValidationError, field_validator

from pvtool.malo_id_validation import validate_marktlokations_id


class _ClassWithMaLoId(BaseModel):
    malo_id: str
    _malo_id_check = field_validator("malo_id")(validate_marktlokations_id)


class TestMaloIdValidation:
    @pytest.mark.parametrize(
        "malo_id, is_valid",
        [
            pytest.param("51238696781", True),
            pytest.param("41373559241", True),
            pytest.param("56789012345", True),
            pytest.param("52935155442", True),
            pytest.param("12345678910", False),
            pytest.param("asdasd", False),
            pytest.param("   ", False),
            pytest.param("  asdasdasd ", False),
            pytest.param("keine malo id", False),
            pytest.param(None, False),
            pytest.param("", False),
        ],
    )
    def test_id_validation(self, malo_id: str, is_valid: bool) -> None:
        def _instantiate_malo(malo_id: str) -> None:
            _ = _ClassWithMaLoId(
                malo_id=malo_id,
            )

        if not is_valid:
            with pytest.raises(ValidationError):
                _instantiate_malo(malo_id)
        else:
            _instantiate_malo(malo_id)
