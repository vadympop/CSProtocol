import struct
from typing import ClassVar,  Mapping

from .fields import PayloadField
from ..utils import bytes_to_bits, bits_to_bytes

class PayloadSerializer:
    """Serializer responsible for encoding a sensor payload."""

    type_name: ClassVar[str]
    code: ClassVar[int]
    field_definitions: ClassVar[tuple[PayloadField, ...]]

    def __init__(self) -> None:
        if not getattr(self, "field_definitions", None):
            raise ValueError("Payload serializers must define field_definitions")

        self._fields: tuple[PayloadField, ...] = tuple(self.field_definitions)
        self._required_fields: tuple[str, ...] = tuple(
            name for field in self._fields for name in field.required_names
        )
        self._struct_format = "!" + "".join(field.struct_format for field in self._fields)

    @property
    def fields(self) -> tuple[PayloadField, ...]:
        return self._fields

    @property
    def struct_format(self) -> str:
        return self._struct_format

    @property
    def field_names(self) -> tuple[str, ...]:
        return self._required_fields

    def validate_payload(self, payload: Mapping[str, int]) -> None:
        missing = [name for name in self._required_fields if name not in payload]
        if missing:
            raise KeyError(f"Missing payload values for {missing!r}")

    def encode_payload(self, payload: Mapping[str, int]) -> bytes:
        self.validate_payload(payload)
        packed_values = tuple(field.pack(payload) for field in self._fields)
        return struct.pack(self._struct_format, *packed_values)

    def encode_to_bits(self, payload: Mapping[str, int]) -> str:
        return bytes_to_bits(self.encode_payload(payload))

    def decode_payload(self, payload_bytes: bytes) -> dict[str, int]:
        parsed_fields = struct.unpack(self._struct_format, payload_bytes)
        result: dict[str, int] = {}

        for field, value in zip(self._fields, parsed_fields):
            result.update(field.unpack(value))

        return result

    def decode_from_bits(self, bits: str) -> dict[str, int]:
        return self.decode_payload(bits_to_bytes(bits))
