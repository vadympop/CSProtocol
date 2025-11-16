import time
import ujson as json

from asyncio import DatagramTransport
from typing import Any

from shared.codes import PacketCode
from shared.types import PacketAddr
from shared.logger import Logger
from shared.packets import Packet


class TransportWrapper:
    def __init__(self, transport: DatagramTransport) -> None:
        self._transport: DatagramTransport = transport
        self._last_packets: dict[PacketCode, dict[str, Any]] = {}

    def sendto(self, packet: Packet, addr: PacketAddr, *, force_invalid_crc: bool = False) -> None:
        Logger.log_debug(f"Packet {packet.to_dict()} sent to {addr}")
        packet_bytes = packet.to_bytes()

        if force_invalid_crc:
            payload = json.loads(packet_bytes.decode("utf-8"))
            payload["crc"] = (payload["crc"] + 1) & 0xFFFFFFFF
            packet_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        self._transport.sendto(packet_bytes, addr)
        self._last_packets[packet.code] = {"packet": packet, "addr": addr, "time": time.time()}

    def get_last_overall(self) -> tuple[Packet, PacketAddr]:
        sorted_records = sorted(self._last_packets.values(), key=lambda x: x["time"], reverse=True)
        return sorted_records[0]["packet"], sorted_records[0]["addr"]

    def resend_last(self, code: PacketCode = None) -> None:
        if code is None:
            last_record = self.get_last_overall()
            self.sendto(last_record[0], last_record[1])
            return

        if code not in self._last_packets:
            return

        found_record = self._last_packets[code]
        self.sendto(found_record["packet"], found_record["addr"])
