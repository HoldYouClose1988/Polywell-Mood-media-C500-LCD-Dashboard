from datetime import datetime

from polywell_c500.page_api import Page


class ClockPage(Page):
    name = "clock"
    title = "Clock"
    refresh_interval = 1.0

    def render(self):
        now = datetime.now()
        return [
            "CLOCK",
            now.strftime("%A"),
            now.strftime("%Y-%m-%d"),
            now.strftime("%I:%M:%S %p"),
        ]


PAGE_CLASS = ClockPage
