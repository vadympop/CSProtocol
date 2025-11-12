import asyncio
import contextlib
import functools
import socket
from asyncio import DatagramTransport

from shared.logger import Logger
from shared.protocol import CSProtocol
from shared.cli.utils import has_debug_flag

from .cli import ClientCLI, SensorRuntime
from .handlers import manager as main_handlers_manager


Logger.set_config(debug=has_debug_flag())


async def start_server(on_shutdown, cli: ClientCLI, server_addr, configured_sensors) -> None:
    loop = asyncio.get_running_loop()
    transports: list[DatagramTransport] = []
    sensor_runtimes: list[SensorRuntime] = []

    for conf in configured_sensors:
        storage_defaults = {
            "configuration": conf,
            "server_addr": server_addr,
        }
        manager = main_handlers_manager.copy(storage=storage_defaults)

        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda m=manager: CSProtocol(m, on_shutdown),
                local_addr=(conf["ip"], conf["port"]),
            )
        except socket.gaierror:
            Logger.log_debug(f"Could not connect to {conf['ip']}:{conf['port']}")
            return

        transports.append(transport)
        sensor_runtimes.append(
            SensorRuntime(
                identifier=conf["sensor_type"],
                local_ip=conf["ip"],
                local_port=conf["port"],
                storage=manager.storage,
            )
        )

    cli.init(
        sensors=sensor_runtimes,
        transports=transports,
    )


async def main() -> None:
    shutdown_event = asyncio.Event()

    def _request_shutdown() -> None:
        if not shutdown_event.is_set():
            shutdown_event.set()

    start_hook = functools.partial(start_server, _request_shutdown)
    cli = ClientCLI(start_hook, _request_shutdown)
    cli_task = asyncio.create_task(cli.run())
    try:
        await shutdown_event.wait()
    finally:
        cli_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cli_task

        for transport in cli.get_transports():
            transport.close()


if __name__ == "__main__":
    asyncio.run(main())
