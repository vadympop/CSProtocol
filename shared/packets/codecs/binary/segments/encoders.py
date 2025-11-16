from typing import TYPE_CHECKING
from ..utils import fit_to_str_bits

if TYPE_CHECKING:
    from .segment import BinarySegment


def int_encoder(value: int, segment: "BinarySegment", _) -> str:
    return fit_to_str_bits(value, segment.bits_count)
