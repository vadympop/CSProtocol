from asyncio import DatagramTransport
from collections import defaultdict
from typing import Callable, Dict, Any

from shared.codes import PacketCode
from shared.handlers.types import CallbackType, StartupCallbackType, PacketAddr
from shared.middlewares.manager import MiddlewareManager
from shared.packet import Packet
from shared.sensors import SensorManager
from shared.transport.manager import TransportWrapper


class HandlersManager:
    def __init__(self, server_mode: bool = True, initial_storage: dict = None) -> None:
        self._callbacks: Dict[PacketCode, list[CallbackType]] = defaultdict(list)
        self._startup_callbacks: list[StartupCallbackType] = []
        self._transport_core: DatagramTransport | None = None
        self._transport: TransportWrapper | None = None
        self.server_mode = server_mode
        self.storage: dict[str, Any] = initial_storage or {}

        self.middlewares: MiddlewareManager = MiddlewareManager()
        self.sensors: SensorManager | None = SensorManager() if server_mode else None

    def copy(self, storage: dict = None) -> "HandlersManager":
        storage = self.storage if storage is None else self.storage | storage
        manager = HandlersManager(self.server_mode, storage)

        for code, callbacks in self._callbacks.items():
            for callback in callbacks:
                manager.receive(code)(callback)

        for callback in self._startup_callbacks:
            manager.startup()(callback)

        return manager

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
        self._transport_core = transport
        self._transport = TransportWrapper(transport)

        if self.server_mode:
            self.sensors.init_transport(self._transport)

        callback_kwargs = self._generate_callback_kwargs()
        for callback in self._startup_callbacks:
            callback(**callback_kwargs)

    def _generate_callback_kwargs(self, **kwargs) -> dict[str, Any]:
        middleware_kwargs = {"transport": self._transport, "storage": self.storage, **kwargs}
        if self.server_mode:
            middleware_kwargs |= {"sensors": self.sensors}

        return middleware_kwargs

    def process(self, data: bytes, addr: PacketAddr) -> None:
        if self.server_mode:
            self.sensors.update(addr)

        packet = Packet.from_any_payload(data)
        middleware_kwargs = self._generate_callback_kwargs(addr=addr)
        found_handlers = self._callbacks.get(packet.code, [])

        for handler in found_handlers:
            middleware = MiddlewareManager.wrap_middlewares(
                self.middlewares.collect_middlewares(packet.code, True),
                handler
            )
            middleware(packet, middleware_kwargs)
