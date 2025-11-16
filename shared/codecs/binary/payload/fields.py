from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping

from ..consts import BITS_COUNT_TO_STRUCT
from ..utils import  compose_combined_bits, parse_combined_bits

class PayloadField(ABC):
    """Base definition for a field inside a sensor payload"""

    @property
    @abstractmethod
    def struct_format(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def required_names(self) -> tuple[str, ...]:
        raise NotImplementedError

    @abstractmethod
    def pack(self, payload: Mapping[str, int]) -> int:
        raise NotImplementedError

    @abstractmethod
    def unpack(self, value: int) -> dict[str, int]:
        raise NotImplementedError


@dataclass(frozen=True)
class ScalarPayloadField(PayloadField):
    name: str
    format_char: str

    @property
    def struct_format(self) -> str:
        return self.format_char

    @property
    def required_names(self) -> tuple[str, ...]:
        return (self.name,)

    def pack(self, payload: Mapping[str, int]) -> int:
        if self.name not in payload:
            raise KeyError(f"Missing payload field '{self.name}'")

        return payload[self.name]

    def unpack(self, value: int) -> dict[str, int]:
        return {self.name: value}


@dataclass(frozen=True)
class CombinedPayloadField(PayloadField):
    names: tuple[str, ...]
    bits: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.names) != len(self.bits):
            raise ValueError("Combined payload field names and bits must align")
        bits_sum = sum(self.bits)
        if bits_sum not in BITS_COUNT_TO_STRUCT:
            raise ValueError("Invalid combined field bits sum")

    @property
    def struct_format(self) -> str:
        return BITS_COUNT_TO_STRUCT[sum(self.bits)]

    @property
    def required_names(self) -> tuple[str, ...]:
        return self.names

    def pack(self, payload: Mapping[str, int]) -> int:
        return compose_combined_bits(payload, list(self.names), list(self.bits))

    def unpack(self, value: int) -> dict[str, int]:
        return parse_combined_bits(value, list(self.names), list(self.bits))
