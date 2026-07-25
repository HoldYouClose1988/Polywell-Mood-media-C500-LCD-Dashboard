import subprocess

from polywell_c500.page_api import Page


class ServicesPage(Page):
    name = "services"
    title = "Services"
    refresh_interval = 5.0

    def _state(self, service):
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception:
            return "ERR"
        return "OK" if result.stdout.strip() == "active" else "DOWN"

    def render(self):
        services = self.context.config.get("services", ["smbd", "ssh", "docker"])
        rows = ["SERVICES"]
        for service in services[:3]:
            rows.append(f"{service[:16]} {self._state(service)}")
        while len(rows) < 4:
            rows.append("")
        return rows


PAGE_CLASS = ServicesPage
