import asyncio
import contextlib
import functools
import socket

from core.cli.base import ShutdownCallbackType
from core.types import RemoteAddr
from core.protocol import CSProtocol
from core.logger import Logger
from core.cli.utils import has_debug_flag

from .cli import ServerCLI
from .handlers import manager as handlers_manager


Logger.set_config(debug=has_debug_flag())


async def start_server(on_shutdown: ShutdownCallbackType, cli: ServerCLI, local_addr: RemoteAddr) -> None:
    loop = asyncio.get_running_loop()

    try:
        transport, _ = await loop.create_datagram_endpoint(
            lambda: CSProtocol(handlers_manager, on_shutdown),
            local_addr=local_addr
        )
    except socket.gaierror:
        Logger.log_debug(f"Could not connect to {local_addr[0]}:{local_addr[1]}")
        return

    cli.init(
        transport=transport,
        storage=handlers_manager.storage,
        get_sensors=lambda: handlers_manager.sensors.all_sensors(),  # sensors never be None if in manager server_mode=True
        get_address=lambda: transport.get_extra_info("sockname"),
    )


async def main() -> None:
    shutdown_event = asyncio.Event()

    def _request_shutdown() -> None:
        if not shutdown_event.is_set():
            shutdown_event.set()

    start_hook = functools.partial(start_server, _request_shutdown)
    cli = ServerCLI(start_hook=start_hook, shutdown_callback=_request_shutdown)
    cli_task = asyncio.create_task(cli.run())

    try:
        await shutdown_event.wait()
    finally:
        cli_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cli_task

        if (transport := cli.get_transport()) is not None and not transport.is_closing():
            transport.close()


if __name__ == "__main__":
    asyncio.run(main())
