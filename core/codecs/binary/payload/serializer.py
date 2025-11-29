from typing import ClassVar
from .fields import PayloadField


class PayloadSerializer:
    """Serializer responsible for encoding a sensor payload."""

    type_name: ClassVar[str]
    code: ClassVar[int]
    field_definitions: ClassVar[tuple[PayloadField, ...]]

    def __init__(self) -> None:
        if not getattr(self, "field_definitions", None):
            raise ValueError("Payload serializers must define field_definitions")

        self._fields: tuple[PayloadField, ...] = tuple(self.field_definitions)
        self._required_fields: tuple[str, ...] = tuple(field.name for field in self._fields)

    @property
    def fields(self) -> tuple[PayloadField, ...]:
        return self._fields

    @property
    def field_names(self) -> tuple[str, ...]:
        return self._required_fields

    def validate_payload(self, payload: dict[str, int]) -> None:
        missing = [name for name in self._required_fields if name not in payload]
        if missing:
            raise KeyError(f"Missing payload values for {missing!r}")

    def encode_to_bits(self, payload: dict[str, int | float]) -> str:
        self.validate_payload(payload)

        return "".join([field.pack(payload) for field in self._fields])

    def decode_from_bits(self, payload_bits: str) -> dict[str, int | float]:
        result: dict[str, int] = {}
        offset = 0
        for field in self._fields:
            header_bits = payload_bits[offset:offset + field.header_size]
            offset += field.header_size

            body_size = field.get_body_size(header_bits)
            field_result = field.unpack(payload_bits[offset:offset + body_size])
            offset += body_size

            result.update(field_result)

        return result
