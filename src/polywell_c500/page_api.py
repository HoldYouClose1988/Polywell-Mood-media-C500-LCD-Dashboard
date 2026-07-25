from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PageContext:
    config: dict[str, Any]


class Page(ABC):
    """
    Base class for dashboard page plugins.

    Required:
      name: unique plugin identifier
      render(): return up to four strings

    Optional:
      refresh_interval: seconds between refreshes while this page is active
      title: human-readable name for the configurator
    """

    name = "page"
    title = "Page"
    refresh_interval = 1.0

    def __init__(self, context: PageContext):
        self.context = context

    @abstractmethod
    def render(self) -> list[str]:
        raise NotImplementedError
