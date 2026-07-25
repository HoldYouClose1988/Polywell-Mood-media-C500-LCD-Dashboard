# Page Plugins

External dashboard pages are loaded from:

```text
/etc/polywell-c500/pages/
```

Each plugin is a Python file that exports `PAGE_CLASS`. The class must inherit
from `polywell_c500.page_api.Page`.

```python
from polywell_c500.page_api import Page


class ExamplePage(Page):
    name = "example"
    title = "Example"
    refresh_interval = 10.0

    def render(self):
        return [
            "EXAMPLE",
            "Line 2",
            "Line 3",
            "Line 4",
        ]


PAGE_CLASS = ExamplePage
```

## Requirements

- `name` must be unique.
- `render()` must return up to four strings.
- Each string is limited to 24 display characters.
- `refresh_interval` controls how often the active page is refreshed.
- Plugins should catch expected I/O failures and return useful fallback text.

## Installation

Copy the plugin:

```bash
sudo cp example.py /etc/polywell-c500/pages/
```

Enable the page using the TUI:

```bash
sudo /opt/polywell-c500/venv/bin/polywell-c500-config
```

Then restart the service if the configurator did not already do so:

```bash
sudo systemctl restart polywell-c500-dashboard
```

A clock example is included at:

```text
examples/pages/clock.py
```
