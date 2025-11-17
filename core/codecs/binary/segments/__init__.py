from core.packets.flags import PacketFlags
from .decoders import int_decoder, payload_decoder, sensor_type_decoder
from .encoders import int_encoder, length_encoder, payload_encoder, sensor_type_encoder
from .segment import BinarySegment

PACKET_STRUCTURE = [
    BinarySegment(4, "code", int_encoder, int_decoder),
    BinarySegment(4, "flags", int_encoder, int_decoder),
    BinarySegment(32, "timestamp", int_encoder, int_decoder),
    BinarySegment(32, "crc", int_encoder, int_decoder),
    BinarySegment(2, "sensor_type", sensor_type_encoder, sensor_type_decoder, flag=PacketFlags.SENSOR_TYPE),
    BinarySegment(32, "token", int_encoder, int_decoder, flag=PacketFlags.TOKEN),
    BinarySegment(8, "length", length_encoder, int_decoder, flag=PacketFlags.PAYLOAD),
    BinarySegment(-1, "payload", payload_encoder, payload_decoder, flag=PacketFlags.PAYLOAD),
]
