from asyncio import DatagramTransport
from typing import Callable, Any

from shared.packet import Packet

PacketAddr = tuple[str, int]
CallbackType = Callable[[Packet, PacketAddr, DatagramTransport], Any]
StartupCallbackType = Callable[[DatagramTransport], Any]
