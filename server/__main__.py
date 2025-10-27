import asyncio
import contextlib

from shared.protocol import CSProtocol
from shared.logger import Logger
from shared.utils.cli import prompt_port, prompt_ip

from .cli import ServerCLI
from .handlers import manager as handlers_manager


Logger.set_config(debug=True)

DEFAULT_SERVER_ADDR = ("127.0.0.1", 5000)


async def main() -> None:
    local_ip = prompt_ip("Enter server IP", DEFAULT_SERVER_ADDR[0])
    local_port = prompt_port("Enter server port", DEFAULT_SERVER_ADDR[1])

    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()

    transport, _ = await loop.create_datagram_endpoint(
        lambda: CSProtocol(handlers_manager, on_connection_lost),
        local_addr=(local_ip, local_port)
    )

    cli = ServerCLI(
        storage=handlers_manager.storage,
        get_sensors=lambda: handlers_manager.sensors.all_sensors(),  # sensors never be None if in manager server_mode=True
        get_address=lambda: transport.get_extra_info("sockname"),
        shutdown_callback=transport.close,
    )

    cli_task = asyncio.create_task(cli.run())

    try:
        await on_connection_lost
    finally:
        cli_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cli_task

        if not transport.is_closing():
            transport.close()


if __name__ == "__main__":
    asyncio.run(main())
