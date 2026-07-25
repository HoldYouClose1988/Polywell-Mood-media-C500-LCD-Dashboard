from dataclasses import dataclass
from enum import Enum
import time

class Button(str, Enum):
    OPTION_1 = "option_1"
    OPTION_2 = "option_2"
    OPTION_3 = "option_3"
    UP = "up"
    ENTER = "enter"
    LEFT = "left"
    DOWN = "down"
    RIGHT = "right"

BYTE_MAP = {
    b"1": Button.OPTION_1,
    b"2": Button.OPTION_2,
    b"3": Button.OPTION_3,
    b"4": Button.UP,
    b"5": Button.ENTER,
    b"6": Button.LEFT,
    b"7": Button.DOWN,
    b"8": Button.RIGHT,
}

@dataclass(frozen=True)
class ButtonEvent:
    button: Button
    raw: bytes
    timestamp: float

    @classmethod
    def decode(cls, raw: bytes):
        button = BYTE_MAP.get(raw)
        if button is None:
            return None
        return cls(button=button, raw=raw, timestamp=time.monotonic())
