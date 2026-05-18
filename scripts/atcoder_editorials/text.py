"""Text normalization and filename helpers."""

from __future__ import annotations

import re


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" +([,.!?;:])", r"\1", text)
    return text.strip()


def slugify(text: str, *, max_length: int = 72) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:max_length].strip("-")
