import socket
import time

import psutil

from polywell_c500.page_api import Page
from .common import cpu_temperature, local_ip


class OverviewPage(Page):
    name = "overview"
    title = "Overview"
    refresh_interval = 1.0

    def render(self):
        uptime = int(time.time() - psutil.boot_time())
        days = uptime // 86400
        hours = (uptime % 86400) // 3600
        interface = self.context.config.get("network_interface")
        return [
            socket.gethostname(),
            local_ip(interface),
            f"CPU {psutil.cpu_percent():.0f}% RAM {psutil.virtual_memory().percent:.0f}%",
            f"Up {days}d {hours}h T {cpu_temperature()}",
        ]


PAGE_CLASS = OverviewPage
