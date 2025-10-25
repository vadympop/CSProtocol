from asyncio import DatagramTransport
from typing import Callable, Any, Dict

from shared.packet import Packet

PacketAddr = tuple[str, int]
CallbackType = Callable[[Packet, Dict[str, Any]], Any]
StartupCallbackType = Callable[[DatagramTransport], Any]
