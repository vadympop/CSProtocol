from shared.packets.flags import PacketFlags
from .decoders import int_decoder, payload_decoder
from .encoders import int_encoder
from .segment import BinarySegment

PACKET_STRUCTURE = [
    BinarySegment(4, "code", int_encoder, int_decoder),
    BinarySegment(4, "flags", int_encoder, int_decoder),
    BinarySegment(32, "timestamp", int_encoder, int_decoder),
    BinarySegment(32, "crc", int_encoder, int_decoder),
    BinarySegment(2, "sensor_type", int_encoder, int_decoder, flag=PacketFlags.SENSOR_TYPE),
    BinarySegment(32, "token", int_encoder, int_decoder, flag=PacketFlags.TOKEN),
    BinarySegment(8, "length", None, None, flag=PacketFlags.PAYLOAD),
    BinarySegment(-1, "payload", None, payload_decoder, flag=PacketFlags.PAYLOAD),
]
PAYLOAD_STRUCTURE = { # H - uint16(2 bytes), h - int16, B - uint8(1 byte)
    "TEMP": [
        ("temperature", "h"),
        ("humidity", "H"),
        ("dew_point", "h"),
        ("pressure", "H"),
    ],
    "WIND": [
        ("wind_speed", "H"),
        ("wind_gust", "H"),
        ("wind_direction", "H"),
        ("turbulence", "B"),
    ],
    "RAIN": [
        ("rainfall", "H"),
        ("soil_moisture", "H"),
        (["flood_risk", "rain_duration"], [2, 6]), # 2 and 6 bits
    ],
    "AIR": [
        ("co2", "H"),
        ("ozone", "H"),
        ("air_quality_index", "H"),
    ]
}