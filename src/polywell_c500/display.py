from __future__ import annotations

import os
import select
import termios
import time
from typing import Iterable, Optional

from .buttons import ButtonEvent
from .protocol import (
    CLEAR_SCREEN,
    HOME,
    ERASE_LINE,
    ROWS,
    COLS,
    DEFAULT_DEVICE,
    DEFAULT_BAUD,
    DEFAULT_WRITE_DELAY,
    cursor,
)

class C500Error(RuntimeError):
    pass

class C500Display:
    """
    Stable driver based on the confirmed C500 protocol.

    Confirmed behavior:
    - 19200 baud, 8N1
    - exact double-clear/double-home initialization at startup
    - ESC[2K erases the current line
    - changed rows are updated as:
        goto row -> erase line -> goto row -> write text
    - no trailing-space padding
    - no runtime full-screen clears
    """

    def __init__(
        self,
        device: str = DEFAULT_DEVICE,
        baud: int = DEFAULT_BAUD,
        timeout: float = 0.1,
        write_delay: float = DEFAULT_WRITE_DELAY,
    ):
        self.device = device
        self.baud = baud
        self.timeout = timeout
        self.write_delay = write_delay
        self.fd: Optional[int] = None
        self._frame = [""] * ROWS

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def open(self):
        if self.fd is not None:
            return
        try:
            self.fd = os.open(
                self.device,
                os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK,
            )
            self._configure_serial()
        except Exception:
            self.close()
            raise

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def _require_fd(self) -> int:
        if self.fd is None:
            raise C500Error("display is not open")
        return self.fd

    def _configure_serial(self):
        fd = self._require_fd()
        speeds = {
            9600: termios.B9600,
            19200: termios.B19200,
            38400: termios.B38400,
            57600: termios.B57600,
            115200: termios.B115200,
        }
        if self.baud not in speeds:
            raise ValueError(f"unsupported baud rate: {self.baud}")

        attrs = termios.tcgetattr(fd)
        attrs[0] = termios.IGNPAR
        attrs[1] = 0
        attrs[2] &= ~(termios.PARENB | termios.CSTOPB | termios.CSIZE)
        attrs[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL | termios.HUPCL
        attrs[3] = 0
        attrs[4] = speeds[self.baud]
        attrs[5] = speeds[self.baud]
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0

        termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSANOW, attrs)

    def _write(self, data: bytes):
        fd = self._require_fd()
        view = memoryview(data)

        while view:
            try:
                count = os.write(fd, view)
            except BlockingIOError:
                select.select([], [fd], [], 0.1)
                continue

            if count <= 0:
                raise C500Error("serial write failed")

            view = view[count:]

        termios.tcdrain(fd)

        if self.write_delay > 0:
            time.sleep(self.write_delay)

    @staticmethod
    def _sanitize(value: object) -> str:
        return str(value).replace("\r", " ").replace("\n", " ")[:COLS]

    def initialize(self):
        for chunk in (CLEAR_SCREEN, HOME, CLEAR_SCREEN, HOME):
            self._write(chunk)
        self._frame = [""] * ROWS

    def goto(self, row: int, col: int = 0):
        self._write(cursor(row, col))

    def erase_row(self, row: int):
        self.goto(row, 0)
        self._write(ERASE_LINE)
        self.goto(row, 0)

    def write(self, value: object):
        text = self._sanitize(value)
        if text:
            self._write(text.encode("ascii", errors="replace"))

    def write_row(self, row: int, value: object):
        text = self._sanitize(value)
        self.erase_row(row)
        if text:
            self.write(text)
        self._frame[row - 1] = text

    def show(
        self,
        lines: Iterable[object],
        *,
        initialize: bool = True,
        center: bool = False,
    ):
        values = [self._sanitize(value) for value in list(lines)[:ROWS]]
        values += [""] * (ROWS - len(values))

        if center:
            values = [
                ((" " * max(0, (COLS - len(value)) // 2)) + value) if value else ""
                for value in values
            ]

        if initialize:
            self.initialize()

        for row, value in enumerate(values, start=1):
            self.write_row(row, value)

    def render(
        self,
        lines: Iterable[object],
        *,
        center: bool = False,
        force: bool = False,
    ):
        values = [self._sanitize(value) for value in list(lines)[:ROWS]]
        values += [""] * (ROWS - len(values))

        if center:
            values = [
                ((" " * max(0, (COLS - len(value)) // 2)) + value) if value else ""
                for value in values
            ]

        for row, value in enumerate(values, start=1):
            if force or value != self._frame[row - 1]:
                self.write_row(row, value)

    def read_button(self, timeout: float | None = None):
        fd = self._require_fd()
        wait = self.timeout if timeout is None else timeout
        ready, _, _ = select.select([fd], [], [], wait)
        if not ready:
            return None

        raw = os.read(fd, 1)
        return ButtonEvent.decode(raw) if raw else None

    def wait_button(self):
        while True:
            event = self.read_button(timeout=1.0)
            if event is not None:
                return event
