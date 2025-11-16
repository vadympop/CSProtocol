from dataclasses import dataclass, field
from typing import Callable, Any

from shared.packets.flags import PacketFlags


@dataclass
class BinarySegment:
    bits_count: int
    field_name: str
    encoder: Callable[[int, "BinarySegment", dict], str]
    decoder: Callable[[str, dict], Any]
    flag: PacketFlags = field(default=None, kw_only=True)

    def has_flag(self, flags: int | PacketFlags) -> bool:
        if self.flag is None:
            return True

        resolved_flags = PacketFlags(flags)
        return bool(resolved_flags & self.flag)

    @property
    def is_consume_remains(self) -> bool:
        return self.bits_count == -1
