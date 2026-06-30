def is_raspberry_pi() -> bool:
    """Return True only when running on actual Raspberry Pi hardware."""
    try:
        with open("/proc/device-tree/model") as f:
            return "Raspberry Pi" in f.read()
    except OSError:
        return False


IS_RPI = is_raspberry_pi()
