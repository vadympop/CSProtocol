import asyncio
import time
from typing import Any

from client.utils import generate_sensor_value
from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager
from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.transport.manager import TransportWrapper

manager = HandlersManager(server_mode=False)


async def send_data(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    server_addr: PacketAddr = storage["server_addr"]
    sensor_conf: dict = storage["configuration"]
    token: int = storage["token"]

    while True:
        if token is not None:
            generated_payload = {
                x[0]: generate_sensor_value(*x[1:]) for x in sensor_conf["fields"]
            }
            transport.sendto(pkt.SensorDataPkt(token=token, payload=generated_payload), server_addr)
            storage["data_sent_at"] = time.time()

        await asyncio.sleep(10)


async def check_data_ack(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    while True:
        if storage["data_sent_at"] is not None:
            if not storage["is_data_ack"] and time.time() - storage["data_sent_at"] > 1:
                Logger.log_debug(f"Data ack timed out, last packet was resent")
                transport.resend_last(PacketCode.SENSOR_DATA)

        await asyncio.sleep(0.5)


@manager.startup()
def on_startup(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    storage["is_data_ack"] = False
    storage["data_sent_at"] = None

    server_addr: PacketAddr = storage["server_addr"]
    sensor_conf: dict = storage["configuration"]

    transport.sendto(
        pkt.SensorRegistrationPkt(sensor_type=sensor_conf["sensor_type"]),
        server_addr
    )


@manager.receive(PacketCode.DATA_ACK)
def handle_data_ack(packet: pkt.Packet, storage: dict[str, Any]) -> None:
    storage["is_data_ack"] = True
    Logger.log_debug("Last data ack received")


@manager.receive(PacketCode.REGISTRATION_ACK)
def handle_registration_ack(packet: pkt.RegistrationAckPkt, transport: TransportWrapper, storage: dict[str, Any]) -> None:
    storage["token"] = packet.token
    Logger.log_debug(f"Token was received - {packet.token}")

    storage["send_data_task"] = asyncio.create_task(send_data(transport, storage))
    storage["data_ack_task"] = asyncio.create_task(check_data_ack(transport, storage))


@manager.receive(PacketCode.CHECK_ALIVE)
def handle_check_alive(
        packet: pkt.CheckAlivePkt,
        addr: PacketAddr,
        transport: TransportWrapper,
        storage: dict[str, Any]
) -> None:
    transport.sendto(pkt.CheckAliveResponsePkt(token=storage["token"]), addr)


@manager.receive(PacketCode.INVALID_CRC)
def handle_invalid_crc(packet: pkt.Packet, transport: TransportWrapper) -> None:
    transport.resend_last()
    Logger.log_debug("Resend last data packet due to invalid CRC")


@manager.receive(PacketCode.INVALID_TOKEN)
def handle_invalid_token(packet: pkt.Packet, storage: dict[str, Any]) -> None:
    storage["token"] = None

    # Cancel tasks
    storage["send_data_task"].cancel()
    storage["data_ack_task"].cancel()

    # Send registration
    manager.call_startup()
