from __future__ import annotations

import time

from .buttons import Button
from .notifications import Notification, NotificationServer
from .screensaver import build_screensaver


class Dashboard:
    def __init__(
        self,
        display,
        pages,
        refresh=1.0,
        screensaver_enabled=True,
        screensaver_timeout=60.0,
        screensaver_config=None,
        notification_socket="/run/polywell-c500/dashboard.sock",
    ):
        if not pages:
            raise ValueError("at least one page is required")

        self.display = display
        self.pages = list(pages)
        self.refresh = refresh
        self.index = 0
        self.running = False

        self.screensaver_enabled = screensaver_enabled
        self.screensaver_timeout = max(1.0, screensaver_timeout)
        self.screensaver = build_screensaver(screensaver_config or {})
        self.last_input = time.monotonic()
        self.screensaver_active = False

        self.notification_server = NotificationServer(notification_socket)
        self.notification: Notification | None = None

    @property
    def current(self):
        return self.pages[self.index]

    def next_page(self):
        self.index = (self.index + 1) % len(self.pages)

    def previous_page(self):
        self.index = (self.index - 1) % len(self.pages)

    def _enter_screensaver(self):
        self.screensaver_active = True
        self.screensaver.reset()
        self.display.render(["", "", "", ""], force=True)

    def _exit_screensaver(self):
        self.screensaver_active = False
        self.last_input = time.monotonic()
        self.display.render(self.current.render(), force=True)

    def _show_notification(self, notification: Notification):
        self.notification = notification
        self.screensaver_active = False
        self.display.render(notification.lines, force=True)

    def _clear_notification(self):
        self.notification = None
        self.last_input = time.monotonic()
        self.display.render(self.current.render(), force=True)

    def run(self):
        self.running = True
        self.notification_server.open()
        self.display.show(self.current.render(), initialize=True)
        next_refresh = time.monotonic() + getattr(self.current, 'refresh_interval', self.refresh)

        try:
            while self.running:
                now = time.monotonic()

                incoming = self.notification_server.read()
                if incoming is not None:
                    self._show_notification(incoming)

                if self.notification is not None:
                    if self.notification.expired:
                        self._clear_notification()
                    event = self.display.read_button(timeout=0.05)
                    if event is not None:
                        self._clear_notification()
                    continue

                if (
                    self.screensaver_enabled
                    and not self.screensaver_active
                    and now - self.last_input >= self.screensaver_timeout
                ):
                    self._enter_screensaver()

                if self.screensaver_active:
                    if self.screensaver.due(now):
                        self.display.render(self.screensaver.step(now), force=True)
                elif now >= next_refresh:
                    self.display.render(self.current.render())
                    next_refresh = now + getattr(self.current, 'refresh_interval', self.refresh)

                event = self.display.read_button(timeout=0.05)
                if event is None:
                    continue

                if self.screensaver_active:
                    self._exit_screensaver()
                    next_refresh = time.monotonic() + getattr(self.current, 'refresh_interval', self.refresh)
                    continue

                self.last_input = time.monotonic()

                if event.button in (
                    Button.RIGHT,
                    Button.DOWN,
                    Button.ENTER,
                    Button.OPTION_2,
                ):
                    self.next_page()
                    self.display.render(self.current.render(), force=True)
                    next_refresh = time.monotonic() + getattr(self.current, 'refresh_interval', self.refresh)
                elif event.button in (
                    Button.LEFT,
                    Button.UP,
                    Button.OPTION_1,
                ):
                    self.previous_page()
                    self.display.render(self.current.render(), force=True)
                    next_refresh = time.monotonic() + getattr(self.current, 'refresh_interval', self.refresh)
                elif event.button is Button.OPTION_3:
                    self._enter_screensaver()
        finally:
            self.notification_server.close()

    def stop(self):
        self.running = False
