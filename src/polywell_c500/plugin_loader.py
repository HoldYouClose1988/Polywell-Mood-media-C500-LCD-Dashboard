from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from types import ModuleType

from .page_api import Page, PageContext


BUILTIN_MODULES = (
    "polywell_c500.builtin_pages.overview",
    "polywell_c500.builtin_pages.storage",
    "polywell_c500.builtin_pages.network",
    "polywell_c500.builtin_pages.temperatures",
    "polywell_c500.builtin_pages.services",
)


def _page_class(module: ModuleType):
    cls = getattr(module, "PAGE_CLASS", None)
    if isinstance(cls, type) and issubclass(cls, Page):
        return cls
    return None


def discover_page_classes(plugin_dir: str | None = None) -> dict[str, type[Page]]:
    classes: dict[str, type[Page]] = {}

    for module_name in BUILTIN_MODULES:
        module = importlib.import_module(module_name)
        cls = _page_class(module)
        if cls is not None:
            classes[cls.name] = cls

    if not plugin_dir:
        return classes

    directory = Path(plugin_dir)
    if not directory.exists():
        return classes

    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue

        module_name = f"polywell_c500_external_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            cls = _page_class(module)
            if cls is None:
                logging.warning("Skipping page plugin without PAGE_CLASS: %s", path)
                continue
            classes[cls.name] = cls
        except Exception:
            logging.exception("Failed loading page plugin: %s", path)

    return classes


def build_pages(config: dict) -> list[Page]:
    plugin_dir = config.get("page_plugin_dir", "/etc/polywell-c500/pages")
    classes = discover_page_classes(plugin_dir)
    context = PageContext(config=config)
    pages: list[Page] = []

    for name in config.get(
        "pages",
        ["overview", "storage", "network", "temperatures", "services"],
    ):
        cls = classes.get(name)
        if cls is None:
            logging.warning("Configured page is unavailable: %s", name)
            continue
        try:
            pages.append(cls(context))
        except Exception:
            logging.exception("Failed initializing page: %s", name)

    if not pages:
        raise RuntimeError("No dashboard pages could be loaded")

    return pages
