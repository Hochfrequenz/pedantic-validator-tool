# Pedantic Validator Tool

![Unittests status badge](https://github.com/Hochfrequenz/pedantic-validator-tool/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/pedantic-validator-tool/workflows/Coverage/badge.svg)
![Linting status badge](https://github.com/Hochfrequenz/pedantic-validator-tool/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/pedantic-validator-tool/workflows/Formatting/badge.svg)
![PyPI](https://img.shields.io/pypi/v/pvtool)

This package contains the validation logic to validate the data of the BO4E migration model
[ibims](https://github.com/Hochfrequenz/intermediate-bo4e-migration-models).
It uses the [pedantic-validator-framework](https://github.com/Hochfrequenz/pedantic-validator-framework) to
create `ValidationManager`s for each data set in
[ibims](https://github.com/Hochfrequenz/intermediate-bo4e-migration-models).
(Currently supported are only `Customer`, `Network` and `Resource`.)

This package is designed to be used together with [bomf](https://github.com/Hochfrequenz/bo4e_migration_framework).
Although, it only uses the `MigrationConfig` to use the `migration_key_date` which is necessary for some validations.

## Usage
Install it [from pypi](https://pypi.org/project/pvtool/):
```bash
pip install pvtool
```

To use the validation logic you just need to bind the preconfigured modules of this package to
`ValidationManager` of your `Injector`. Alternatively, you could execute the provider-method of the
module on your own by supplying a `MigrationConfig` instance.

```python
from injector import Injector
from pvtool import ValidationManagerProviderCustomer
from pvframework import ValidationManager
from bomf.config import MigrationConfig
from datetime import datetime, UTC

customer_injector = Injector([
    ValidationManagerProviderCustomer,
    lambda binder: binder.bind(MigrationConfig, MigrationConfig(migration_key_date=datetime(2021, 1, 1, tzinfo=UTC))),
])

customer_validation_manager = customer_injector.get(ValidationManager)
```

## How to use this Repository on Your Machine

Follow the instructions in our [Python template repository](https://github.com/Hochfrequenz/python_template_repository#how-to-use-this-repository-on-your-machine).

## Contribute

You are very welcome to contribute to this repository by opening a pull request against the main branch.
