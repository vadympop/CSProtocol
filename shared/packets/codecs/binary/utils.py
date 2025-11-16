from .segments import PAYLOAD_STRUCTURE
from .segments.consts import BITS_COUNT_TO_STRUCT


def bits_to_bytes(bits: str) -> bytes:
    bits = list(map(lambda x: int(x), bits))
    while len(bits) % 8 != 0:
        bits.append(0)

    value = 0
    for b in bits:
        value = (value << 1) | b

    length = len(bits) // 8
    return value.to_bytes(length, "big")


def parse_combined_bits(value: int, names: list[str], bits: list[int]) -> dict:
    total_bits = sum(bits)
    if total_bits % 8 != 0:
        raise ValueError("Total bits must be divisible by 8")

    result = {}
    shift = total_bits
    for name, bit_size in zip(names, bits):
        shift -= bit_size
        mask = (1 << bit_size) - 1
        field_value = (value >> shift) & mask
        result[name] = field_value

    return result


def fit_to_bits(value: int, n: int) -> int:
    return value & ((1 << n) - 1)


def fit_to_str_bits(value: int, n: int) -> str:
    return bin(fit_to_bits(value, n))[2:].zfill(n)


def generate_struct_format(sensor_type: str) -> str:
    result = "!"
    for field in PAYLOAD_STRUCTURE[sensor_type]:
        if isinstance(field[0], str):
            result += field[1]
        elif isinstance(field[0], list):
            bits_sum = sum(field[1])
            if bits_sum not in BITS_COUNT_TO_STRUCT:
                raise ValueError("Invalid combined field's bits sum")

            result += BITS_COUNT_TO_STRUCT[bits_sum]

    return result
