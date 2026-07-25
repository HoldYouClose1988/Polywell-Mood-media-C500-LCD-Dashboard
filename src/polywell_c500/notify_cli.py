from __future__ import annotations

import argparse
import json
import socket


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send a temporary message to the Polywell C500 dashboard"
    )
    parser.add_argument(
        "--socket",
        default="/run/polywell-c500/dashboard.sock",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="seconds to display the message",
    )
    parser.add_argument(
        "lines",
        nargs="+",
        help="one to four display lines",
    )
    args = parser.parse_args()

    payload = json.dumps(
        {
            "lines": args.lines[:4],
            "duration": args.duration,
        }
    ).encode("utf-8")

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        sock.sendto(payload, args.socket)
    except OSError as exc:
        parser.error(f"could not send notification: {exc}")
    finally:
        sock.close()

    return 0
