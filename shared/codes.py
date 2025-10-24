from enum import Enum


class PacketCode(str, Enum):
    SENSOR_REGISTRATION = "0"
    SENSOR_DATA = "1"
    DATA_ACK = "20"
    REGISTRATION_ACK = "21"
    CHECK_ALIVE = "30"
    CHECK_ALIVE_RESPONSE = "31"
    INVALID_TOKEN = "40"

    GLOBAL = "*"