"""Raspberry Pi power/throttle monitoring via `vcgencmd get_throttled`.

The command returns e.g. `throttled=0x50005`. Bit meanings:
  bit 0  undervoltage now          bit 16 undervoltage has occurred
  bit 1  arm frequency capped now   bit 17 arm freq capping has occurred
  bit 2  currently throttled        bit 18 throttling has occurred
"""
import shutil
import subprocess

_BITS = {
    "undervoltage_now": 0,
    "frequency_capped_now": 1,
    "throttled_now": 2,
    "undervoltage_occurred": 16,
    "frequency_capped_occurred": 17,
    "throttled_occurred": 18,
}


def parse(raw: str) -> dict:
    """Parse a `throttled=0x...` string (or bare hex) into flag ints."""
    value = raw.strip()
    if "=" in value:
        value = value.split("=", 1)[1]
    bits = int(value, 16)
    return {name: (bits >> shift) & 1 for name, shift in _BITS.items()}


def read() -> tuple[dict, str] | None:
    """Run vcgencmd. Returns (flags, raw) or None if unavailable (non-Pi)."""
    if not shutil.which("vcgencmd"):
        return None
    try:
        raw = subprocess.check_output(
            ["vcgencmd", "get_throttled"], text=True, timeout=5).strip()
    except (subprocess.SubprocessError, OSError):
        return None
    return parse(raw), raw


def has_warning(flags: dict) -> bool:
    """Any active or historical undervoltage/throttle condition worth logging."""
    return any(flags.values())


def is_active(flags: dict) -> bool:
    """A *currently* active undervoltage or throttle (danger-level)."""
    return bool(flags["undervoltage_now"] or flags["throttled_now"])
