from asyncio import DatagramTransport
from typing import Callable, Any

from shared.handlers.types import PacketAddr
from shared.packet import Packet


def check_token(
    handler: Callable[[Packet, PacketAddr, DatagramTransport], Any],
    packet: Packet,
    addr: PacketAddr,
    transport: DatagramTransport,
):
    return handler(packet, addr, transport)


def check_crc(
    handler: Callable[[Packet, PacketAddr, DatagramTransport], Any],
    packet: Packet,
    addr: PacketAddr,
    transport: DatagramTransport,
):
    return handler(packet, addr, transport)
