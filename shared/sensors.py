import asyncio
import time

from asyncio import Task
from dataclasses import dataclass
from typing import Dict

from shared.handlers.types import PacketAddr
from shared.logger import Logger
from shared.packet import CheckAlivePkt
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
    disconnected_task: Task | None = None
    check_alive_task: Task | None = None


class SensorManager:
    def __init__(self, timeout: float = 15.0) -> None:
        self._sensors: Dict[PacketAddr, SensorInfo] = {}
        self.timeout = timeout
        self._transport: TransportWrapper | None = None

    def init_transport(self, transport: TransportWrapper) -> None:
        self._transport = transport

    def register(self, addr: PacketAddr, sensor_type: str, token: int) -> None:
        if addr not in self._sensors:
            print(f"[+] Registered sensor {sensor_type} @ {addr}")

        found_sensor = next((x for x in self._sensors.values() if x.sensor_type == sensor_type), None)
        if found_sensor:
            print("Sensor {sensor_type} already registered")
            return

        self._sensors[addr] = SensorInfo(addr, sensor_type, time.time(), token, True)

    def unregister(self, addr: PacketAddr) -> None:
        self._sensors[addr].check_alive_task.cancel()
        self._sensors[addr].disconnected_task.cancel()

        self._sensors.pop(addr)

    def update(self, addr: PacketAddr) -> None:
        if addr in self._sensors:
            self._sensors[addr].last_seen = time.time()
        else:
            print(f"[?] Unregistered sensor sent data from {addr}")

    def mark_inactive(self) -> None:
        now = time.time()
        for s in self._sensors.values():
            if s.alive and now - s.last_seen > self.timeout:
                s.alive = False

                self.send_check_alive(s, True)
                # Send first check alive packet and wait for response 1sec
                # If response doesnt come start tasks:
                # 1. Every 10sec print DISCONNECTED msg
                # 2. Every 5sec send check alive packet max 10 attempts
                print(f"[x] Sensor {s.addr} timed out (inactive)")

    def mark_disconnected(self) -> None:
        now = time.time()
        for s in self._sensors.values():
            if not s.alive and not s.disconnected and now - s.first_check_alive_time > 1:
                s.disconnected = True
                self.start_disconnected_tasks(s)

    def send_check_alive(self, sensor: SensorInfo, first: bool = False) -> None:
        self._transport.sendto(CheckAlivePkt(), sensor.addr)

        if first:
            self._sensors[sensor.addr].first_check_alive_time = time.time()

    async def disconnected_task(self, sensor: SensorInfo) -> None:
        while True:
            Logger.disconnected(sensor.sensor_type)
            await asyncio.sleep(10)

    async def repeated_check_alive_task(self, sensor: SensorInfo) -> None:
        attempts = 0
        while attempts < 10:
            self.send_check_alive(sensor)
            attempts += 1

            await asyncio.sleep(5)

        # Unregister sensor if sensor doesnt reply and task wasnt cancelled earlier
        self.unregister(sensor.addr)

    def start_disconnected_tasks(self, sensor: SensorInfo) -> None:
        sensor.disconnected_task = asyncio.create_task(self.disconnected_task(sensor))
        sensor.check_alive_task = asyncio.create_task(self.repeated_check_alive_task(sensor))

    def mark_alive(self, addr: PacketAddr) -> None:
        sensor = self._sensors[addr]

        sensor.alive = True
        sensor.disconnected = False

        sensor.check_alive_task.cancel()
        sensor.disconnected_task.cancel()

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
