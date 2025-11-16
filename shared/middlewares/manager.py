import functools

from collections import defaultdict
from typing import Sequence, Any, Dict

from shared.codes import PacketCode
from shared.middlewares.types import MiddlewareType, NextMiddlewareType
from shared.handlers.types import CallbackType
from shared.packets import Packet


class MiddlewareManager:
    def __init__(self):
        self._middlewares: Dict[PacketCode, list[MiddlewareType]] = defaultdict(list)

    def register(
        self, code: PacketCode | list[PacketCode], middleware: MiddlewareType,
    ) -> MiddlewareType:
        if isinstance(code, PacketCode):
            code = [code,]

        for rec in code:
            self._middlewares[rec].append(middleware)

        return middleware

    def unregister(self, code: PacketCode, middleware: MiddlewareType) -> None:
        self._middlewares[code].remove(middleware)

    def collect_middlewares(self, code: PacketCode, with_global: bool = False) -> list[MiddlewareType]:
        found_midlw = self._middlewares.get(code, [])
        if with_global:
            found_midlw += self._middlewares.get(PacketCode.GLOBAL, [])

        return found_midlw

    @staticmethod
    def wrap_middlewares(
        middlewares: Sequence[MiddlewareType], final_handler: CallbackType
    ) -> NextMiddlewareType:
        @functools.wraps(final_handler)
        def handler_wrapper(packet: Packet, kwargs: Dict[str, Any]) -> Any:
            return final_handler(packet, **kwargs)

        middleware = handler_wrapper
        for m in reversed(middlewares):
            middleware = functools.partial(m, middleware)

        return middleware
