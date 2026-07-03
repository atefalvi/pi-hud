"""Background loop: renders the current HUD frame and pushes it to the panel
only when it changes, samples metrics, and monitors power. Also exposes
`build_frame()` so the web dashboard can show the exact same image."""
import logging
import threading
import time

from PIL import Image

from . import message_store as store
from . import metrics, power, renderer
from .config import Config

log = logging.getLogger("pi_hud.display")


def _threshold(cfg: Config, key: str) -> float:
    """Runtime override from the settings table, else config.ini default."""
    override = store.get_setting(key)
    if override is not None:
        return float(override)
    return float(cfg.getint("thresholds", key))


def _level_color(level: str):
    return {"normal": renderer.SUCCESS, "warning": renderer.WARNING,
            "danger": renderer.DANGER}[level]


def build_frame(cfg: Config, snap: dict | None = None) -> Image.Image:
    """The image that should currently be on the panel."""
    active = store.active_message()
    count = store.active_count()

    if count > 1:
        groups = [(lbl, cnt, _group_color(gi))
                  for lbl, cnt, gi in store.queue_groups()]
        return renderer.render_queue(count, groups)

    if active is not None:
        m = dict(active)
        import json
        m["metadata"] = json.loads(m["metadata_json"]) if m["metadata_json"] else {}
        return renderer.render_message(m)

    snap = snap or metrics.snapshot()
    colors = {
        "temp": _level_color(metrics.level(snap["temp_c"],
                  _threshold(cfg, "temp_warning_c"), _threshold(cfg, "temp_danger_c"))),
        "cpu": _level_color(metrics.level(snap["cpu_percent"],
                  _threshold(cfg, "cpu_warning_percent"), _threshold(cfg, "cpu_danger_percent"))),
        "ram": _level_color(metrics.level(snap["ram_percent"],
                  _threshold(cfg, "ram_warning_percent"), _threshold(cfg, "ram_danger_percent"))),
    }
    badges = _status_badges()
    return renderer.render_normal(snap, badges, colors)


def _group_color(group_index: int):
    return [renderer.DANGER, renderer.ACCENT, renderer.INFO][group_index]


# ponytail: DNS/API badges are fixed green (service is up); PWR reflects the
# latest power reading. Per-service health probes would be over-engineering v1.
_pwr_state = {"color": renderer.SUCCESS}


def _status_badges():
    return [("DNS", renderer.SUCCESS), ("API", renderer.SUCCESS),
            ("PWR", _pwr_state["color"])]


class DisplayLoop:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.driver = None
        self._stop = threading.Event()
        self._thread = None
        self._prev_power: dict | None = None
        self.status = "ok"

    def start(self):
        if self.cfg.getbool("display", "enabled"):
            self._init_driver()
        else:
            self.status = "disabled"
        self._thread = threading.Thread(target=self._run, name="display", daemon=True)
        self._thread.start()

    def _init_driver(self):
        try:
            from .drivers.st7735s import ST7735S
            self.driver = ST7735S(
                dc=self.cfg.getint("display", "dc_pin"),
                rst=self.cfg.getint("display", "rst_pin"),
                bl=self.cfg.getint("display", "bl_pin"),
                port=self.cfg.getint("display", "spi_port"),
                cs=self.cfg.getint("display", "spi_cs"),
                speed_hz=self.cfg.getint("display", "spi_speed_hz"),
                rotation=self.cfg.getint("display", "rotation"),
                x_offset=self.cfg.getint("display", "x_offset"),
                y_offset=self.cfg.getint("display", "y_offset"),
            )
            self.driver.display(renderer.render_boot())
            self.status = "ok"
        except Exception as e:
            self.driver = None
            self.status = "unavailable"
            log.warning("display driver unavailable, running headless: %s", e)
            store.log("warning", "display", "driver_unavailable", str(e))

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        if self.driver:
            self.driver.clear()
            self.driver.close()

    # --- loop ---
    def _run(self):
        normal_s = self.cfg.getint("display", "normal_refresh_seconds")
        power_s = self.cfg.getint("display", "power_refresh_seconds")
        last_power = 0.0
        last_snapshot = 0.0
        metrics.psutil.cpu_percent(interval=None)  # prime the counter
        while not self._stop.is_set():
            try:
                snap = metrics.snapshot()
                frame = build_frame(self.cfg, snap)
                if self.driver:
                    self.driver.display_if_changed(frame)

                nowt = time.monotonic()
                if nowt - last_power >= power_s:
                    self._check_power()
                    last_power = nowt
                if nowt - last_snapshot >= 60:
                    self._save_snapshot(snap)
                    last_snapshot = nowt
            except Exception:
                log.exception("display loop iteration failed")
            self._stop.wait(normal_s)

    def _save_snapshot(self, snap):
        store.save_snapshot(snap["cpu_percent"], snap["ram_percent"], snap["temp_c"],
                            snap["disk_percent"], "ok",
                            self.status, "ok")

    def _check_power(self):
        result = power.read()
        if result is None:
            return
        flags, raw = result
        if power.has_warning(flags) and flags != self._prev_power:
            store.save_power_event(flags, raw)
            store.log("warning", "power", "throttle_state", raw)
        self._prev_power = flags

        if power.is_active(flags):
            _pwr_state["color"] = renderer.DANGER
            self._ensure_power_message(flags)
        elif power.has_warning(flags):
            _pwr_state["color"] = renderer.WARNING
        else:
            _pwr_state["color"] = renderer.SUCCESS

    def _ensure_power_message(self, flags):
        from . import db
        row = db.query_one(
            "SELECT id FROM messages WHERE status='active' AND category='power' LIMIT 1")
        if row:
            return
        pinned = store.get_setting("power_event_pinning", "true") == "true"
        title = "Undervoltage" if flags["undervoltage_now"] else "Throttled"
        store.create_message(
            source="system", type="caution", title=f"Power Dip", category="power",
            message=f"{title} detected. Check the Pi power supply.",
            pinned=pinned, priority=8, metadata={"flags": flags})
        store.log("warning", "power", "power_message_created", title)
