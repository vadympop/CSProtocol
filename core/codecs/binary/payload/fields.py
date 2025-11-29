import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping

from ..utils import fit_to_str_bits, bits_required

@dataclass(frozen=True)
class PayloadField(ABC):
    """Base definition for a field inside a sensor payload"""
    name: str
    decimals: int

    @property
    def header_size(self) -> int:
        return 0

    @property
    def decimals_multiplier(self) -> int:
        return 10**self.decimals

    @abstractmethod
    def get_body_size(self, header_bits: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def pack(self, payload: Mapping[str, int]) -> str:
        raise NotImplementedError

    def unpack(self, value: str) -> dict[str, int | float]:
        int_value = int(value, 2)

        result = int_value / self.decimals_multiplier if self.decimals_multiplier > 0 else int_value
        return {self.name: result}


@dataclass(frozen=True)
class BoundedPayloadField(PayloadField):
    max_value: int

    def get_body_size(self, _ = None) -> int:
        return bits_required(self.max_value * self.decimals_multiplier)

    def pack(self, payload: dict[str, int | float]) -> str:
        if self.name not in payload:
            raise KeyError(f"Missing payload field '{self.name}'")

        packed_value = int(payload[self.name] * self.decimals_multiplier)
        return fit_to_str_bits(packed_value, self.get_body_size())


@dataclass(frozen=True)
class ShiftedDynamicPayloadField(PayloadField):
    max_value: int
    min_value: int

    __header_bits_count: int = 2
    __segmentation_count: int = 4

    @property
    def header_size(self) -> int:
        return self.__header_bits_count

    @property
    def computed_range(self) -> int:
        return self.max_value - self.min_value

    @property
    def bits_segmentation(self) -> list[int]:
        min_bits = bits_required(self.decimals_multiplier)
        max_bits = bits_required(self.computed_range * self.decimals_multiplier)
        segments_step = math.floor((max_bits - min_bits) / self.__segmentation_count)

        return [
            min(min_bits + i * segments_step, max_bits)
            for i in range(self.__segmentation_count)
        ]

    def get_body_size(self, header_bits: str) -> int:
        if len(header_bits) != self.__header_bits_count:
            raise ValueError(f"Header bits count ({len(header_bits)}) does not match")

        index = int(header_bits, 2)
        return self.bits_segmentation[index]

    def pack(self, payload: dict[str, int | float]) -> str:
        if self.name not in payload:
            raise KeyError(f"Missing payload field '{self.name}'")

        shifted_value = payload[self.name] - self.min_value
        packed_value = int(shifted_value * self.decimals_multiplier)
        value_bits_needed = bits_required(packed_value)

        # Choose smallest segment able to hold this value
        segments = self.bits_segmentation
        chosen_bits_segment = next(
            (i for i, x in enumerate(segments) if x >= value_bits_needed),
            len(segments) - 1
        )

        header_bits = fit_to_str_bits(chosen_bits_segment, self.__header_bits_count)
        body = fit_to_str_bits(packed_value, segments[chosen_bits_segment])
        return header_bits + body

    def unpack(self, value: str) -> dict[str, int | float]:
        result = super().unpack(value)
        result[self.name] += self.min_value

        return result
