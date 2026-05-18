"""Shared constants for the AtCoder editorial fetcher."""

from __future__ import annotations

import re


ATCODER_BASE_URL = "https://atcoder.jp"
SUPPORTED_SERIES = {"abc", "arc", "agc"}
CONTEST_RE = re.compile(r"^(abc|arc|agc)(\d{3,})$", re.IGNORECASE)
DEFAULT_USER_AGENT = (
    "ac-recommender-editorial-fetcher/1.0 "
    "(compatible; contact: local-script)"
)
