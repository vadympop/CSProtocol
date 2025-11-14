from asyncio import DatagramTransport
from collections import defaultdict
from typing import Callable, Dict, Any

from shared.codes import PacketCode
from shared.middlewares import MiddlewareManager
from shared.packet import Packet
from shared.sensors import SensorManager
from shared.tasks import BackgroundTasksManager
from shared.transport import TransportWrapper

from .handler import HandlerObject
from .types import CallbackType
from ..types import PacketAddr


class HandlersManager:
    def __init__(self, server_mode: bool = True, initial_storage: dict = None) -> None:
        self._handlers: Dict[PacketCode, list[HandlerObject]] = defaultdict(list)
        self._startup_callbacks: list[HandlerObject] = []
        self._transport_core: DatagramTransport | None = None
        self._transport: TransportWrapper | None = None
        self.server_mode = server_mode
        self.storage: dict[str, Any] = initial_storage or {}

        self.background_tasks: BackgroundTasksManager = BackgroundTasksManager()
        self.middlewares: MiddlewareManager = MiddlewareManager()
        self.sensors: SensorManager | None = SensorManager(self.background_tasks) if server_mode else None

    def copy(self, storage: dict = None) -> "HandlersManager":
        storage = {**self.storage} if storage is None else {**self.storage} | storage
        manager = HandlersManager(self.server_mode, storage)

        for code, callbacks in self._handlers.items():
            for callback in callbacks:
                manager.receive(code)(callback.func)

        for callback in self._startup_callbacks:
            manager.startup()(callback.func)

        return manager

    def receive(self, code: PacketCode) -> Callable[[CallbackType], CallbackType]:
        """
        Decorator for registering event handlers
        """
        if not code.isdigit() and code != PacketCode.GLOBAL:
            raise TypeError(f"Handler code {code} has invalid type")

        def wrapper(callback: CallbackType) -> CallbackType:
            self._handlers[code].append(HandlerObject(callback))
            return callback

        return wrapper

    def startup(self) -> Callable[[CallbackType], CallbackType]:
        def wrapper(callback: CallbackType) -> CallbackType:
            self._startup_callbacks.append(HandlerObject(callback))
            return callback

        return wrapper

    def call_startup(self) -> None:
        for callback in self._startup_callbacks:
            callback_kwargs = self._generate_middleware_kwargs()
            callback.call(**callback_kwargs)

    def init(self, transport: DatagramTransport) -> None:
        self._transport_core = transport
        self._transport = TransportWrapper(transport)

        if self.server_mode:
            self.sensors.init_transport(self._transport)

        self.call_startup()

    def _generate_middleware_kwargs(self, **kwargs) -> dict[str, Any]:
        middleware_kwargs = {
            "handlers": self,
            "transport": self._transport,
            "storage": self.storage,
            "background_tasks": self.background_tasks,
            **kwargs
        }
        if self.server_mode:
            middleware_kwargs |= {"sensors": self.sensors}

        return middleware_kwargs

    def process(self, data: bytes, addr: PacketAddr) -> None:
        if self.server_mode:
            self.sensors.update(addr)

        packet = Packet.from_any_payload(data)
        found_handlers = self._handlers.get(packet.code, [])

        for handler in found_handlers:
            middleware_kwargs = self._generate_middleware_kwargs(addr=addr)
            middleware = MiddlewareManager.wrap_middlewares(
                self.middlewares.collect_middlewares(packet.code, True),
                handler.call
            )
            middleware(packet, middleware_kwargs)
