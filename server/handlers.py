from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager
from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.sensors import SensorManager
from shared.transport.manager import TransportWrapper

from .utils import generate_sensor_token
from .middlewares import check_token, check_crc, check_unregistered_sensors

manager = HandlersManager()
manager.middlewares.register(
    [PacketCode.SENSOR_DATA, PacketCode.CHECK_ALIVE_RESPONSE],
    check_unregistered_sensors
) # ~ For all except SENSOR_REGISTRATION
manager.middlewares.register(PacketCode.GLOBAL, check_crc)
manager.middlewares.register(
    [PacketCode.SENSOR_DATA, PacketCode.CHECK_ALIVE_RESPONSE],
    check_token
)  # ~ For all except SENSOR_REGISTRATION


@manager.receive(PacketCode.SENSOR_REGISTRATION)
def device_registration(
        packet: pkt.SensorRegistrationPkt,
        addr: PacketAddr,
        transport: TransportWrapper,
        sensors: SensorManager,
) -> None:
    token = generate_sensor_token()
    sensors.register(addr, packet.sensor_type, token)

    transport.sendto(pkt.RegistrationAckPkt(token=token), addr)


@manager.receive(PacketCode.SENSOR_DATA)
def device_data_receiving(
        packet: pkt.SensorDataPkt,
        addr: PacketAddr,
        transport: TransportWrapper,
        sensors: SensorManager,
) -> None:
    transport.sendto(pkt.DataAckPkt(), addr)
    Logger.data_received(sensors.get_sensor_id(addr), packet.timestamp, False, packet.payload)


@manager.receive(PacketCode.CHECK_ALIVE_RESPONSE)
def check_alive_response(
        _: pkt.CheckAliveResponsePkt,
        addr: PacketAddr,
        sensors: SensorManager,
) -> None:
    sensors.mark_alive(addr)
    Logger.reconnected(sensors.get_sensor_id(addr))
