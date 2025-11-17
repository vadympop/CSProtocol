import contextlib
import datetime
import functools
import zlib

from abc import ABC
from dataclasses import dataclass, asdict, field, fields
from typing import Type, Dict, Callable, TypeVar, Any, ClassVar

from core.codes import PacketCode
from .flags import PacketFlags, extract_flags
from ..codecs.base import BaseCodec
from ..codecs.binary.codec import BinaryCodec

_PACKET_REGISTRY: Dict[PacketCode, Type["Packet"]] = {}
PacketT = TypeVar("PacketT", bound="Packet")


def register_packet(cls: Type["Packet"]) -> Type["Packet"]:
    _PACKET_REGISTRY[cls.__CODE__] = cls
    return cls


def validate_payload(func: Callable[..., PacketT]) -> Callable[..., PacketT]:

    @functools.wraps(func)
    def wrapper(cls: Type[PacketT], payload: dict, *args, **kwargs) -> PacketT:
        if not cls.validate(payload):
            raise ValueError(f"Invalid payload for {cls.__name__}: {payload!r}")
        return func(cls, payload, *args, **kwargs)

    return wrapper


@dataclass(kw_only=True)
class Packet(ABC):
    __CODE__ = PacketCode.GLOBAL  # Just placeholder
    __required_fields__ = ()
    _codec: ClassVar[BaseCodec] = BinaryCodec()

    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    code: PacketCode = field(init=False)
    crc: int = None

    def __post_init__(self):
        if not hasattr(self, "__CODE__") or self.__CODE__ == PacketCode.GLOBAL:
            raise TypeError(f"{self.__class__.__name__} missing CODE attribute")

        self.code = self.__CODE__

    def to_dict(self) -> dict[str, Any]:
        data_in_dict = asdict(self)
        data_in_dict["code"] = int(data_in_dict["code"])
        data_in_dict["timestamp"] = int(data_in_dict["timestamp"].timestamp())
        data_in_dict["length"] = 0
        data_in_dict["flags"] = extract_flags(data_in_dict)

        return data_in_dict

    def to_bytes(self) -> bytes:
        data_in_dict = self.to_dict()

        self.crc = self.calculate_crc(data_in_dict)
        data_in_dict["crc"] = self.crc

        return self.encode_dict(data_in_dict)

    @classmethod
    def encode_dict(cls, payload: dict[str, Any]) -> bytes:
        return cls._codec.encode(dict(payload))

    @classmethod
    def decode_dict(cls, data: bytes) -> dict[str, Any]:
        return cls._codec.decode(data)

    @classmethod
    def calculate_crc(cls, packet_dict: dict[str, Any]) -> int:
        crc_payload = dict(packet_dict)
        crc_payload.pop("crc", None)
        encoded = cls._codec.encode(crc_payload)
        return zlib.crc32(encoded) & 0xFFFFFFFF

    @classmethod
    def parse_timestamp(cls, payload: dict) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(payload["timestamp"])

    @classmethod
    def validate(cls, data: dict) -> bool:
        all_fields = map(lambda x: x.name, fields(cls))
        required_fields = all_fields if not cls.__required_fields__ else cls.__required_fields__
        if not all(k in data for k in required_fields):
            return False

        with contextlib.suppress(ValueError):
            PacketCode(str(data["code"]))
            cls.parse_timestamp(data)
            return True

        return False

    @classmethod
    @validate_payload
    def from_payload(cls: Type["Packet"], payload: dict) -> "Packet":
        return cls(timestamp=cls.parse_timestamp(payload), crc=payload["crc"])

    @classmethod
    def from_any_payload(cls, data: bytes | str) -> "Packet":
        if not data:
            raise ValueError("No data received")

        parsed_data = cls.decode_dict(data)
        if "flags" in parsed_data:
            parsed_data["flags"] = PacketFlags(parsed_data["flags"])

        code = PacketCode(str(parsed_data["code"]))
        packet_cls = _PACKET_REGISTRY.get(code)
        if not packet_cls:
            raise ValueError(f"Unsupported packet code: {code.name}")

        return packet_cls.from_payload(parsed_data)


@register_packet
@dataclass
class SensorRegistrationPkt(Packet):
    __CODE__ = PacketCode.SENSOR_REGISTRATION

    sensor_type: str

    @classmethod
    @validate_payload
    def from_payload(cls: Type["SensorRegistrationPkt"], payload: dict) -> "SensorRegistrationPkt":
        return cls(
            sensor_type=payload["sensor_type"],
            crc=payload["crc"],
            timestamp=cls.parse_timestamp(payload),
        )


@register_packet
@dataclass
class SensorDataPkt(Packet):
    __required_fields__ = ("sensor_type", "payload", "token", "timestamp", "crc", "code")
    __CODE__ = PacketCode.SENSOR_DATA

    sensor_type: str
    payload: dict
    token: int
    is_low_battery: bool = False

    @classmethod
    @validate_payload
    def from_payload(cls: Type["SensorDataPkt"], payload: dict) -> "SensorDataPkt":
        return cls(
            payload=payload["payload"],
            token=payload["token"],
            crc=payload["crc"],
            sensor_type=payload["sensor_type"],
            is_low_battery=bool(payload["flags"] & PacketFlags.LOW_BATTERY),
            timestamp=cls.parse_timestamp(payload),
        )


@register_packet
@dataclass
class DataAckPkt(Packet):
    __CODE__ = PacketCode.DATA_ACK


@register_packet
@dataclass
class RegistrationAckPkt(Packet):
    __CODE__ = PacketCode.REGISTRATION_ACK

    token: int

    @classmethod
    @validate_payload
    def from_payload(cls: Type["RegistrationAckPkt"], payload: dict) -> "RegistrationAckPkt":
        return cls(
            token=payload["token"],
            crc=payload["crc"],
            timestamp=cls.parse_timestamp(payload),
        )


@register_packet
@dataclass
class CheckAlivePkt(Packet):
    __CODE__ = PacketCode.CHECK_ALIVE


@register_packet
@dataclass
class CheckAliveResponsePkt(Packet):
    __CODE__ = PacketCode.CHECK_ALIVE_RESPONSE

    token: int

    @classmethod
    @validate_payload
    def from_payload(cls: Type["CheckAliveResponsePkt"], payload: dict) -> "CheckAliveResponsePkt":
        return cls(
            token=payload["token"],
            crc=payload["crc"],
            timestamp=cls.parse_timestamp(payload),
        )


@register_packet
@dataclass
class InvalidTokenPkt(Packet):
    __CODE__ = PacketCode.INVALID_TOKEN


@register_packet
@dataclass
class InvalidCrcPkt(Packet):
    __CODE__ = PacketCode.INVALID_CRC


@register_packet
@dataclass
class InvalidPkt(Packet):
    __CODE__ = PacketCode.INVALID_PKT
