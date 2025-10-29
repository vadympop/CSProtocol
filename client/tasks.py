import asyncio
import time
from typing import Any

from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers import HandlersManager
from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.transport import TransportWrapper

from .utils import generate_sensor_payload


def send_data(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    if not storage["auto_sending"]:
        return

    server_addr: PacketAddr = storage["server_addr"]
    sensor_conf: dict = storage["configuration"]
    token: int | None = storage["token"]

    if token is None:
        return

    generated_payload = generate_sensor_payload(sensor_conf["fields"])

    storage["data_sent_at"] = time.time()
    storage["is_data_ack"] = False

    transport.sendto(pkt.SensorDataPkt(token=token, payload=generated_payload), server_addr)


def check_data_ack(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    if storage["data_sent_at"] is not None:
        if not storage["is_data_ack"] and time.time() - storage["data_sent_at"] > 1:
            Logger.log_debug(f"Data ack timed out, last packet was resent")
            transport.resend_last(PacketCode.SENSOR_DATA)


async def check_register_ack(manager: HandlersManager) -> None:
    while True:
        storage: dict[str, Any] = manager.storage
        if storage["register_sent_at"] is not None:
            if not storage["is_register_ack"] and time.time() - storage["register_sent_at"] > 1:
                Logger.log_debug(f"Register ack timed out, do registration again")

                # Sends registration
                manager.call_startup()
                break

        await asyncio.sleep(0.5)
