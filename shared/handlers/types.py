from asyncio import DatagramTransport
from typing import Callable, Any

from shared.packet import Packet

CallbackType = Callable[[Packet, DatagramTransport], Any]
StartupCallbackType = Callable[[DatagramTransport], Any]
