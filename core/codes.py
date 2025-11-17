from enum import Enum


class PacketCode(str, Enum):
    SENSOR_REGISTRATION = "0"
    SENSOR_DATA = "1"
    CHECK_ALIVE_RESPONSE = "2"
    REGISTRATION_ACK = "10"
    DATA_ACK = "11"
    CHECK_ALIVE = "12"
    INVALID_PKT = "30"
    INVALID_TOKEN = "29"
    INVALID_CRC = "28"
    # < 10 - sensor codes
    # >= 10 & < 20 - server codes
    # >= 20 - error codes

    GLOBAL = "*"