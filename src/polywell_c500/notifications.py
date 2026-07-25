from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Notification:
    lines: list[str]
    expires_at: float

    @property
    def expired(self) -> bool:
        return time.monotonic() >= self.expires_at


class NotificationServer:
    def __init__(self, socket_path: str):
        self.socket_path = Path(socket_path)
        self.sock: socket.socket | None = None

    def open(self):
        self.close()
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.bind(str(self.socket_path))
        self.sock.setblocking(False)
        os.chmod(self.socket_path, 0o666)

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass

    def read(self) -> Notification | None:
        if self.sock is None:
            return None

        try:
            payload = self.sock.recv(4096)
        except BlockingIOError:
            return None

        try:
            data = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

        raw_lines = data.get("lines", [])
        if not isinstance(raw_lines, list):
            return None

        lines = [str(line)[:24] for line in raw_lines[:4]]
        while len(lines) < 4:
            lines.append("")

        try:
            duration = float(data.get("duration", 5.0))
        except (TypeError, ValueError):
            duration = 5.0

        duration = max(1.0, min(duration, 300.0))
        return Notification(
            lines=lines,
            expires_at=time.monotonic() + duration,
        )
