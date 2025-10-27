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
