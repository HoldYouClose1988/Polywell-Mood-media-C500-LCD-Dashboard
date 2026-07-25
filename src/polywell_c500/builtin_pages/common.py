from __future__ import annotations

import socket

import psutil


def local_ip(interface: str | None = None) -> str:
    if interface:
        addrs = psutil.net_if_addrs().get(interface, [])
        for addr in addrs:
            if addr.family == socket.AF_INET:
                return addr.address
        return "No IPv4"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("1.1.1.1", 80))
        return sock.getsockname()[0]
    except OSError:
        return "No network"
    finally:
        sock.close()


def cpu_temperature() -> str:
    try:
        groups = psutil.sensors_temperatures()
    except Exception:
        groups = {}

    preferred = ("coretemp", "k10temp", "cpu_thermal", "acpitz")
    for name in preferred:
        entries = groups.get(name) or []
        for entry in entries:
            if entry.current is not None:
                return f"{entry.current:.0f}C"

    for entries in groups.values():
        for entry in entries:
            if entry.current is not None:
                return f"{entry.current:.0f}C"

    return "N/A"
