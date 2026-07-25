from __future__ import annotations

import curses
import os
import shutil
import subprocess
from pathlib import Path

import psutil
import yaml

from .config import load_config
from .plugin_loader import discover_page_classes


CONFIG_PATH = Path("/etc/polywell-c500/dashboard.yml")


def interfaces():
    return [""] + sorted(name for name in psutil.net_if_addrs() if name != "lo")


def mounts():
    values = ["/"]
    for part in psutil.disk_partitions(all=False):
        if part.mountpoint not in values:
            values.append(part.mountpoint)
    return values


def block_devices():
    values = [""]
    try:
        result = subprocess.run(
            ["lsblk", "-dn", "-o", "PATH,TYPE"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for line in result.stdout.splitlines():
            path, _, kind = line.partition(" ")
            if kind.strip() == "disk":
                values.append(path.strip())
    except Exception:
        pass
    return values


def cycle(options, current, direction=1):
    if not options:
        return current
    try:
        index = options.index(current)
    except ValueError:
        index = -1
    return options[(index + direction) % len(options)]


class Configurator:
    fields = (
        "network_interface",
        "drive_1",
        "drive_2",
        "drive_3",
        "temperature_mode",
        "temperature_groups",
        "screensaver_type",
        "screensaver_timeout",
        "screensaver_interval",
        "snake_length",
        "pages",
        "save",
        "quit",
    )

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.config = load_config(CONFIG_PATH)
        self.config.setdefault("device", "/dev/ttyUSB0")
        self.config.setdefault("baud", 19200)
        self.config.setdefault("refresh", 1.0)
        self.config.setdefault("write_delay", 0.020)
        self.config.setdefault("network_interface", "")
        self.config.setdefault("storage_path", "/")
        self.config.setdefault("storage_devices", [
            {"label": "OS", "path": "/", "device": ""},
            {"label": "DATA1", "path": "/", "device": ""},
            {"label": "DATA2", "path": "/", "device": ""},
        ])
        while len(self.config["storage_devices"]) < 3:
            index = len(self.config["storage_devices"]) + 1
            self.config["storage_devices"].append(
                {"label": f"DISK{index}", "path": "/", "device": ""}
            )
        self.config.setdefault("temperature_sources", ["cpu", "sensor", "drives"])
        self.config.setdefault("temperature_sensor_groups", [])
        self.config.setdefault("screensaver_enabled", True)
        self.config.setdefault("screensaver_timeout", 60)
        self.config.setdefault("screensaver_type", "snake")
        self.config.setdefault("screensaver_interval", 0.45)
        self.config.setdefault("snake_length", 6)
        self.config.setdefault(
            "pages",
            ["overview", "storage", "network", "temperatures", "services"],
        )
        self.config.setdefault("services", ["smbd", "ssh", "docker"])
        self.config.setdefault("page_plugin_dir", "/etc/polywell-c500/pages")
        self.config.setdefault(
            "notification_socket",
            "/run/polywell-c500/dashboard.sock",
        )

        self.interfaces = interfaces()
        self.mounts = mounts()
        self.devices = block_devices()
        self.available_pages = list(
            discover_page_classes(self.config["page_plugin_dir"]).keys()
        )
        self.sensor_groups = self._sensor_groups()
        self.selected = 0
        self.message = ""

    def _sensor_groups(self):
        try:
            return sorted(psutil.sensors_temperatures().keys())
        except Exception:
            return []

    def _drive_text(self, index):
        entry = self.config["storage_devices"][index]
        return f"{entry.get('label','DISK')} | {entry.get('path','/')} | {entry.get('device','Auto') or 'Auto'}"

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        title = "Polywell C500 Dashboard Configurator"
        self.stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        self.stdscr.addstr(2, 2, "Arrows change values. Enter opens detailed selectors.")

        values = {
            "network_interface": self.config["network_interface"] or "Auto",
            "drive_1": self._drive_text(0),
            "drive_2": self._drive_text(1),
            "drive_3": self._drive_text(2),
            "temperature_mode": ", ".join(self.config["temperature_sources"]),
            "temperature_groups": ", ".join(self.config["temperature_sensor_groups"]) or "Auto",
            "screensaver_type": self.config["screensaver_type"],
            "screensaver_timeout": f"{self.config['screensaver_timeout']} seconds",
            "screensaver_interval": f"{self.config['screensaver_interval']:.2f} seconds",
            "snake_length": str(self.config["snake_length"]),
            "pages": ", ".join(self.config["pages"]),
            "save": "Save and restart dashboard",
            "quit": "Exit without saving",
        }

        labels = {
            "network_interface": "Network adapter",
            "drive_1": "Storage drive 1",
            "drive_2": "Storage drive 2",
            "drive_3": "Storage drive 3",
            "temperature_mode": "Temperature sources",
            "temperature_groups": "Sensor groups",
            "screensaver_type": "Screensaver",
            "screensaver_timeout": "Idle timeout",
            "screensaver_interval": "Animation interval",
            "snake_length": "Snake length",
            "pages": "Enabled pages",
            "save": "Save",
            "quit": "Quit",
        }

        for i, field in enumerate(self.fields):
            y = 4 + i
            attr = curses.A_REVERSE if i == self.selected else curses.A_NORMAL
            line = f"{labels[field]:<22} {values[field]}"
            self.stdscr.addnstr(y, 2, line, max(1, width - 4), attr)

        if self.message:
            self.stdscr.addnstr(height - 2, 2, self.message, max(1, width - 4), curses.A_BOLD)

        self.stdscr.refresh()

    def select_list(self, title, options, selected_values, multi=False):
        index = 0
        selected = list(selected_values)

        while True:
            self.stdscr.erase()
            self.stdscr.addstr(0, 2, title)
            self.stdscr.addstr(1, 2, "Space toggles. Enter accepts. Esc cancels.")

            for row, option in enumerate(options):
                marker = "[x]" if option in selected else "[ ]"
                attr = curses.A_REVERSE if row == index else curses.A_NORMAL
                prefix = marker if multi else ">"
                self.stdscr.addnstr(3 + row, 4, f"{prefix} {option or 'Auto'}", 70, attr)

            self.stdscr.refresh()
            key = self.stdscr.getch()

            if key == 27:
                return selected_values
            if key in (curses.KEY_UP, ord("k")):
                index = (index - 1) % len(options)
            elif key in (curses.KEY_DOWN, ord("j")):
                index = (index + 1) % len(options)
            elif key == ord(" ") and multi:
                option = options[index]
                if option in selected:
                    selected.remove(option)
                else:
                    selected.append(option)
            elif key in (10, 13, curses.KEY_ENTER):
                return selected if multi else options[index]

    def edit_drive(self, index):
        entry = self.config["storage_devices"][index]
        entry["path"] = self.select_list("Select mount path", self.mounts, entry.get("path", "/"), multi=False)
        entry["device"] = self.select_list("Select block device for SMART temperature", self.devices, entry.get("device", ""), multi=False)

    def edit_pages(self):
        result = self.select_list(
            "Select dashboard pages",
            self.available_pages,
            self.config["pages"],
            multi=True,
        )
        if result:
            self.config["pages"] = result

    def edit_temperature_sources(self):
        self.config["temperature_sources"] = self.select_list(
            "Select temperature sources",
            ["cpu", "sensor", "drives"],
            self.config["temperature_sources"],
            multi=True,
        )

    def edit_temperature_groups(self):
        self.config["temperature_sensor_groups"] = self.select_list(
            "Select lm-sensors groups",
            self.sensor_groups,
            self.config["temperature_sensor_groups"],
            multi=True,
        )

    def adjust(self, direction):
        field = self.fields[self.selected]
        if field == "network_interface":
            self.config[field] = cycle(self.interfaces, self.config[field], direction)
        elif field == "screensaver_type":
            self.config[field] = cycle(
                ["snake", "pong", "starfield", "matrix", "radar", "bounce"],
                self.config[field],
                direction,
            )
        elif field == "screensaver_timeout":
            self.config[field] = max(5, int(self.config[field]) + 5 * direction)
        elif field == "screensaver_interval":
            value = float(self.config[field]) + 0.05 * direction
            self.config[field] = round(max(0.20, min(2.0, value)), 2)
        elif field == "snake_length":
            self.config[field] = max(2, min(24, int(self.config[field]) + direction))

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        Path(self.config["page_plugin_dir"]).mkdir(parents=True, exist_ok=True)

        if CONFIG_PATH.exists():
            shutil.copy2(CONFIG_PATH, CONFIG_PATH.with_suffix(".yml.bak"))

        CONFIG_PATH.write_text(
            yaml.safe_dump(self.config, sort_keys=False),
            encoding="utf-8",
        )

        result = subprocess.run(
            ["systemctl", "restart", "polywell-c500-dashboard"],
            capture_output=True,
            text=True,
        )
        self.message = (
            f"Saved {CONFIG_PATH} and restarted dashboard."
            if result.returncode == 0
            else f"Saved, restart failed: {result.stderr.strip()}"
        )

    def run(self):
        curses.curs_set(0)
        self.stdscr.keypad(True)

        while True:
            self.draw()
            key = self.stdscr.getch()

            if key in (curses.KEY_UP, ord("k")):
                self.selected = (self.selected - 1) % len(self.fields)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.selected = (self.selected + 1) % len(self.fields)
            elif key in (curses.KEY_LEFT, ord("h")):
                self.adjust(-1)
            elif key in (curses.KEY_RIGHT, ord("l")):
                self.adjust(1)
            elif key in (10, 13, curses.KEY_ENTER):
                field = self.fields[self.selected]
                if field.startswith("drive_"):
                    self.edit_drive(int(field[-1]) - 1)
                elif field == "temperature_mode":
                    self.edit_temperature_sources()
                elif field == "temperature_groups":
                    self.edit_temperature_groups()
                elif field == "pages":
                    self.edit_pages()
                elif field == "save":
                    self.save()
                elif field == "quit":
                    return


def main():
    if os.geteuid() != 0:
        raise SystemExit("Run as root: sudo polywell-c500-config")
    curses.wrapper(lambda stdscr: Configurator(stdscr).run())
