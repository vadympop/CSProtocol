from typing import Callable
from asyncio import DatagramProtocol, DatagramTransport

from shared.handlers import HandlersManager
from shared.types import PacketAddr
from shared.logger import Logger


class CSProtocol(DatagramProtocol):
    def __init__(self, handler_manager: HandlersManager, on_connection_lost: Callable[[], None]) -> None:
        self.on_connection_lost: Callable[[], None] = on_connection_lost
        self.transport: DatagramTransport | None = None
        self._handlers_manager: HandlersManager = handler_manager

    def connection_made(self, transport: DatagramTransport) -> None:
        self.transport = transport
        self._handlers_manager.init(transport)
        Logger.log_debug("Server started")

    def datagram_received(self, data: bytes, addr: PacketAddr) -> None:
        self._handlers_manager.process(data, addr)

    def error_received(self, exc: Exception) -> None:
        Logger.log_debug(f"Error received: {exc}")

    def connection_lost(self, exc: Exception | None) -> None:
        Logger.log_debug("Server stopped")
        self.on_connection_lost()
