from ..consts import INT_TO_SENSOR_TYPE
from ..payload.structure import get_serializer_by_code
from ..utils import bits_to_bytes


def int_decoder(bits: str, _) -> int:
    return int(bits, 2)


def sensor_type_decoder(bits: str, _) -> str:
    int_value = int(bits, 2)
    return INT_TO_SENSOR_TYPE[int_value]


def payload_decoder(bits: str, data: dict) -> dict:
    length = data["length"]
    if len(bits) > length:
        bits = bits[:length]

    serializer = get_serializer_by_code(data["sensor_type"])
    payload_bytes = bits_to_bytes(bits)
    return serializer.decode_payload(payload_bytes)