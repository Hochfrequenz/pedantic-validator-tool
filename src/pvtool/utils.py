"""
Contains utility functions to be used in the PV-Tool.
"""
import inspect
from typing import Optional

from bomf.config import MigrationConfig
from pvframework import ValidationManager

from .validation_manager import ValidationManagerWithConfig


def migration_config() -> MigrationConfig:
    """
    This function can only be used inside validator functions and will only work if the function is executed by the
    validation framework. If you run the validator function "by yourself" or use this function elsewhere it will
    raise a RuntimeError.
    When using inside a validator function, this function returns the MigrationConfig object.
    E.g.:
    ```
    def validate_datetime(datetime_inst: datetime):
        config = migration_config()
        assert config.migration_key_date >= datetime_inst
    ```
    """
    call_stack = inspect.stack()
    # call_stack[0] -> this function
    # call_stack[1] -> must be the validator function
    # call_stack[2] -> should be either `_execute_sync_validator` or `_execute_async_validator`
    validation_manager: Optional[ValidationManagerWithConfig] = None
    try:
        validation_manager = call_stack[2].frame.f_locals["self"]
        if not isinstance(validation_manager, ValidationManagerWithConfig):
            if isinstance(validation_manager, ValidationManager):
                raise TypeError(
                    "You can call this function only on ValidationManagerWithConfig, not on ValidationManager"
                )
            validation_manager = None
    except KeyError:
        pass

    if validation_manager is None:
        raise RuntimeError(
            "You can call this function only directly from inside a function "
            "which is executed by the validation framework"
        )

    config: MigrationConfig = validation_manager.config
    assert isinstance(config, MigrationConfig), "This shouldn't happen"
    return config
