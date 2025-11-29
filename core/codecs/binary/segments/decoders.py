from ..consts import INT_TO_SENSOR_TYPE
from ..payload.structure import get_serializer_by_name


def int_decoder(bits: str, _) -> int:
    return int(bits, 2)


def sensor_type_decoder(bits: str, _) -> str:
    int_value = int(bits, 2)
    return INT_TO_SENSOR_TYPE[int_value]


def payload_decoder(bits: str, data: dict) -> dict:
    length = data["length"]
    if len(bits) > length:
        bits = bits[:length]

    # In upper decoder int sensor type is already converting to string sensor type
    serializer = get_serializer_by_name(data["sensor_type"])
    return serializer.decode_from_bits(bits)