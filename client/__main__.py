import asyncio
from asyncio import DatagramTransport

from .server import SensorProtocol
from .handlers import manager as main_handlers_manager


SENSORS_CONFIGURATION = [
    {
        "port": 5001,
        "sensor_type": "TEMP",
        "fields": [
            ("temperature", -50, 60, 1), # field_name, min, max, zeros after comma
            ("humidity", 0, 100, 1),
            ("dew_point", -50, 60, 1),
            ("pressure", 800, 1100, 2),
        ]
    },
    {
        "port": 5002,
        "sensor_type": "WIND",
        "fields": [
            ("wind_speed", 0, 50, 1),
            ("wind_gust", 0, 70, 1),
            ("wind_direction", 0, 359, 0),
            ("turbulence", 0, 1, 1),
        ]
    },
    {
        "port": 5003,
        "sensor_type": "RAIN",
        "fields": [
            ("rainfall", 0, 500, 1),
            ("soil_moisture", 0, 100, 1),
            ("flood_risk", 0, 3, 0),
            ("rain_duration", 0, 60, 0),
        ]
    },
    {
        "port": 5004,
        "sensor_type": "AIR",
        "fields": [
            ("co2", 300, 5000, 1),
            ("ozone", 0, 500, 1),
            ("air_quality_index", 0, 500, 0)
        ]
    }
]

async def main() -> None:
    loop = asyncio.get_running_loop()
    on_connection_lost = loop.create_future()
    servers: list[DatagramTransport] = []

    for conf in SENSORS_CONFIGURATION:
        manager = main_handlers_manager.copy(storage={"configuration": conf, "server_addr": ("127.0.0.1", 5000)})
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SensorProtocol(manager, on_connection_lost),
            remote_addr=('127.0.0.1', conf["port"])
        )
        servers.append(transport)

    try:
        await on_connection_lost
    finally:
        for transport in servers:
            transport.close()


if __name__ == "__main__":
    asyncio.run(main())
