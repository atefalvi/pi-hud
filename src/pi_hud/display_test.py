"""Hardware triage: drive the panel directly and report each step.

Run on the Pi (stop the service first — it owns the display):

    sudo systemctl stop pi-hud
    sudo PI_HUD_CONFIG=/etc/pi-hud/config.ini \
        /opt/pi-hud/.venv/bin/python -m pi_hud.display_test
    sudo systemctl start pi-hud

Pass --slow to run SPI at 4MHz (rules out signal-integrity problems at 24MHz).
"""
import sys
import time

from . import config


def main():
    cfg = config.load()
    slow = "--slow" in sys.argv
    speed = 4_000_000 if slow else cfg.getint("display", "spi_speed_hz")
    dc = cfg.getint("display", "dc_pin")
    rst = cfg.getint("display", "rst_pin")
    bl = cfg.getint("display", "bl_pin")
    port = cfg.getint("display", "spi_port")
    cs = cfg.getint("display", "spi_cs")

    print(f"config: {cfg.path or 'built-in defaults'}")
    print(f"pins:   DC={dc} RST={rst} BL={bl}  spi={port}.{cs} @ {speed//1_000_000}MHz"
          + ("  [--slow]" if slow else ""))

    try:
        import spidev  # noqa: F401
        import RPi.GPIO  # noqa: F401
        print("libs:   spidev + RPi.GPIO import ok")
    except ImportError as e:
        print(f"FAIL:   hardware library missing: {e}")
        print("        fix: /opt/pi-hud/.venv/bin/pip install spidev RPi.GPIO")
        sys.exit(1)

    from .drivers.st7735s import ST7735S
    try:
        drv = ST7735S(dc=dc, rst=rst, bl=bl, port=port, cs=cs, speed_hz=speed,
                      rotation=cfg.getint("display", "rotation"),
                      x_offset=cfg.getint("display", "x_offset"),
                      y_offset=cfg.getint("display", "y_offset"))
    except Exception as e:
        print(f"FAIL:   driver init: {e}")
        print("        Is SPI enabled? sudo raspi-config -> Interface Options -> SPI")
        sys.exit(1)

    print("init:   ok — cycling solid colors (watch the panel)")
    for name, c in (("red", (255, 0, 0)), ("green", (0, 255, 0)),
                    ("blue", (0, 0, 255)), ("white", (255, 255, 255))):
        print(f"        {name}")
        drv.clear(c)
        time.sleep(1.2)

    from . import renderer
    drv.display(renderer.render_boot())
    print("done:   boot screen left on panel")
    print()
    print("If the panel did NOT change (still static/blank), check wiring:")
    print("  MOSI=GPIO10(pin19) SCLK=GPIO11(pin23) CS=CE0/GPIO8(pin24)")
    print(f"  DC=GPIO{dc} RST=GPIO{rst} BL=GPIO{bl} + 3.3V/GND")
    print("  and retry with --slow. If colors look swapped/inverted, the panel")
    print("  variant may need invert/BGR — report what you see.")
    drv.close()


if __name__ == "__main__":
    main()
