from asyncio import DatagramTransport
from typing import Callable, Any, Union

from shared.handlers.types import PacketAddr
from shared.middlewares.base import BaseMiddleware
from shared.packet import Packet

NextMiddlewareType = Callable[[Packet, PacketAddr, DatagramTransport], Any]
MiddlewareType = Union[
    BaseMiddleware,
    Callable[[NextMiddlewareType, Packet, PacketAddr, DatagramTransport], Any],
]
