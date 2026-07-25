#!/usr/bin/env python3
from polywell_c500 import C500Display, Dashboard
from polywell_c500.pages import Page

class HelloPage(Page):
    def render(self):
        return ["CUSTOM DASHBOARD", "Polywell C500", "ESC[2K line erase", "Ready"]

with C500Display() as display:
    Dashboard(display, [HelloPage()]).run()
