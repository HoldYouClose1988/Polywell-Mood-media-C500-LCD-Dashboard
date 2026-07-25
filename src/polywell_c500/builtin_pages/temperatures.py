from __future__ import annotations

import subprocess

import psutil

from polywell_c500.page_api import Page
from .common import cpu_temperature


def smart_temperature(device: str) -> str:
    try:
        result = subprocess.run(
            ["smartctl", "-A", device],
            capture_output=True,
            text=True,
            timeout=4,
        )
    except Exception:
        return "N/A"

    for line in result.stdout.splitlines():
        if "Temperature_Celsius" in line or "Airflow_Temperature_Cel" in line:
            parts = line.split()
            if parts:
                return f"{parts[-1]}C"
        if line.strip().startswith("194 "):
            parts = line.split()
            if parts:
                return f"{parts[-1]}C"
    return "N/A"


class TemperaturesPage(Page):
    name = "temperatures"
    title = "Temperatures"
    refresh_interval = 5.0

    def render(self):
        cfg = self.context.config
        sources = cfg.get("temperature_sources", ["cpu", "sensor", "drives"])

        rows = ["TEMPERATURES"]

        if "cpu" in sources and len(rows) < 4:
            rows.append(f"CPU {cpu_temperature()}")

        if "sensor" in sources and len(rows) < 4:
            try:
                sensors = psutil.sensors_temperatures()
            except Exception:
                sensors = {}

            preferred = cfg.get("temperature_sensor_groups", [])
            groups = preferred or list(sensors.keys())

            for group in groups:
                for entry in sensors.get(group, []):
                    if len(rows) >= 4:
                        break
                    if entry.current is None:
                        continue
                    label = (entry.label or group)[:14]
                    rows.append(f"{label} {entry.current:.0f}C")
                if len(rows) >= 4:
                    break

        if "drives" in sources and len(rows) < 4:
            for entry in cfg.get("storage_devices", []):
                if len(rows) >= 4:
                    break
                device = entry.get("device")
                if not device:
                    continue
                label = str(entry.get("label", device))[:14]
                rows.append(f"{label} {smart_temperature(str(device))}")

        while len(rows) < 4:
            rows.append("")
        return rows


PAGE_CLASS = TemperaturesPage
