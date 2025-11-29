import math


def bits_to_bytes(bits: str) -> bytes:
    bits = list(map(lambda x: int(x), bits))
    while len(bits) % 8 != 0:
        bits.append(0)

    value = 0
    for b in bits:
        value = (value << 1) | b

    length = len(bits) // 8
    return value.to_bytes(length, "big")


def bytes_to_bits(data: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in data)


def bits_required(value: int) -> int:
    return math.ceil(math.log2(value))


def fit_to_bits(value: int, n: int) -> int:
    return value & ((1 << n) - 1)


def fit_to_str_bits(value: int, n: int) -> str:
    return bin(fit_to_bits(value, n))[2:].zfill(n)
