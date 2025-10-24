from asyncio import DatagramTransport

from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager

from .utils import generate_sensor_token
from .middlewares import check_token, check_crc

manager = HandlersManager()
manager.middlewares.register(check_crc)
manager.middlewares.register(check_token)


@manager.receive(PacketCode.SENSOR_REGISTRATION)
def device_registration(packet: pkt.SensorRegistrationPkt, transport: DatagramTransport) -> None:
    token = generate_sensor_token()

    transport.sendto(pkt.RegistrationAckPkt(token=token).to_bytes())


@manager.receive(PacketCode.SENSOR_DATA)
def device_data_receiving(packet: pkt.SensorDataPkt, transport: DatagramTransport) -> None:
    transport.sendto(pkt.DataAckPkt().to_bytes())


@manager.receive(PacketCode.CHECK_ALIVE_RESPONSE)
def check_alive_response(packet: pkt.CheckAliveResponsePkt, transport: DatagramTransport) -> None:
    pass
