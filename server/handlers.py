from typing import Any

from core.packets import packet as pkt
from core.codes import PacketCode
from core.handlers import HandlersManager
from core.types import PacketAddr
from core.logger import Logger
from core.sensors import SensorManager
from core.transport import TransportWrapper

from .utils import generate_sensor_token
from .middlewares import check_token, check_crc, check_unregistered_sensors

manager = HandlersManager(initial_storage={"skip_data_ack_remaining": {}})
manager.middlewares.register(
    [PacketCode.SENSOR_DATA, PacketCode.CHECK_ALIVE_RESPONSE],
    check_unregistered_sensors
) # ~ For all except SENSOR_REGISTRATION
manager.middlewares.register(PacketCode.GLOBAL, check_crc)
manager.middlewares.register(
    [PacketCode.SENSOR_DATA, PacketCode.CHECK_ALIVE_RESPONSE],
    check_token
)  # ~ For all except SENSOR_REGISTRATION


@manager.startup()
def on_startup(sensors: SensorManager) -> None:
    sensors.tasks.start_base_tasks()


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
        storage: dict[str, Any],
        sensors: SensorManager,
) -> None:
    Logger.data_received(
        sensors.get_sensor_id(addr),
        packet.timestamp,
        packet.is_low_battery,
        packet.payload,
    )

    if (pending_skip := storage["skip_data_ack_remaining"].get(addr)) is not None:
        if pending_skip > 0:
            storage["skip_data_ack_remaining"][addr] -= 1
            Logger.log_debug(
                f"Skipping DATA_ACK as requested ({storage['skip_data_ack_remaining'][addr]} remaining)"
            )
            return

    transport.sendto(pkt.DataAckPkt(), addr)


@manager.receive(PacketCode.CHECK_ALIVE_RESPONSE)
def check_alive_response(
        _: pkt.CheckAliveResponsePkt,
        addr: PacketAddr,
        sensors: SensorManager,
) -> None:
    sensors.mark_alive(addr)
    Logger.reconnected(sensors.get_sensor_id(addr))
