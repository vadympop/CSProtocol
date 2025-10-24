from asyncio import DatagramTransport
from typing import Callable, Any, Union

from shared.middlewares.base import BaseMiddleware
from shared.packet import Packet

NextMiddlewareType = Callable[[Packet, DatagramTransport], Any]
MiddlewareType = Union[
    BaseMiddleware,
    Callable[[NextMiddlewareType, Packet, DatagramTransport], Any],
]
