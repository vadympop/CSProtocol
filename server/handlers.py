from asyncio import DatagramTransport

from shared.handlers.manager import HandlersManager
from shared.packet import Packet

manager = HandlersManager()


@manager.receive("0")
def device_registration(packet: Packet, transport: DatagramTransport) -> None:
    pass


@manager.receive("1")
def device_data_receiving(packet: Packet, transport: DatagramTransport) -> None:
    pass


@manager.receive("31")
def check_alive_response(packet: Packet, transport: DatagramTransport) -> None:
    pass
