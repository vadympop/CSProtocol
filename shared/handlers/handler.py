import inspect
from dataclasses import dataclass, field
from typing import Any

from .types import CallbackType


@dataclass
class HandlerObject:
    func: CallbackType
    params: set[str] = field(init=False)

    def __post_init__(self) -> None:
        func = inspect.unwrap(self.func)
        spec = inspect.getfullargspec(func)
        self.params = {*spec.args, *spec.kwonlyargs}  # which params method has in signature
        self.varkw = spec.varkw is not None  # if method has '**kwargs' in signature

    def _prepare_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self.varkw:
            return kwargs

        return {k: kwargs[k] for k in self.params if k in kwargs}

    def call(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **self._prepare_kwargs(kwargs))
