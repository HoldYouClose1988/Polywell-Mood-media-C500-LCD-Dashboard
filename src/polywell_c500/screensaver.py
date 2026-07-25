from __future__ import annotations

import math
import random
import socket
from dataclasses import dataclass
from typing import Protocol

from .protocol import ROWS, COLS


class Screensaver(Protocol):
    interval: float
    def reset(self) -> None: ...
    def due(self, now: float) -> bool: ...
    def step(self, now: float) -> list[str]: ...


class TimedScreensaver:
    interval = 0.45

    def __init__(self, interval: float):
        self.interval = interval
        self._last_step = 0.0

    def reset(self):
        self._last_step = 0.0

    def due(self, now: float) -> bool:
        return self._last_step == 0.0 or now - self._last_step >= self.interval

    def _mark(self, now: float):
        self._last_step = now


class SnakeScreensaver(TimedScreensaver):
    def __init__(self, interval=0.45, length=6, head="@", body="o"):
        super().__init__(interval)
        self.length = max(2, min(int(length), COLS))
        self.head = (head or "@")[:1]
        self.body = (body or "o")[:1]
        self.rng = random.Random()
        self.reset()

    def reset(self):
        super().reset()
        row, col = ROWS // 2, COLS // 2
        self.snake = [(row, max(0, col - i)) for i in range(self.length)]
        self.direction = (0, 1)

    def step(self, now):
        if self._last_step:
            if self.rng.random() < 0.18:
                dr, dc = self.direction
                self.direction = self.rng.choice(
                    [(-1, 0), (1, 0)] if dr == 0 else [(0, -1), (0, 1)]
                )
            dr, dc = self.direction
            hr, hc = self.snake[0]
            new_head = ((hr + dr) % ROWS, (hc + dc) % COLS)

            if new_head in self.snake[1:]:
                choices = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                self.rng.shuffle(choices)
                for candidate in choices:
                    if candidate == (-dr, -dc):
                        continue
                    test = ((hr + candidate[0]) % ROWS, (hc + candidate[1]) % COLS)
                    if test not in self.snake[1:]:
                        self.direction = candidate
                        new_head = test
                        break

            self.snake.insert(0, new_head)
            del self.snake[self.length:]

        self._mark(now)
        canvas = [[" "] * COLS for _ in range(ROWS)]
        for r, c in self.snake[1:]:
            canvas[r][c] = self.body
        r, c = self.snake[0]
        canvas[r][c] = self.head
        return ["".join(row).rstrip() for row in canvas]


class PongScreensaver(TimedScreensaver):
    def __init__(self, interval=0.45):
        super().__init__(interval)
        self.reset()

    def reset(self):
        super().reset()
        self.ball_r, self.ball_c = 1, COLS // 2
        self.dr, self.dc = 1, 1
        self.left_r, self.right_r = 1, 1

    def step(self, now):
        if self._last_step:
            nr, nc = self.ball_r + self.dr, self.ball_c + self.dc
            if nr < 0 or nr >= ROWS:
                self.dr *= -1
                nr = self.ball_r + self.dr
            if nc <= 1 or nc >= COLS - 2:
                self.dc *= -1
                nc = self.ball_c + self.dc
            self.ball_r, self.ball_c = nr, nc
            if self.ball_r > self.left_r:
                self.left_r = min(ROWS - 2, self.left_r + 1)
            elif self.ball_r < self.left_r:
                self.left_r = max(0, self.left_r - 1)
            if self.ball_r > self.right_r:
                self.right_r = min(ROWS - 2, self.right_r + 1)
            elif self.ball_r < self.right_r:
                self.right_r = max(0, self.right_r - 1)

        self._mark(now)
        canvas = [[" "] * COLS for _ in range(ROWS)]
        for rr in (self.left_r, min(ROWS - 1, self.left_r + 1)):
            canvas[rr][0] = "|"
        for rr in (self.right_r, min(ROWS - 1, self.right_r + 1)):
            canvas[rr][COLS - 1] = "|"
        canvas[self.ball_r][self.ball_c] = "o"
        return ["".join(row).rstrip() for row in canvas]


class StarfieldScreensaver(TimedScreensaver):
    CHARS = (".", "+", "*")

    def __init__(self, interval=0.50, stars=9):
        super().__init__(interval)
        self.count = max(3, min(int(stars), 20))
        self.rng = random.Random()
        self.reset()

    def reset(self):
        super().reset()
        self.stars = [
            [self.rng.randrange(ROWS), self.rng.randrange(COLS), self.rng.randrange(3)]
            for _ in range(self.count)
        ]

    def step(self, now):
        if self._last_step:
            for star in self.stars:
                speed = star[2] + 1
                star[1] -= speed
                if star[1] < 0:
                    star[0] = self.rng.randrange(ROWS)
                    star[1] = COLS - 1
                    star[2] = self.rng.randrange(3)

        self._mark(now)
        canvas = [[" "] * COLS for _ in range(ROWS)]
        for r, c, depth in self.stars:
            canvas[r][c] = self.CHARS[depth]
        return ["".join(row).rstrip() for row in canvas]


class MatrixScreensaver(TimedScreensaver):
    GLYPHS = "0123456789ABCDEF"

    def __init__(self, interval=0.55, columns=5):
        super().__init__(interval)
        self.column_count = max(2, min(int(columns), 8))
        self.rng = random.Random()
        self.reset()

    def reset(self):
        super().reset()
        cols = self.rng.sample(range(COLS), k=min(self.column_count, COLS))
        self.drops = [[col, self.rng.randrange(ROWS), self.rng.randrange(2, 5)] for col in cols]

    def step(self, now):
        if self._last_step:
            for drop in self.drops:
                drop[1] = (drop[1] + 1) % ROWS
                if self.rng.random() < 0.25:
                    drop[2] = self.rng.randrange(2, 5)

        self._mark(now)
        canvas = [[" "] * COLS for _ in range(ROWS)]
        for col, head, length in self.drops:
            for offset in range(length):
                row = (head - offset) % ROWS
                canvas[row][col] = self.rng.choice(self.GLYPHS)
        return ["".join(row).rstrip() for row in canvas]


class RadarScreensaver(TimedScreensaver):
    SWEEPS = ("|", "/", "-", "\\")

    def __init__(self, interval=0.55, blips=3):
        super().__init__(interval)
        self.blip_count = max(1, min(int(blips), 6))
        self.rng = random.Random()
        self.reset()

    def reset(self):
        super().reset()
        self.phase = 0
        self.blips = []
        self._regen_blips()

    def _regen_blips(self):
        self.blips = [
            (self.rng.randrange(ROWS), self.rng.randrange(COLS))
            for _ in range(self.blip_count)
        ]

    def step(self, now):
        if self._last_step:
            self.phase = (self.phase + 1) % len(self.SWEEPS)
            if self.phase == 0:
                self._regen_blips()

        self._mark(now)
        canvas = [[" "] * COLS for _ in range(ROWS)]
        center_r, center_c = 1, COLS // 2
        canvas[center_r][center_c] = "+"
        canvas[center_r][min(COLS - 1, center_c + 1)] = self.SWEEPS[self.phase]
        for r, c in self.blips:
            canvas[r][c] = "*"
        return ["".join(row).rstrip() for row in canvas]


@dataclass
class BouncingTextScreensaver(TimedScreensaver):
    text: str | None = None
    interval: float = 0.45

    def __post_init__(self):
        TimedScreensaver.__init__(self, self.interval)
        if self.text is None:
            self.text = socket.gethostname().upper()
        self.text = str(self.text)[:COLS]
        self.reset()

    def reset(self):
        TimedScreensaver.reset(self)
        self.row = 0
        self.col = 0
        self.drow = 1
        self.dcol = 1

    def step(self, now):
        max_col = max(0, COLS - len(self.text))
        if self._last_step:
            nr = self.row + self.drow
            nc = self.col + self.dcol
            if nr < 0 or nr >= ROWS:
                self.drow *= -1
                nr = self.row + self.drow
            if nc < 0 or nc > max_col:
                self.dcol *= -1
                nc = self.col + self.dcol
            self.row, self.col = nr, nc
        self._mark(now)
        frame = [""] * ROWS
        frame[self.row] = (" " * self.col) + self.text
        return frame


def build_screensaver(config: dict) -> Screensaver:
    kind = str(config.get("screensaver_type", "snake")).strip().lower()
    interval = float(config.get("screensaver_interval", 0.45))
    interval = max(0.20, interval)

    factories = {
        "snake": lambda: SnakeScreensaver(
            interval=interval,
            length=int(config.get("snake_length", 6)),
            head=str(config.get("snake_head", "@"))[:1] or "@",
            body=str(config.get("snake_body", "o"))[:1] or "o",
        ),
        "pong": lambda: PongScreensaver(interval=interval),
        "starfield": lambda: StarfieldScreensaver(
            interval=interval,
            stars=int(config.get("starfield_stars", 9)),
        ),
        "matrix": lambda: MatrixScreensaver(
            interval=interval,
            columns=int(config.get("matrix_columns", 5)),
        ),
        "radar": lambda: RadarScreensaver(
            interval=interval,
            blips=int(config.get("radar_blips", 3)),
        ),
        "bounce": lambda: BouncingTextScreensaver(
            text=config.get("screensaver_text"),
            interval=interval,
        ),
    }

    try:
        return factories[kind]()
    except KeyError as exc:
        raise ValueError(f"unknown screensaver_type: {kind}") from exc
