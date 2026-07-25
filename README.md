# Polywell C500 Front Panel Dashboard

An independent Linux driver and dashboard for the 4×24 character LCD and
eight-button front panel used in the Polywell C500, including C500 hardware
distributed as a Mood Media appliance.

The project was developed through direct hardware testing and protocol analysis.
It does not contain vendor firmware, proprietary binaries, or copied vendor code.

> This project is not affiliated with or endorsed by Polywell Computers or Mood
> Media. Product names are used only for identification and compatibility.

## Features

- Verified 19200-baud C500 LCD protocol
- Reliable row clearing with `ESC[2K`
- All eight front-panel buttons
- Overview, storage, network, temperature, and service pages
- Compact monitoring for three storage volumes
- Optional SMART temperature readings
- CPU and `lm-sensors` temperature sources
- Plugin-based custom dashboard pages
- Per-page refresh intervals
- Unix-socket notifications
- Curses TUI configurator
- Six screensavers:
  - Snake
  - Pong
  - Starfield
  - Matrix Rain
  - Radar
  - Bouncing Text
- `systemd` service

## Requirements

- Debian, Ubuntu, OpenMediaVault, or another compatible Linux distribution
- Python 3.10 or newer
- Front panel available as `/dev/ttyUSB0` by default
- `smartmontools` for drive temperatures
- Working sensor drivers for CPU and motherboard temperatures

Install system dependencies:

```bash
sudo apt update
sudo apt install -y python3-venv smartmontools
```

## Installation

Create a virtual environment:

```bash
sudo mkdir -p /opt/polywell-c500
sudo python3 -m venv /opt/polywell-c500/venv
```

Install the project from the repository directory:

```bash
sudo /opt/polywell-c500/venv/bin/pip install .
```

Install the default configuration and service:

```bash
sudo mkdir -p /etc/polywell-c500/pages
sudo cp config/dashboard.yml /etc/polywell-c500/dashboard.yml
sudo cp systemd/polywell-c500-dashboard.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now polywell-c500-dashboard
```

Check the service:

```bash
sudo systemctl status polywell-c500-dashboard --no-pager
sudo journalctl -u polywell-c500-dashboard -n 50 --no-pager
```

## TUI Configurator

```bash
sudo /opt/polywell-c500/venv/bin/polywell-c500-config
```

The configurator supports:

- Network interface selection
- Three storage mount paths
- Three optional SMART block-device mappings
- Temperature source selection
- Sensor-group selection
- Dashboard page selection
- Screensaver type and timing
- Snake length

The existing configuration is backed up to:

```text
/etc/polywell-c500/dashboard.yml.bak
```

before saving.

## Default Controls

- Right, Down, Enter, or Option 2: next page
- Left, Up, or Option 1: previous page
- Option 3: activate screensaver
- Any button while a screensaver is active: wake the dashboard
- Any button while a notification is displayed: dismiss it

## Notifications

Send one to four temporary display lines:

```bash
sudo /opt/polywell-c500/venv/bin/polywell-c500-notify \
  --duration 8 \
  "Backup Complete" \
  "No errors"
```

The dashboard listens on:

```text
/run/polywell-c500/dashboard.sock
```

## Custom Page Plugins

External pages are loaded from:

```text
/etc/polywell-c500/pages/
```

See [docs/PLUGINS.md](docs/PLUGINS.md) and
[examples/pages/clock.py](examples/pages/clock.py).

## Hardware Documentation

- [Hardware notes and BIOS access](docs/HARDWARE.md)
- [Front-panel protocol](docs/PROTOCOL.md)
- [Technical handoff](docs/TECHNICAL_HANDOFF.md)

## License

MIT. See [LICENSE](LICENSE).

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

///////From the keyboard of the human///////

Obviously, I used AI on a lot of this. This was a weekend project. I bought this thing to use as a headless OMV server, and my goal is complete, so don't expect updates.

I was able to pull a read of the BIOS using a RasPi and a TSSOP8 clip. The password is not Mood Media's set admin password. Best I can tell, it's an override or backdoor from AMI—or maybe it was just left in. Who knows. You will have to re-enter it every time you boot to the BIOS, however, due to it sidestepping the set admin password.

 I'll put a dump of the BIOS in here if you feel like poking around.

The BIOS and hardware are fairly recent, though. The AI wrote a competent enough driver for the front LCD, so it works pretty well. It suffers from AI oversights, so ymmv. I threw in some screensavers for some pizzazz when it's on your homelab rack. 

Overall, it's a cool little box, I think. Make sure your hardware matches mine, though, as there are a lot of Mood Media boxes floating around—mainly old ones. The driver might be the same; it won't hurt to try. You could feed this repo into another AI to customize it for your Mood hardware. Good luck!
