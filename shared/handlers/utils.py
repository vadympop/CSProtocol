import inspect
from functools import lru_cache
from typing import Callable


@lru_cache()
def get_handler_params(handler: Callable):
    return set(inspect.signature(handler).parameters.keys())
