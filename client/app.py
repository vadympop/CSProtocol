from asyncio import DatagramProtocol, DatagramTransport, Future

from shared.handlers import HandlersManager
from shared.handlers.types import PacketAddr


class SensorProtocol(DatagramProtocol):
    def __init__(self, handler_manager: HandlersManager, on_connection_lost: Future[bool]) -> None:
        self.on_connection_lost: Future[bool] = on_connection_lost
        self.transport: DatagramTransport | None = None
        self._handlers_manager: HandlersManager = handler_manager

    def connection_made(self, transport: DatagramTransport) -> None:
        self.transport = transport
        self._handlers_manager.init(transport)
        print("Connection established")

    def datagram_received(self, data: bytes, addr: PacketAddr) -> None:
        self._handlers_manager.process(data, addr)

    def error_received(self, exc: Exception) -> None:
        print('Error received:', exc)

    def connection_lost(self, exc: Exception | None) -> None:
        print("Connection closed")
        self.on_connection_lost.set_result(True)
