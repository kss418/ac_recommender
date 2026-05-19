"""Contest id validation and AtCoder editorial URL helpers."""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

from atcoder_editorials.constants import ATCODER_BASE_URL, CONTEST_RE, SUPPORTED_SERIES


def normalize_contest_id(value: str) -> str:
    match = CONTEST_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(
            f"unsupported contest id '{value}'. Expected abcNNN, arcNNN, or agcNNN."
        )
    return f"{match.group(1).lower()}{match.group(2)}"


def contest_id_from_range(series: str, number: int) -> str:
    series = series.lower()
    if series not in SUPPORTED_SERIES:
        raise ValueError(f"unsupported series '{series}'")
    if number <= 0:
        raise ValueError("contest number must be positive")
    return f"{series}{number:03d}"


def contest_output_parts(contest: str) -> tuple[str, str]:
    match = CONTEST_RE.fullmatch(contest)
    if not match:
        raise ValueError(f"unsupported contest id '{contest}'")
    return match.group(1).lower(), match.group(2)


def contest_index_url(contest: str, *, lang: str | None, editorial_lang: str | None) -> str:
    params: dict[str, str] = {}
    if editorial_lang:
        params["editorialLang"] = editorial_lang
    if lang:
        params["lang"] = lang
    query = urllib.parse.urlencode(params)
    url = f"{ATCODER_BASE_URL}/contests/{contest}/editorial"
    return f"{url}?{query}" if query else url


def is_editorial_source_url(url: str, contest: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lower()
    contest = contest.lower()
    match = CONTEST_RE.fullmatch(contest)
    if not match:
        return False

    if re.fullmatch(rf"/contests/{re.escape(contest)}/editorial/\d+", path):
        return True
    if re.fullmatch(rf"/contests/{re.escape(contest)}/tasks/[^/]+/editorial", path):
        return True

    if path.endswith(".pdf") and "editorial" in path:
        series, number = match.groups()
        compact = f"{series}{number}"
        split_style = f"/{series}/{number}/"
        return compact in path or split_style in path
    return False


def canonicalize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered_query = urllib.parse.urlencode(
        [(key, value) for key, value in query_pairs if key in {"lang", "editorialLang"}]
    )
    return urllib.parse.urlunparse(
        (
            parsed.scheme or "https",
            parsed.netloc,
            parsed.path,
            "",
            filtered_query,
            "",
        )
    )


def with_language_params(url: str, *, lang: str | None, editorial_lang: str | None) -> str:
    parsed = urllib.parse.urlparse(url)
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query: dict[str, str] = {
        key: value
        for key, value in query_pairs
        if key not in {"lang", "editorialLang"}
    }
    if editorial_lang:
        query["editorialLang"] = editorial_lang
    if lang:
        query["lang"] = lang
    return urllib.parse.urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urllib.parse.urlencode(query),
            parsed.fragment,
        )
    )


def source_id_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    if match := re.search(r"/editorial/(\d+)$", path):
        return f"editorial-{match.group(1)}"
    if match := re.search(r"/tasks/([^/]+)/editorial$", path):
        return f"task-{match.group(1)}"
    stem = Path(path).stem
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "editorial"
