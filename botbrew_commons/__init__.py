import importlib
import sys

# Import subpackages and register them so they can be imported as
# `botbrew_commons.data_models` and `botbrew_commons.repositories`.
_data_models = importlib.import_module('botbrew_commons.botbrew_commons.data_models')
sys.modules[__name__ + '.data_models'] = _data_models
_repositories = importlib.import_module('botbrew_commons.botbrew_commons.repositories')
sys.modules[__name__ + '.repositories'] = _repositories

__all__ = ["data_models", "repositories"]
