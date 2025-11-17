from abc import ABC


class BaseCodec(ABC):
    def decode(self, data: bytes | str) -> dict:
        raise NotImplementedError

    def encode(self, packet: dict) -> bytes:
        raise NotImplementedError
