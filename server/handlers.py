from asyncio import DatagramTransport

from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager
from shared.packet import Packet

manager = HandlersManager()


@manager.receive(PacketCode.SENSOR_REGISTRATION)
def device_registration(packet: Packet, transport: DatagramTransport) -> None:
    pass


@manager.receive(PacketCode.SENSOR_DATA)
def device_data_receiving(packet: Packet, transport: DatagramTransport) -> None:
    pass


@manager.receive(PacketCode.CHECK_ALIVE_RESPONSE)
def check_alive_response(packet: Packet, transport: DatagramTransport) -> None:
    pass
