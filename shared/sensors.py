import time
from dataclasses import dataclass
from typing import Dict

from shared.handlers.types import PacketAddr


@dataclass
class SensorInfo:
    addr: PacketAddr
    sensor_type: str
    last_seen: float
    token: int
    alive: bool = True


class SensorManager:
    def __init__(self, timeout: float = 15.0) -> None:
        self._sensors: Dict[PacketAddr, SensorInfo] = {}
        self.timeout = timeout

    def __getitem__(self, addr: PacketAddr) -> SensorInfo | None:
        return self._sensors.get(addr)

    def register(self, addr: PacketAddr, sensor_type: str, token: int) -> None:
        if addr not in self._sensors:
            print(f"[+] Registered sensor {sensor_type} @ {addr}")

        found_sensor = next((x for x in self._sensors.values() if x.sensor_type == sensor_type), None)
        if found_sensor:
            print("Sensor {sensor_type} already registered")
            return

        self._sensors[addr] = SensorInfo(addr, sensor_type, time.time(), token, True)

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
                # Send first check alive packet and wait for response 1sec
                # If response doesnt come start tasks:
                # 1. Every 10sec print DISCONNECTED msg
                # 2. Every 5sec send check alive packet max 10 attempts
                print(f"[x] Sensor {s.addr} timed out (inactive)")

    def all_sensors(self) -> list[SensorInfo]:
        return list(self._sensors.values())

    def alive_sensors(self) -> list[SensorInfo]:
        return [s for s in self._sensors.values() if s.alive]
