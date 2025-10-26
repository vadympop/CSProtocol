import asyncio
from typing import Any

from client.utils import generate_sensor_value
from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers.manager import HandlersManager
from shared.handlers.types import PacketAddr
from shared.transport.manager import TransportWrapper

manager = HandlersManager()


async def send_data(transport: TransportWrapper, addr: PacketAddr, token: int, fields: list[tuple]) -> None:
    while True:
        generated_payload = {
            x[0]: generate_sensor_value(*x[1:]) for x in fields
        }
        transport.sendto(pkt.SensorDataPkt(token=token, payload=generated_payload), addr)

        await asyncio.sleep(10)


@manager.startup()
def on_startup(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    server_addr: PacketAddr = storage["server_addr"]
    sensor_conf: dict = storage["configuration"]

    transport.sendto(
        pkt.SensorRegistrationPkt(sensor_type=sensor_conf["sensor_type"]),
        server_addr
    )

    asyncio.create_task(send_data(transport, server_addr, storage["token"], sensor_conf["fields"]))


@manager.receive(PacketCode.INVALID_CRC)
def handle_invalid_crc(packet: pkt.Packet, transport: TransportWrapper) -> None:
    transport.resend_last()


@manager.receive(PacketCode.DATA_ACK)
def handle_data_ack(packet: pkt.Packet) -> None:
    pass


@manager.receive(PacketCode.REGISTRATION_ACK)
def handle_registration_ack(packet: pkt.RegistrationAckPkt, storage: dict[str, Any]) -> None:
    storage["token"] = packet.token


@manager.receive(PacketCode.CHECK_ALIVE)
def handle_check_alive(
        packet: pkt.CheckAlivePkt,
        addr: PacketAddr,
        transport: TransportWrapper,
        storage: dict[str, Any]
) -> None:
    transport.sendto(pkt.CheckAliveResponsePkt(token=storage["token"]), addr)
