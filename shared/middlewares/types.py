from asyncio import DatagramTransport
from typing import Callable, Any

from shared.handlers.types import PacketAddr
from shared.packet import Packet

NextMiddlewareType = Callable[[Packet, PacketAddr, DatagramTransport], Any]
MiddlewareType = Callable[[NextMiddlewareType, Packet, PacketAddr, DatagramTransport], Any],
