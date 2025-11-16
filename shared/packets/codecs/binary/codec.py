from shared.packets.flags import make_flags
from .segments import PACKET_STRUCTURE
from .utils import bits_to_bytes
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
        data = {"flags": 0}
        bits = "".join(f"{b:08b}" for b in data)
        for segment in PACKET_STRUCTURE:
            if not segment.has_flag(data["flags"]):
                continue

            if segment.is_consume_remains:
                data[segment.field_name] = segment.decoder(bits)
                break

            data[segment.field_name] = segment.decoder(bits[:segment.bits_count], data)
            bits = bits[segment.bits_count:]

        return data
