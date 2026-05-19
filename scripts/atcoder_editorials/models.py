"""Data models passed between fetcher modules."""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class FetchResult:
    url: str
    status: int
    content_type: str
    body: bytes


@dataclasses.dataclass
class EditorialLink:
    url: str
    label: str
    section: str
    context: str = ""

    @property
    def kind(self) -> str:
        lowered = f"{self.context} {self.label}".lower()
        if "official" in lowered or "\u516c\u5f0f" in lowered:
            return "official"
        if "user editorial" in lowered or "user" in lowered or "\u30e6\u30fc\u30b6" in lowered:
            return "user"
        return "unknown"
