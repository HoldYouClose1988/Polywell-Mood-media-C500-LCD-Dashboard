# Confirmed C500 Front-Panel Protocol

## Transport

- Interface: USB serial through a CH340 bridge
- Default Linux device: `/dev/ttyUSB0`
- Baud rate: 19200
- Format: 8N1
- Display: 4 rows × 24 columns

## Initialization

The known-good startup sequence is:

```text
ESC[2J
ESC[0;0H
ESC[2J
ESC[0;0H
```

In bytes:

```text
1b 5b 32 4a
1b 5b 30 3b 30 48
1b 5b 32 4a
1b 5b 30 3b 30 48
```

This full initialization is intended for startup, not routine animation.

## Cursor Positioning

The display accepts:

```text
ESC[row;columnf
```

The four logical rows use cursor row values `0`, `2`, `4`, and `6`.

Examples:

```text
ESC[0;0f
ESC[2;0f
ESC[4;0f
ESC[6;0f
```

## Safe Runtime Row Update

For each changed row:

```text
ESC[row;0f
ESC[2K
ESC[row;0f
text
```

`ESC[2K` is the key behavior discovered during testing. It erases the current
line without the unreliable effects observed when writing a complete row of
spaces or repeatedly clearing the entire screen.

## Timing

The controller processes commands slowly relative to the serial link. The
driver uses `tcdrain()` and a configurable inter-write delay. The shipped
configuration uses:

```yaml
write_delay: 0.020
```

Animation intervals should remain conservative. Faster serial transport does
not imply that the display controller can accept rapid command bursts.

## Button Input

Button presses arrive as one-byte ASCII values:

```text
1 2 3 4 5 6 7 8
```

Mapping:

| ASCII | Function |
|---|---|
| `1` | Option 1 |
| `2` | Option 2 |
| `3` | Option 3 |
| `4` | Up |
| `5` | Enter |
| `6` | Left |
| `7` | Down |
| `8` | Right |

## Failure Modes Observed During Development

### Stale characters

Cause: writing shorter text without erasing the line.

Fix: use `ESC[2K` before rewriting the row.

### Solid or all-pixels-on display

Observed after aggressive full-row space padding. Avoid using spaces as a
general line-clear mechanism.

### Repeated `J` characters

Observed when full-screen clear commands were repeatedly sent during normal
runtime updates. Reserve the double-clear startup sequence for initialization.

## Implementation Rule

Treat `src/polywell_c500/display.py` as the stable hardware abstraction layer.
Changes to the low-level protocol should be validated with controlled serial
traces before release.
