# Technical Handoff

## Project Layout

- `src/polywell_c500/display.py` — stable serial/LCD driver
- `src/polywell_c500/buttons.py` — front-panel button decoding
- `src/polywell_c500/dashboard.py` — navigation, refresh scheduling,
  notifications, and screensaver lifecycle
- `src/polywell_c500/screensaver.py` — Snake, Pong, Starfield, Matrix Rain,
  Radar, and Bouncing Text
- `src/polywell_c500/notifications.py` — Unix datagram notification receiver
- `src/polywell_c500/notify_cli.py` — notification command
- `src/polywell_c500/configurator.py` — curses TUI
- `src/polywell_c500/plugin_loader.py` — built-in and external page discovery
- `src/polywell_c500/page_api.py` — page plugin contract
- `src/polywell_c500/builtin_pages/` — stock dashboard pages
- `config/dashboard.yml` — default configuration
- `systemd/polywell-c500-dashboard.service` — service definition
- `examples/pages/clock.py` — external plugin example

## Runtime Paths

```text
/etc/polywell-c500/dashboard.yml
/etc/polywell-c500/pages/
/run/polywell-c500/dashboard.sock
/dev/ttyUSB0
```

## Console Commands

```text
polywell-c500
polywell-c500-dashboard
polywell-c500-notify
polywell-c500-config
```

When installed in the documented virtual environment, the full paths are under:

```text
/opt/polywell-c500/venv/bin/
```

## Dashboard Pages

Built-in pages:

- `overview` — hostname, selected-interface address, CPU/RAM, uptime, CPU temp
- `storage` — up to three configured volumes and optional SMART temperatures
- `network` — selected-interface address and transfer rates
- `temperatures` — CPU, selected sensor groups, and configured drive temps
- `services` — up to three configured systemd services

Each page can declare its own `refresh_interval`.

## Screensavers

Selectable values:

```text
snake
pong
starfield
matrix
radar
bounce
```

Animations intentionally use moderate intervals to avoid overrunning the
controller.

## Configuration Safety

The TUI backs up the active YAML file before saving. The default configuration
contains generic mount paths and no personal identifiers.

## Hardware-Layer Policy

The current runtime update sequence is verified:

```text
cursor -> ESC[2K -> cursor -> text
```

Do not replace this with full-row spaces or runtime full-screen clears. Any
future low-level change should be tested independently from the dashboard
engine.

## Service Privileges

The supplied service runs as root because it accesses the serial device,
systemd state, hardware sensors, and SMART data. A future hardening pass could
use dedicated groups and narrowly scoped privileges, but that has not been
implemented in this release.

## Public Release Notes

The repository should not contain:

- Private IP addresses
- Personal names or email addresses
- SSH material or API credentials
- Drive serial numbers
- Machine-specific UUIDs
- User home-directory paths

The documented BIOS password is intentionally included as hardware access
documentation.
