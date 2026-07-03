"""Config loading. Infrastructure settings live in an INI file (needs a
restart to change); runtime-tunable settings live in the SQLite `settings`
table (see message_store.get_setting)."""
import configparser
import os
from pathlib import Path

# Built-in defaults. The INI file only needs to override what differs, so a
# missing or partial config still boots. These mirror config.example.ini.
DEFAULTS = {
    "app": {"name": "pi-hud", "environment": "production"},
    "api": {"host": "127.0.0.1", "port": "8765", "lan_mode": "false"},
    "database": {"path": "/var/lib/pi-hud/pi-hud.db"},
    "display": {
        "enabled": "true",
        "rotation": "270",
        "x_offset": "24",
        "y_offset": "0",
        "dc_pin": "23",
        "rst_pin": "24",
        "bl_pin": "18",
        "spi_port": "0",
        "spi_cs": "0",
        "spi_speed_hz": "24000000",
        "normal_refresh_seconds": "2",
        "power_refresh_seconds": "10",
    },
    "thresholds": {
        "temp_warning_c": "65",
        "temp_danger_c": "75",
        "cpu_warning_percent": "70",
        "cpu_danger_percent": "85",
        "ram_warning_percent": "70",
        "ram_danger_percent": "85",
    },
    "messages": {
        "default_pinned": "false",
        "max_message_chars": "500",
        "max_metadata_chars": "4096",
    },
}

_SEARCH = [
    os.environ.get("PI_HUD_CONFIG"),
    "/etc/pi-hud/config.ini",
    str(Path(__file__).resolve().parents[2] / "config.example.ini"),
]


class Config:
    def __init__(self, parser: configparser.ConfigParser, path: str | None):
        self._p = parser
        self.path = path

    def get(self, section: str, key: str) -> str:
        return self._p.get(section, key)

    def getint(self, section: str, key: str) -> int:
        return self._p.getint(section, key)

    def getbool(self, section: str, key: str) -> bool:
        return self._p.getboolean(section, key)


def load(path: str | None = None) -> Config:
    parser = configparser.ConfigParser()
    parser.read_dict(DEFAULTS)
    candidates = [path] if path else _SEARCH
    used = None
    for c in candidates:
        if c and Path(c).is_file():
            parser.read(c)
            used = c
            break
    return Config(parser, used)
