import zlib
import ujson as json

from asyncio import DatagramTransport
from typing import Any

from shared.handlers.types import PacketAddr, CallbackType
from shared.packet import Packet, InvalidTokenPkt, InvalidCrcPkt
from shared.sensors import SensorManager


def check_token(
    handler: CallbackType,
    packet: Packet,
    data: dict[str, Any]
):
    sensors: SensorManager = data["sensors"]
    transport: DatagramTransport = data["transport"]
    addr: PacketAddr = data["addr"]

    if sensors[addr].token != packet.token:
        transport.sendto(InvalidTokenPkt().to_bytes(), addr)
        return

    return handler(packet, data)


def check_crc(
    handler: CallbackType,
    packet: Packet,
    data: dict[str, Any]
):
    transport: DatagramTransport = data["transport"]
    addr: PacketAddr = data["addr"]

    recv_crc = packet.crc
    dict_packet = packet.to_dict()
    dict_packet.pop("crc")

    recalculated_crc = zlib.crc32(json.dumps(dict_packet, separators=(",", ":")).encode("utf-8")) & 0xFFFFFFFF
    if not recv_crc == recalculated_crc:
        transport.sendto(InvalidCrcPkt().to_bytes(), addr)
        return

    return handler(packet, data)


def check_unregistered_sensors(
    handler: CallbackType,
    packet: Packet,
    data: dict[str, Any]
):
    return handler(packet, data)
