from typing import Callable, Any, Dict

from shared.packets import Packet

NextMiddlewareType = Callable[[Packet, Dict[str, Any]], Any]
MiddlewareType = Callable[[NextMiddlewareType, Packet, Dict[str, Any]], Any]
