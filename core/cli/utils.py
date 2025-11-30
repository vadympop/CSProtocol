import sys

from client.consts import DEFAULT_SERVER_ADDR, DEFAULT_SENSOR_IP
from core.configs.sensors_config import SENSORS_CONFIGURATION


def has_debug_flag() -> bool:
    if "--debug" not in sys.argv:
        return False

    index = sys.argv.index("--debug")
    if (index + 1) < len(sys.argv):
        value = sys.argv[index + 1].lower()
        return value == "true"

    return True  # if after debug no value specified, return default - True


def prompt_ip(prompt: str, default: str) -> str:
    return input(f"{prompt} [{default}]: ").strip() or default


def prompt_port(prompt: str, default: int) -> int:
    while True:
        value = input(f"{prompt} [{default}]: ").strip()
        if not value:
            return default

        if value.isdigit() and 0 < int(value) < 65536:
            return int(value)

        print("Port must be an integer between 1 and 65535.")


def prompt_yes_no(prompt: str, default: bool = True) -> bool:
    default_label = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} [{default_label}]: ").strip().lower()
        if not value:
            return default

        if value in {"y", "yes"}:
            return True

        if value in {"n", "no"}:
            return False

        print("Please answer with 'y' or 'n'.")


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

