"""
This module contains the ValidationManager classes used throughout the PV-Tool.
"""
from bomf.config import MigrationConfig
from injector import inject
from pvframework import ValidationManager
from pvframework.types import DataSetT


class ValidationManagerWithConfig(ValidationManager[DataSetT]):
    """
    This class extends the ValidationManager class from the bomf package by adding the MigrationConfig.
    """

    @inject
    def __init__(self, config: MigrationConfig):
        super().__init__()
        self.config = config
