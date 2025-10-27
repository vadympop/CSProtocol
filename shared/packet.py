import contextlib
import datetime
import functools
import zlib

import ujson as json

from abc import ABC
from dataclasses import dataclass, asdict, field, fields
from typing import Type, Dict, Callable, TypeVar, Any

from shared.codes import PacketCode


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
        data_in_dict["timestamp"] = data_in_dict["timestamp"].timestamp()

        return data_in_dict

    def to_bytes(self) -> bytes:
        data_in_dict = self.to_dict()

        data_in_dict.pop("crc")
        json_bytes = json.dumps(data_in_dict, separators=(",", ":")).encode("utf-8")

        self.crc = zlib.crc32(json_bytes) & 0xFFFFFFFF
        data_in_dict["crc"] = self.crc

        return json.dumps(data_in_dict, separators=(",", ":")).encode("utf-8")

    @classmethod
    def parse_timestamp(cls, payload: dict) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(payload["timestamp"])

    @classmethod
    def validate(cls, data: dict) -> bool:
        if not all(k.name in data for k in fields(cls)):
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

    @staticmethod
    def from_any_payload(data: bytes | str) -> "Packet":
        if not data:
            raise ValueError("No data received")

        if isinstance(data, bytes):
            data = data.decode("utf-8")

        try:
            parsed_data = json.loads(data)
        except ValueError:
            raise ValueError("Invalid JSON was provided")

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
    __CODE__ = PacketCode.SENSOR_DATA

    payload: dict
    token: int

    @classmethod
    @validate_payload
    def from_payload(cls: Type["SensorDataPkt"], payload: dict) -> "SensorDataPkt":
        return cls(
            payload=payload["payload"],
            token=payload["token"],
            crc=payload["crc"],
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
