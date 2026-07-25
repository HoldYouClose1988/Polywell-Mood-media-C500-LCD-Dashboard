import time

import psutil

from polywell_c500.page_api import Page
from .common import local_ip


class NetworkPage(Page):
    name = "network"
    title = "Network"
    refresh_interval = 1.0

    def __init__(self, context):
        super().__init__(context)
        self.interface = context.config.get("network_interface")
        self.last = self._counters()
        self.last_time = time.monotonic()

    def _counters(self):
        if self.interface:
            return psutil.net_io_counters(pernic=True).get(self.interface)
        return psutil.net_io_counters()

    def render(self):
        now = self._counters()
        now_time = time.monotonic()

        if now is None or self.last is None:
            self.last = now
            self.last_time = now_time
            return ["NETWORK", self.interface or "Auto", "No counters", ""]

        elapsed = max(now_time - self.last_time, 0.001)
        rx = (now.bytes_recv - self.last.bytes_recv) / elapsed / 1024**2
        tx = (now.bytes_sent - self.last.bytes_sent) / elapsed / 1024**2
        self.last = now
        self.last_time = now_time

        label = self.interface or "Auto"
        return [
            f"NETWORK {label}"[:24],
            local_ip(self.interface),
            f"RX {rx:.2f} MB/s",
            f"TX {tx:.2f} MB/s",
        ]


PAGE_CLASS = NetworkPage
