import secrets


def generate_sensor_token() -> int:
    token_bytes = secrets.token_bytes(4)
    return int.from_bytes(token_bytes, "big")
