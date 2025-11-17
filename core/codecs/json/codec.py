import ujson as json

from ..base import BaseCodec


class JSONCodec(BaseCodec):
    def decode(self, data: bytes | str) -> dict:
        if isinstance(data, bytes):
            data = data.decode("utf-8")

        try:
            parsed_data = json.loads(data)
        except ValueError:
            raise ValueError("Invalid JSON was provided")

        return parsed_data

    def encode(self, data: dict) -> bytes:
        return json.dumps(data, separators=(",", ":")).encode("utf-8")
