import struct
from typing import TYPE_CHECKING

from .consts import SENSOR_TYPES
from .payload_structure import PAYLOAD_STRUCTURE
from ..utils import fit_to_str_bits, generate_struct_format, bytes_to_bits, compose_combined_bits

if TYPE_CHECKING:
    from .segment import BinarySegment

_PAYLOAD_BITS_CACHE_KEY = "__payload_bits_cache__"


def int_encoder(value: int, segment: "BinarySegment", _) -> str:
    return fit_to_str_bits(value, segment.bits_count)


def length_encoder(_, segment: "BinarySegment", packet: dict) -> str:
    payload_bits = _get_payload_bits(packet)
    return fit_to_str_bits(len(payload_bits), segment.bits_count)


def payload_encoder(_, __, packet: dict) -> str:
    return _get_payload_bits(packet)


def _get_payload_bits(packet: dict) -> str:
    cached_bits = packet.get(_PAYLOAD_BITS_CACHE_KEY)
    if cached_bits is not None:
        return cached_bits

    payload = packet.get("payload")
    if payload is None:
        raise ValueError("Packet payload is required for encoding")

    sensor_type = _resolve_sensor_type(packet)
    payload_fields = PAYLOAD_STRUCTURE[sensor_type]
    struct_format = generate_struct_format(sensor_type)
    packed_values = []

    for field in payload_fields:
        field_name = field[0]
        if isinstance(field_name, str):
            if field_name not in payload:
                raise KeyError(f"Missing payload field '{field_name}'")

            packed_values.append(payload[field_name])
        elif isinstance(field_name, list):
            packed_values.append(
                compose_combined_bits(payload, field_name, field[1])
            )

    payload_bytes = struct.pack(struct_format, *packed_values)
    bits = bytes_to_bits(payload_bytes)
    packet[_PAYLOAD_BITS_CACHE_KEY] = bits
    return bits


def _resolve_sensor_type(packet: dict) -> str:
    if "sensor_type" not in packet:
        raise ValueError("Sensor type is required for encoding the payload")

    sensor_type_code = packet["sensor_type"]
    if sensor_type_code not in SENSOR_TYPES:
        raise ValueError("Unknown sensor type code")

    return SENSOR_TYPES[sensor_type_code]
