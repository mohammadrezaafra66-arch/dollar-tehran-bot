"""Selector registry for Divar extraction.

Divar page structure can change over time. This registry centralizes selectors
and fallback chains so extractor code does not hard-code DOM assumptions in many
places.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SelectorGroup:
    """Fallback selector group for one extraction field."""

    field_name: str
    selectors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class DivarSelectorSet:
    """Versioned selector set for Divar pages."""

    version: str
    groups: Dict[str, SelectorGroup]

    def selectors_for(self, field_name: str) -> List[str]:
        """Return fallback selectors for a field."""

        group = self.groups.get(field_name)
        return group.selectors if group else []


class DivarSelectorRegistry:
    """Loads selector sets from config with safe defaults."""

    DEFAULT = DivarSelectorSet(
        version="default-v1",
        groups={
            "title": SelectorGroup("title", ["h1", "[data-testid='post-title']"]),
            "description": SelectorGroup("description", ["[data-testid='post-description']", "article", "main"]),
            "price": SelectorGroup("price", ["[data-testid='post-price']", "main"]),
            "location": SelectorGroup("location", ["[data-testid='post-location']", "main"]),
            "contact_button": SelectorGroup("contact_button", ["button", "[role='button']"]),
            "body": SelectorGroup("body", ["body"]),
        },
    )

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path or Path(os.getenv("DIVAR_SELECTOR_CONFIG", "configs/divar_selectors.json"))
        self.selector_set = self._load()

    def selectors_for(self, field_name: str) -> List[str]:
        """Return selectors for a field from active selector set."""

        return self.selector_set.selectors_for(field_name)

    def snapshot(self) -> Dict[str, object]:
        """Return active selector registry snapshot."""

        return {
            "version": self.selector_set.version,
            "fields": {key: group.selectors for key, group in self.selector_set.groups.items()},
        }

    def _load(self) -> DivarSelectorSet:
        if not self.config_path.exists():
            return self.DEFAULT

        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            groups = {
                key: SelectorGroup(field_name=key, selectors=list(value))
                for key, value in data.get("groups", {}).items()
            }
            return DivarSelectorSet(
                version=str(data.get("version", "custom")),
                groups={**self.DEFAULT.groups, **groups},
            )
        except Exception:
            return self.DEFAULT
