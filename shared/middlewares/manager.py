import functools
from asyncio import DatagramTransport

from collections import defaultdict
from typing import Sequence, Any, Dict

from shared.middlewares.types import MiddlewareType, NextMiddlewareType
from shared.handlers.types import CallbackType
from shared.packet import Packet


class MiddlewareManager:
    def __init__(self):
        self._middlewares: Dict[str, list[MiddlewareType]] = defaultdict(list)

    def register(
        self, code: str, middleware: MiddlewareType,
    ) -> MiddlewareType:
        self._middlewares[code].append(middleware)
        return middleware

    def unregister(self, code: str, middleware: MiddlewareType) -> None:
        self._middlewares[code].remove(middleware)

    def collect_middlewares(self, code: str, with_global: bool = False) -> list[MiddlewareType]:
        found_midlw = self._middlewares.get(code, [])
        if with_global:
            found_midlw += self._middlewares.get("*", [])

        return found_midlw

    @staticmethod
    def wrap_middlewares(
        middlewares: Sequence[MiddlewareType], final_handler: CallbackType
    ) -> NextMiddlewareType:
        @functools.wraps(final_handler)
        def handler_wrapper(packet: Packet, transport: DatagramTransport) -> Any:
            return final_handler(packet, transport)

        middleware = handler_wrapper
        for m in reversed(middlewares):
            middleware = functools.partial(m, middleware)

        return middleware
