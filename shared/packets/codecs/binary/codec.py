from shared.packets.flags import make_flags
from .segments import PACKET_STRUCTURE
from .utils import bits_to_bytes, bytes_to_bits
from ..base import BaseCodec


class BinaryCodec(BaseCodec):
    def encode(self, packet: dict) -> bytes:
        str_bits = ""
        flags = make_flags(packet)
        for segment in PACKET_STRUCTURE:
            if not segment.has_flag(flags):
                continue

            if (field_value := packet.get(segment.field_name)) is None:
                continue

            str_bits += segment.encoder(field_value, segment, packet)

        if len(str_bits) % 8 != 0:
            str_bits += "0" * (8 - (len(str_bits) % 8))

        return bits_to_bytes(str_bits)

    def decode(self, data: bytes) -> dict:
        result = {"flags": 0}
        bits = bytes_to_bits(data)
        for segment in PACKET_STRUCTURE:
            if not segment.has_flag(result["flags"]):
                continue

            if segment.is_consume_remains:
                result[segment.field_name] = segment.decoder(bits)
                break

            result[segment.field_name] = segment.decoder(bits[:segment.bits_count], result)
            bits = bits[segment.bits_count:]

        return result
