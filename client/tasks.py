import time
from typing import Any

from client.utils import generate_sensor_value

from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.transport import TransportWrapper


def send_data(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    server_addr: PacketAddr = storage["server_addr"]
    sensor_conf: dict = storage["configuration"]
    token: int = storage["token"]

    if token is not None:
        generated_payload = {
            x[0]: generate_sensor_value(*x[1:]) for x in sensor_conf["fields"]
        }
        transport.sendto(pkt.SensorDataPkt(token=token, payload=generated_payload), server_addr)
        storage["data_sent_at"] = time.time()
        storage["is_data_ack"] = False


def check_data_ack(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    if storage["data_sent_at"] is not None:
        if not storage["is_data_ack"] and time.time() - storage["data_sent_at"] > 1:
            Logger.log_debug(f"Data ack timed out, last packet was resent")
            transport.resend_last(PacketCode.SENSOR_DATA)
