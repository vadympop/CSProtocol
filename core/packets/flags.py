from enum import IntFlag


class PacketFlags(IntFlag):
    LOW_BATTERY = 1 << 0
    SENSOR_TYPE = 1 << 1
    TOKEN = 1 << 2
    PAYLOAD = 1 << 3


def make_flags(packet: dict) -> int:
    flags = 0
    if "payload" in packet:
        flags |= PacketFlags.PAYLOAD

    if "sensor_type" in packet:
        flags |= PacketFlags.SENSOR_TYPE

    if "token" in packet:
        flags |= PacketFlags.TOKEN

    if packet.get("is_low_battery"):
        flags |= PacketFlags.LOW_BATTERY

    return flags
