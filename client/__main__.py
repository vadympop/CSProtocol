import asyncio
import contextlib
from asyncio import DatagramTransport

from shared.logger import Logger
from shared.protocol import CSProtocol
from shared.cli.utils import prompt_ip, prompt_port, prompt_yes_no

from .consts import DEFAULT_SERVER_ADDR, SENSORS_CONFIGURATION, DEFAULT_SENSOR_IP
from .cli import ClientCLI, SensorRuntime
from .handlers import manager as main_handlers_manager

Logger.set_config(debug=True)


def configure_sensors() -> tuple[tuple[str, int], list[dict]]:
    server_ip = prompt_ip("Enter server IP", DEFAULT_SERVER_ADDR[0])
    server_port = prompt_port("Enter server port", DEFAULT_SERVER_ADDR[1])

    configured_sensors: list[dict] = []

    for template in SENSORS_CONFIGURATION:
        enable = prompt_yes_no(f"Enable sensor {template['sensor_type']}?", True)
        if not enable:
            continue

        sensor_ip = prompt_ip(
            f"Enter local IP for {template['sensor_type']}",
            DEFAULT_SENSOR_IP,
        )
        sensor_port = prompt_port(
            f"Enter local port for {template['sensor_type']}",
            template["default_port"],
        )

        configured_sensors.append(
            {
                "sensor_type": template["sensor_type"],
                "fields": template["fields"],
                "ip": sensor_ip,
                "port": sensor_port,
            }
        )

    return (server_ip, server_port), configured_sensors


async def main() -> None:
    server_addr, configured_sensors = configure_sensors()
    if not configured_sensors:
        print("No sensors enabled. Exiting")
        return

    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()
    transports: list[DatagramTransport] = []
    sensor_runtimes: list[SensorRuntime] = []

    for conf in configured_sensors:
        storage_defaults = {
            "configuration": conf,
            "server_addr": server_addr,
        }
        manager = main_handlers_manager.copy(storage=storage_defaults)

        transport, _ = await loop.create_datagram_endpoint(
            lambda m=manager: CSProtocol(m, on_connection_lost),
            local_addr=(conf["ip"], conf["port"]),
        )

        transports.append(transport)
        sensor_runtimes.append(
            SensorRuntime(
                identifier=conf["sensor_type"],
                local_ip=conf["ip"],
                local_port=conf["port"],
                storage=manager.storage,
            )
        )

    shutdown_event = asyncio.Event()

    def _request_shutdown() -> None:
        if not shutdown_event.is_set():
            shutdown_event.set()

    cli = ClientCLI(sensor_runtimes, _request_shutdown)
    cli_task = asyncio.create_task(cli.run())
    try:
        await shutdown_event.wait()
    finally:
        for transport in transports:
            transport.close()

        await on_connection_lost

        cli_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cli_task


if __name__ == "__main__":
    asyncio.run(main())
