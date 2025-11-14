import zlib
import ujson as json

from typing import Any

from shared.handlers.types import CallbackType
from shared.types import PacketAddr
from shared.logger import Logger
from shared.packet import Packet, InvalidTokenPkt, InvalidCrcPkt
from shared.sensors import SensorManager
from shared.transport import TransportWrapper


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
    dict_packet.pop("crc")

    recalculated_crc = zlib.crc32(json.dumps(dict_packet, separators=(",", ":")).encode("utf-8")) & 0xFFFFFFFF
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
