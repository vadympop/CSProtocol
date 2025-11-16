import struct

from .payload_structure import PAYLOAD_STRUCTURE
from .consts import SENSOR_TYPES
from ..utils import bits_to_bytes, parse_combined_bits, generate_struct_format


def int_decoder(bits: str, _) -> int:
    return int(bits, 2)


def payload_decoder(bits: str, data: dict) -> dict:
    length = data["length"]
    if len(bits) > length:
        bits = bits[:length]

    payload = bits_to_bytes(bits)
    sensor_type = SENSOR_TYPES[data["sensor_type"]]
    struct_format = generate_struct_format(sensor_type)

    result = {}
    payload_fields: list[tuple] = PAYLOAD_STRUCTURE[sensor_type]
    parsed_fields = struct.unpack(struct_format, payload)
    for i, value in enumerate(parsed_fields):
        field_name = payload_fields[i][0]
        if isinstance(field_name, str):
            result[field_name] = value
        elif isinstance(field_name, list):
            result |= parse_combined_bits(value, field_name, payload_fields[i][1])

    return result
