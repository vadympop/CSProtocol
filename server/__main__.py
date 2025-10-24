import asyncio

from server.server import CSProtocol
from .handlers import manager as handlers_manager


async def main() -> None:
    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: CSProtocol(handlers_manager, on_connection_lost),
        remote_addr=('127.0.0.1', 9999)
    )

    try:
        await on_connection_lost
    finally:
        transport.close()


if __name__ == "__main__":
    asyncio.run(main())
