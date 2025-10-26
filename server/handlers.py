from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager
from shared.handlers.types import PacketAddr
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
        transport: TransportWrapper
) -> None:
    token = generate_sensor_token()
    manager.sensors.register(addr, packet.sensor_type, token)

    transport.sendto(pkt.RegistrationAckPkt(token=token), addr)


@manager.receive(PacketCode.SENSOR_DATA)
def device_data_receiving(
        packet: pkt.SensorDataPkt,
        addr: PacketAddr,
        transport: TransportWrapper
) -> None:
    transport.sendto(pkt.DataAckPkt(), addr)


@manager.receive(PacketCode.CHECK_ALIVE_RESPONSE)
def check_alive_response(
        _: pkt.CheckAliveResponsePkt,
        addr: PacketAddr,
) -> None:
    manager.sensors.mark_alive(addr)
    print(f"[✓] Sensor {addr} reconnected")
