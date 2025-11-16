from typing import Callable, Any, Dict

from core.packets import Packet

NextMiddlewareType = Callable[[Packet, Dict[str, Any]], Any]
MiddlewareType = Callable[[NextMiddlewareType, Packet, Dict[str, Any]], Any]
