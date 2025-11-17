from typing import Any

from core.handlers.types import CallbackType
from core.types import PacketAddr
from core.logger import Logger
from core.packets import Packet, InvalidTokenPkt, InvalidCrcPkt
from core.sensors import SensorManager
from core.transport import TransportWrapper


def check_token(
    handler: CallbackType,
    packet: Packet,
    data: dict[str, Any]
):
    sensors: SensorManager = data["sensors"]
    transport: TransportWrapper = data["transport"]
    addr: PacketAddr = data["addr"]

    if sensors[addr].token != packet.token:
        transport.sendto(InvalidTokenPkt(), addr)
        Logger.log_debug(f"Invalid token from {sensors.get_sensor_id(addr)}")
        return

    return handler(packet, data)


def check_crc(
    handler: CallbackType,
    packet: Packet,
    data: dict[str, Any]
):
    transport: TransportWrapper = data["transport"]
    addr: PacketAddr = data["addr"]
    sensors: SensorManager = data["sensors"]

    recv_crc = packet.crc
    dict_packet = packet.to_dict()

    recalculated_crc = Packet.calculate_crc(dict_packet)
    if recv_crc != recalculated_crc:
        transport.sendto(InvalidCrcPkt(), addr)
        Logger.invalid_data(sensors.get_sensor_id(addr))

        return

    return handler(packet, data)


def check_unregistered_sensors(
    handler: CallbackType,
    packet: Packet,
    data: dict[str, Any]
):
    addr: PacketAddr = data["addr"]
    sensors: SensorManager = data["sensors"]

    if sensors[addr] is None:
        Logger.log_debug(f"Received data from unregistered sensor {addr}")
        return

    return handler(packet, data)
