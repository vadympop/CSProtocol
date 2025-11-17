from typing import TYPE_CHECKING

from ..consts import SENSOR_TYPE_TO_INT
from ..payload.serializer import PayloadSerializer
from ..payload.structure import get_serializer_by_name, get_serializer_by_code
from ..utils import fit_to_str_bits, bytes_to_bits

if TYPE_CHECKING:
    from .segment import BinarySegment

_PAYLOAD_BITS_CACHE_KEY = "__payload_bits_cache__"


def int_encoder(value: int, segment: "BinarySegment", _) -> str:
    return fit_to_str_bits(value, segment.bits_count)


def sensor_type_encoder(value: str, segment: "BinarySegment", _) -> str:
    return fit_to_str_bits(SENSOR_TYPE_TO_INT[value], segment.bits_count)


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

    serializer = _resolve_serializer(packet)
    payload_bytes = serializer.encode_payload(payload)
    bits = bytes_to_bits(payload_bytes)
    packet[_PAYLOAD_BITS_CACHE_KEY] = bits
    return bits


def _resolve_serializer(packet: dict) -> PayloadSerializer:
    if "sensor_type" not in packet:
        raise ValueError("Sensor type is required for encoding the payload")

    sensor_type = packet["sensor_type"]
    if isinstance(sensor_type, str):
        serializer = get_serializer_by_name(sensor_type)
        packet["sensor_type"] = serializer.code
        return serializer

    return get_serializer_by_code(sensor_type)
