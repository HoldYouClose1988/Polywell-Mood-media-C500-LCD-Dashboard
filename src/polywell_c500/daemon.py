import argparse
import logging
import signal

from .config import load_config
from .dashboard import Dashboard
from .display import C500Display
from .plugin_loader import build_pages


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/polywell-c500/dashboard.yml")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config(args.config)
    display = C500Display(
        device=config.get("device", "/dev/ttyUSB0"),
        baud=int(config.get("baud", 19200)),
        write_delay=float(config.get("write_delay", 0.020)),
    )
    dashboard = Dashboard(
        display,
        build_pages(config),
        refresh=float(config.get("refresh", 1.0)),
        screensaver_enabled=bool(config.get("screensaver_enabled", True)),
        screensaver_timeout=float(config.get("screensaver_timeout", 60.0)),
        screensaver_config=config,
        notification_socket=config.get(
            "notification_socket",
            "/run/polywell-c500/dashboard.sock",
        ),
    )

    signal.signal(signal.SIGTERM, lambda *_: dashboard.stop())
    signal.signal(signal.SIGINT, lambda *_: dashboard.stop())

    try:
        with display:
            dashboard.run()
    except Exception:
        logging.exception("dashboard failed")
        return 1
    return 0
