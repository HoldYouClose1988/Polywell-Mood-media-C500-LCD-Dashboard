ESC = b"\x1b"
CLEAR_SCREEN = ESC + b"[2J"
HOME = ESC + b"[0;0H"
ERASE_LINE = ESC + b"[2K"

ROWS = 4
COLS = 24
PHYSICAL_ROWS = (0, 2, 4, 6)

DEFAULT_DEVICE = "/dev/ttyUSB0"
DEFAULT_BAUD = 19200
DEFAULT_WRITE_DELAY = 0.020

def cursor(row: int, col: int = 0) -> bytes:
    if not 1 <= row <= ROWS:
        raise ValueError("row must be 1 through 4")
    if not 0 <= col < COLS:
        raise ValueError("column must be 0 through 23")
    return f"\x1b[{PHYSICAL_ROWS[row - 1]};{col}f".encode("ascii")
