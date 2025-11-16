from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class BinarySegment:
    bits_count: int
    field_name: str
    encoder: Callable[[int, "BinarySegment", dict], str]
    decoder: Callable[[str, dict], Any]
    flag: int = field(default=-1, kw_only=True)

    def has_flag(self, flags: int) -> bool:
        if self.flag == -1:
            return True

        return self.flag in flags

    @property
    def is_consume_remains(self) -> bool:
        return self.bits_count == -1
