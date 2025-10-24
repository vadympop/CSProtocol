from abc import ABC, abstractmethod
from asyncio import DatagramTransport
from typing import Any, Callable

from shared.packet import Packet


class BaseMiddleware(ABC):
    """
    Base middleware class
    """

    @abstractmethod
    def __call__(
        self,
        handler: Callable[[Packet, DatagramTransport], Any],
        packet: Packet,
        transport: DatagramTransport,
    ) -> Any:
        """
        Execute middleware

        :param handler: Wrapped handler in middlewares chain
        :param packet: Incoming event (Subclass of :class:`aiogram.types.base.TelegramObject`)
        :return: :class:`Any`
        """
        pass
