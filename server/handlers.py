from asyncio import DatagramTransport

from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager
from shared.handlers.types import PacketAddr

from .utils import generate_sensor_token
from .middlewares import check_token, check_crc, check_unregistered_sensors

manager = HandlersManager()
manager.middlewares.register(PacketCode.GLOBAL, check_crc)
# For all except SENSOR_REGISTRATION
manager.middlewares.register([PacketCode.SENSOR_DATA, PacketCode.CHECK_ALIVE_RESPONSE], check_token)
manager.middlewares.register([PacketCode.SENSOR_DATA, PacketCode.CHECK_ALIVE_RESPONSE], check_unregistered_sensors)


@manager.receive(PacketCode.SENSOR_REGISTRATION)
def device_registration(
        packet: pkt.SensorRegistrationPkt,
        addr: PacketAddr,
        transport: DatagramTransport
) -> None:
    token = generate_sensor_token()
    manager.sensors.register(addr, packet.sensor_type, token)

    transport.sendto(pkt.RegistrationAckPkt(token=token).to_bytes())


@manager.receive(PacketCode.SENSOR_DATA)
def device_data_receiving(
        packet: pkt.SensorRegistrationPkt,
        addr: PacketAddr,
        transport: DatagramTransport
) -> None:
    transport.sendto(pkt.DataAckPkt().to_bytes())


@manager.receive(PacketCode.CHECK_ALIVE_RESPONSE)
def check_alive_response(
        packet: pkt.SensorRegistrationPkt,
        addr: PacketAddr,
        transport: DatagramTransport
) -> None:
    pass
