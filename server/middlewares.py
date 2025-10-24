from asyncio import DatagramTransport
from typing import Callable, Any

from shared.packet import Packet


def check_token(
    handler: Callable[[Packet, DatagramTransport], Any],
    packet: Packet,
    transport: DatagramTransport,
):
    return handler(packet, transport)


def check_crc(
    handler: Callable[[Packet, DatagramTransport], Any],
    packet: Packet,
    transport: DatagramTransport,
):
    return handler(packet, transport)
