from asyncio import DatagramTransport
from collections import defaultdict
from typing import Callable, Dict

from shared.codes import PacketCode
from shared.handlers.types import CallbackType, StartupCallbackType
from shared.middlewares.manager import MiddlewareManager
from shared.packet import Packet


class HandlersManager:
    def __init__(self):
        self._callbacks: Dict[PacketCode, list[CallbackType]] = defaultdict(list)
        self._startup_callbacks: list[StartupCallbackType] = []
        self._transport: DatagramTransport | None = None
        self.middlewares = MiddlewareManager()

    def receive(self, code: PacketCode) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """
        if not code.isdigit() and code != PacketCode.GLOBAL:
            raise TypeError(f"Handler code {code} has invalid type")

        def wrapper(callback: CallbackType) -> CallbackType:
            self._callbacks[code].append(callback)
            return callback

        return wrapper

    def startup(self) -> Callable[[StartupCallbackType], StartupCallbackType]:
        def wrapper(callback: StartupCallbackType) -> StartupCallbackType:
            self._startup_callbacks.append(callback)
            return callback

        return wrapper

    def on_startup(self, transport: DatagramTransport) -> None:
        self._transport = transport
        for callback in self._startup_callbacks:
            callback(transport)

    def process(self, data: bytes) -> None:
        packet = Packet.from_any_payload(data)

        found_handlers = self._callbacks.get(packet.code, [])
        for handler in found_handlers:
            middleware = MiddlewareManager.wrap_middlewares(
                self.middlewares.collect_middlewares(packet.code, True),
                handler
            )
            middleware(packet, self._transport)
