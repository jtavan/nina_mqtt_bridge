"""Command-line entry point for nina_mqtt_bridge."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from .bridge import Bridge
from .config import load_config_from_cli


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NINA to MQTT bridge.")
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Path to YAML configuration file.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase log verbosity (can be specified multiple times).",
    )
    return parser.parse_args(argv)


def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    setup_logging(args.verbose)

    config = load_config_from_cli(args.config)
    bridge = Bridge(config)

    stop_signals = (signal.SIGINT, signal.SIGTERM)
    for sig in stop_signals:
        signal.signal(sig, lambda _s, _f: bridge.stop())

    bridge.start()
    try:
        signal.pause()
    except AttributeError:
        # Windows compatibility: fallback to manual loop
        import time

        while True:
            time.sleep(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
