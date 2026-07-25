from __future__ import annotations

import os
import shutil
import subprocess

from polywell_c500.page_api import Page


def temperature_for_device(device: str | None) -> str:
    if not device:
        return ""
    try:
        result = subprocess.run(
            ["smartctl", "-A", device],
            capture_output=True,
            text=True,
            timeout=4,
        )
    except Exception:
        return ""

    for line in result.stdout.splitlines():
        if "Temperature_Celsius" in line or "Airflow_Temperature_Cel" in line:
            parts = line.split()
            if parts:
                return f"{parts[-1]}C"
        if line.strip().startswith("194 "):
            parts = line.split()
            if parts:
                return f"{parts[-1]}C"
    return ""


class StoragePage(Page):
    name = "storage"
    title = "Storage"
    refresh_interval = 5.0

    def render(self):
        entries = self.context.config.get("storage_devices", [])
        if not entries:
            entries = [{"label": "ROOT", "path": self.context.config.get("storage_path", "/")}]

        rows = ["STORAGE"]
        for entry in entries[:3]:
            label = str(entry.get("label", "DISK"))[:7]
            path = str(entry.get("path", "/"))
            device = entry.get("device")

            if not os.path.exists(path):
                rows.append(f"{label:<7} MISSING")
                continue

            usage = shutil.disk_usage(path)
            percent = usage.used / usage.total * 100 if usage.total else 0
            temp = temperature_for_device(device)
            suffix = f" {temp}" if temp else ""
            rows.append(f"{label:<7} {percent:>3.0f}%{suffix}"[:24])

        while len(rows) < 4:
            rows.append("")
        return rows


PAGE_CLASS = StoragePage
