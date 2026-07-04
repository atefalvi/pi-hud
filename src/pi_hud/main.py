"""Entry point: init DB, start the display loop, run uvicorn (single worker)."""
import logging
import signal

import uvicorn

from . import config, db
from . import message_store as store
from .api import create_app
from .display_loop import DisplayLoop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("pi_hud")


def main():
    cfg = config.load()
    log.info("config: %s", cfg.path or "built-in defaults")
    db.init(cfg.get("database", "path"))
    store.log("info", "system", "startup", f"host={cfg.get('api','host')}")

    loop = DisplayLoop(cfg)
    loop.start()

    app = create_app(cfg, loop)

    def _shutdown(*_):
        loop.stop()
    signal.signal(signal.SIGTERM, _shutdown)

    # lan_mode is the one switch that opens the API to the LAN; otherwise
    # bind whatever host is configured (default 127.0.0.1, local-only).
    host = "0.0.0.0" if cfg.getbool("api", "lan_mode") else cfg.get("api", "host")
    log.info("binding %s:%s (lan_mode=%s)", host, cfg.getint("api", "port"),
             cfg.getbool("api", "lan_mode"))
    try:
        uvicorn.run(app, host=host,
                    port=cfg.getint("api", "port"), workers=1, log_level="info")
    finally:
        loop.stop()


if __name__ == "__main__":
    main()
