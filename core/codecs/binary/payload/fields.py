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

    @property
    @abstractmethod
    def decimals_multipliers(self) -> tuple[int, ...]:
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
    decimal: int

    @property
    def struct_format(self) -> str:
        return self.format_char

    @property
    def required_names(self) -> tuple[str, ...]:
        return (self.name,)

    @property
    def decimals_multipliers(self) -> tuple[int, ...]:
        multiplier = 10**self.decimal if self.decimal > 0 else 1
        return (multiplier,)

    def pack(self, payload: dict[str, int | float]) -> int:
        if self.name not in payload:
            raise KeyError(f"Missing payload field '{self.name}'")

        return int(payload[self.name] * self.decimals_multipliers[0])

    def unpack(self, value: int) -> dict[str, int | float]:
        result = value / self.decimals_multipliers[0] if self.decimals_multipliers[0] > 0 else int(value)
        return {self.name: result}


@dataclass(frozen=True)
class CombinedPayloadField(PayloadField):
    names: tuple[str, ...]
    bits: tuple[int, ...]
    decimals: tuple[int, ...]

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

    @property
    def decimals_multipliers(self) -> tuple[int, ...]:
        return tuple((10**decimal if decimal > 0 else 1) for decimal in self.decimals)

    def pack(self, payload: dict[str, int | float]) -> int:
        filtered_payload = {k: v for k, v in payload.items() if k in self.required_names}
        payload = {
            k: int(v*multiplier)
            for [k, v], multiplier in zip(filtered_payload.items(), self.decimals_multipliers)
        }
        return compose_combined_bits(payload, list(self.names), list(self.bits))

    def unpack(self, value: int) -> dict[str, int | float]:
        result = parse_combined_bits(value, list(self.names), list(self.bits))
        return self._format_after_unpacking(result)

    def _format_after_unpacking(self, data: dict[str, int | float]) -> dict[str, int | float]:
        for [k, v], multiplier in zip(data.items(), self.decimals_multipliers):
            if multiplier == 1:
                data[k] = int(v)
            else:
                data[k] = v / multiplier

        return data
