import time

from dataclasses import dataclass
from typing import Dict

from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.packet import CheckAlivePkt
from shared.sensors.tasks import SensorsTasksManager
from shared.tasks import TasksManager
from shared.transport.manager import TransportWrapper


@dataclass
class SensorInfo:
    addr: PacketAddr
    sensor_type: str
    last_seen: float
    token: int
    first_check_alive_time: float | None = None
    alive: bool = True
    disconnected: bool = False


class SensorManager:
    def __init__(self, background_tasks: TasksManager) -> None:
        self.tasks = SensorsTasksManager(self, background_tasks)

        self._sensors: Dict[PacketAddr, SensorInfo] = {}
        self._transport: TransportWrapper | None = None

    def init_transport(self, transport: TransportWrapper) -> None:
        self._transport = transport

    def register(self, addr: PacketAddr, sensor_type: str, token: int) -> None:
        found_sensor = next((x for x in self._sensors.values() if x.sensor_type == sensor_type), None)
        if found_sensor:
            print("Sensor {sensor_type} already registered")
            return

        Logger.log_debug(f"Registering sensor {sensor_type} @ {addr}")
        self._sensors[addr] = SensorInfo(addr, sensor_type, time.time(), token, True)

    def unregister(self, addr: PacketAddr) -> None:
        sensor = self._sensors.pop(addr)
        self.tasks.cancel_sensor_tasks(sensor)

        Logger.log_debug(f"UNregister sensor {sensor.sensor_type} @ {addr}")

    def update(self, addr: PacketAddr) -> None:
        if addr in self._sensors:
            self._sensors[addr].last_seen = time.time()
        else:
            Logger.log_debug(f"Unregistered sensor sent data from {addr}")

    def send_check_alive(self, sensor: SensorInfo, first: bool = False) -> None:
        self._transport.sendto(CheckAlivePkt(), sensor.addr)

        if first:
            self._sensors[sensor.addr].first_check_alive_time = time.time()

    def mark_alive(self, addr: PacketAddr) -> None:
        sensor = self._sensors[addr]

        sensor.alive = True
        sensor.disconnected = False

        self.tasks.cancel_sensor_tasks(sensor)

    def get_sensor_id(self, addr: PacketAddr) -> str:
        sensor_info = self._sensors[addr]

        return sensor_info.sensor_type

    def all_sensors(self) -> list[SensorInfo]:
        return list(self._sensors.values())

    def alive_sensors(self) -> list[SensorInfo]:
        return [s for s in self._sensors.values() if s.alive]

    def disconnected_sensors(self) -> list[SensorInfo]:
        return [s for s in self._sensors.values() if s.disconnected]

    def __getitem__(self, addr: PacketAddr) -> SensorInfo | None:
        if addr not in self._sensors:
            return None

        return self._sensors.get(addr)
