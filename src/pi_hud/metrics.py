"""System metrics via psutil. Cheap enough to call every couple of seconds."""
import socket

import psutil


def hostname() -> str:
    return socket.gethostname().split(".")[0]


def lan_ip() -> str:
    """This machine's LAN IP (no packets sent; falls back to loopback)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.0.1", 80))  # any address works; nothing is sent
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def temp_c() -> float | None:
    """CPU temperature. Reads the thermal zone directly (works on Pi without
    extra deps); falls back to psutil sensors."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except OSError:
        pass
    try:
        temps = psutil.sensors_temperatures()
        for entries in temps.values():
            if entries:
                return round(entries[0].current, 1)
    except (AttributeError, OSError):
        pass
    return None


def snapshot() -> dict:
    return {
        "hostname": hostname(),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "temp_c": temp_c(),
    }


def level(value: float | None, warn: float, danger: float) -> str:
    """Map a metric to a severity level: normal / warning / danger."""
    if value is None:
        return "normal"
    if value >= danger:
        return "danger"
    if value >= warn:
        return "warning"
    return "normal"
