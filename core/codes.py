from enum import Enum


class PacketCode(str, Enum):
    SENSOR_REGISTRATION = "0"
    SENSOR_DATA = "1"
    CHECK_ALIVE_RESPONSE = "2"
    REGISTRATION_ACK = "5"
    DATA_ACK = "6"
    CHECK_ALIVE = "7"
    INVALID_PKT = "13"
    INVALID_TOKEN = "14"
    INVALID_CRC = "15"
    # < 5 - sensor codes
    # >= 5 & < 10 - server codes
    # >= 10 - error codes

    GLOBAL = "*"