from typing import Any

from shared import packet as pkt
from shared.codes import PacketCode
from shared.handlers import HandlersManager
from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.tasks import BackgroundTasksManager, BackgroundTask
from shared.transport import TransportWrapper

from .tasks import send_data, check_data_ack


manager = HandlersManager(
    initial_storage={
        "is_data_ack": False,
        "data_sent_at": None,
        "token": None,
        "auto_sending": True,
        "break_crc_once": False,
        "check_alive_test": None
    },
    server_mode=False
)


@manager.startup()
def on_startup(transport: TransportWrapper, storage: dict[str, Any]) -> None:
    storage["transport"] = transport  # For sending custom packets in cli

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
def handle_registration_ack(
        packet: pkt.RegistrationAckPkt,
        transport: TransportWrapper,
        storage: dict[str, Any],
        background_tasks: BackgroundTasksManager
) -> None:
    storage["token"] = packet.token
    Logger.log_debug(f"Token was received - {packet.token}")

    background_tasks.add_task(
        "send_data", BackgroundTask(send_data, 10), transport=transport, storage=storage)
    background_tasks.add_task(
        "data_ack", BackgroundTask(check_data_ack, 0.5), transport=transport, storage=storage)


@manager.receive(PacketCode.CHECK_ALIVE)
def handle_check_alive(
        packet: pkt.CheckAlivePkt,
        addr: PacketAddr,
        transport: TransportWrapper,
        storage: dict[str, Any]
) -> None:
    test_state = storage.get("check_alive_test")
    if test_state:
        test_state["attempts"] = test_state.get("attempts", 0) + 1
        if test_state["attempts"] <= 3:
            Logger.log_debug("CHECK_ALIVE ignored due to active test mode")
            return

        Logger.log_debug("CHECK_ALIVE test satisfied, responding now")
        storage["check_alive_test"] = None

    if storage.get("token") is None:
        Logger.log_debug("Ignoring CHECK_ALIVE before registration is complete")
        return

    transport.sendto(pkt.CheckAliveResponsePkt(token=storage["token"]), addr)


@manager.receive(PacketCode.INVALID_CRC)
def handle_invalid_crc(packet: pkt.Packet, transport: TransportWrapper) -> None:
    transport.resend_last()
    Logger.log_debug("Resend last data packet due to invalid CRC")


@manager.receive(PacketCode.INVALID_TOKEN)
def handle_invalid_token(packet: pkt.Packet, background_tasks: BackgroundTasksManager, storage: dict[str, Any]) -> None:
    storage["token"] = None

    # Cancel tasks
    background_tasks.cancel("send_data", "data_ack")

    # Send registration
    manager.call_startup()
