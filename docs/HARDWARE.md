# Polywell C500 Hardware Notes

These notes describe the specific Polywell C500 hardware tested during
development. Other board revisions or deployments may differ.

## BIOS Access

The BIOS password verified on the tested C500 is:

```text
l}c-ul+g=&
```

The characters are case-sensitive and include punctuation. This is a hardware
service credential documented for owners of the appliance; it is not used by
the dashboard software.

## Front Panel

- Display: 4 rows × 24 characters
- Controls: eight front-panel buttons
- Interface: USB serial
- USB-UART bridge observed during testing: CH340
- Typical Linux device: `/dev/ttyUSB0`

## Serial Configuration

```text
19200 baud
8 data bits
No parity
1 stop bit
```

The working Linux termios configuration also uses `IGNPAR`, `CREAD`, `CLOCAL`,
and `HUPCL`.

## Button Mapping

The controller sends ASCII digits:

| Byte | Button |
|---|---|
| `1` | Option 1 |
| `2` | Option 2 |
| `3` | Option 3 |
| `4` | Up |
| `5` | Enter |
| `6` | Left |
| `7` | Down |
| `8` | Right |

## Display Geometry

The display uses four logical rows, addressed with the following cursor row
values:

| Logical row | Cursor row value |
|---|---:|
| 1 | 0 |
| 2 | 2 |
| 3 | 4 |
| 4 | 6 |

Each row supports up to 24 characters.

## Important Controller Behavior

The panel is not a fully conventional terminal.

- Writing a shorter string over a longer string leaves stale characters.
- Padding entire rows with spaces produced unreliable behavior during testing.
- Repeated full-screen clears during animation could desynchronize the display.
- `ESC[2K` reliably erases the current row and is the correct runtime update
  mechanism.
- Conservative inter-command pacing is recommended.

## Operating Systems

The implementation was tested on Linux and is intended for Debian-family
systems, including OpenMediaVault. Other Linux distributions should work if
the CH340 driver and Python dependencies are available.

## Reverse-Engineering Scope

The implementation was derived from observed serial behavior and controlled
hardware tests. No proprietary firmware, vendor SDK, customer media, or vendor
service credentials other than the owner-access BIOS password above are
included.
