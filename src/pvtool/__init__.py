"""
This package provides `ValidationManager`s to validate data sets from `ibims`. Currently, only customer, resource and
network data sets are supported.
The `ValidationManager`s are provided through `injector.Module`s.
"""

from .customer_loader import ValidationManagerProviderCustomer
from .network_loader import ValidationManagerProviderNetwork
from .resource_loader import ValidationManagerProviderResource
