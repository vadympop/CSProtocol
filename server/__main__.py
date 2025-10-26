import asyncio

from server.app import CSProtocol
from shared.logger import Logger
from .handlers import manager as handlers_manager


Logger.set_config(debug=True)

async def main() -> None:
    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: CSProtocol(handlers_manager, on_connection_lost),
        local_addr=('127.0.0.1', 5000)
    )

    try:
        await on_connection_lost
    finally:
        transport.close()


if __name__ == "__main__":
    asyncio.run(main())
