"""Persist fetched editorials and contest metadata."""

from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path

from atcoder_editorials.contest import contest_output_parts, source_id_from_url
from atcoder_editorials.http_client import decode_html, is_pdf
from atcoder_editorials.models import EditorialLink, FetchResult
from atcoder_editorials.parsing import html_to_markdown, title_from_markdown
from atcoder_editorials.text import clean_markdown, slugify


def record_for_link(link: EditorialLink, *, status: str) -> dict[str, object]:
    return {
        "status": status,
        "section": link.section,
        "label": link.label,
        "kind": link.kind,
        "context": link.context,
        "source_url": link.url,
    }


def save_editorial_response(
    result: FetchResult,
    link: EditorialLink,
    *,
    contest: str,
    out_dir: Path,
    fetched_at: str,
    duplicate_index: int,
) -> dict[str, object]:
    if is_pdf(result, result.url):
        return save_pdf_editorial(
            result,
            link,
            contest=contest,
            out_dir=out_dir,
            duplicate_index=duplicate_index,
        )
    return save_html_editorial(
        result,
        link,
        contest=contest,
        out_dir=out_dir,
        fetched_at=fetched_at,
        duplicate_index=duplicate_index,
    )


def save_pdf_editorial(
    result: FetchResult,
    link: EditorialLink,
    *,
    contest: str,
    out_dir: Path,
    duplicate_index: int,
) -> dict[str, object]:
    extension = mimetypes.guess_extension(result.content_type.split(";")[0].strip())
    if extension != ".pdf":
        extension = ".pdf"
    filename = f"{editorial_file_stem(link, duplicate_index=duplicate_index)}{extension}"
    path = contest_output_dir(out_dir, contest) / "assets" / filename
    save_binary(path, result.body)
    return {
        **record_for_link(link, status="saved"),
        "source_url": result.url,
        "content_type": result.content_type,
        "path": relative_path(path, out_dir),
    }


def save_html_editorial(
    result: FetchResult,
    link: EditorialLink,
    *,
    contest: str,
    out_dir: Path,
    fetched_at: str,
    duplicate_index: int,
) -> dict[str, object]:
    html = decode_html(result)
    body = html_to_markdown(html, base_url=result.url)
    if not body:
        body = clean_markdown(html)
    fallback_title = f"{link.section} {link.label}".strip() or source_id_from_url(result.url)
    title = title_from_markdown(body, fallback=fallback_title)
    filename = f"{editorial_file_stem(link, duplicate_index=duplicate_index)}.md"
    path = contest_output_dir(out_dir, contest) / filename
    write_markdown(
        path,
        contest=contest,
        source_url=result.url,
        fetched_at=fetched_at,
        title=title,
        body=body,
    )
    return {
        **record_for_link(link, status="saved"),
        "title": title,
        "source_url": result.url,
        "content_type": result.content_type,
        "path": relative_path(path, out_dir),
    }


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def contest_output_dir(out_dir: Path, contest: str) -> Path:
    series, number = contest_output_parts(contest)
    return out_dir / "ac" / series / number


def editorial_file_stem(link: EditorialLink, *, duplicate_index: int = 1) -> str:
    stem = problem_file_stem(link)
    if duplicate_index > 1:
        return f"{stem}-{duplicate_index}"
    return stem


def problem_file_stem(link: EditorialLink) -> str:
    match = re.fullmatch(r"\s*([A-Za-z0-9]+)\s*-\s*(.+?)\s*", link.section)
    if match:
        problem_number = match.group(1)
        problem_name = slugify(match.group(2))
        if problem_name:
            return f"{problem_number}-{problem_name}"

    fallback = slugify(link.section) or slugify(link.label) or "editorial"
    return fallback


def write_markdown(
    path: Path,
    *,
    contest: str,
    source_url: str,
    fetched_at: str,
    title: str,
    body: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    front_matter = {
        "contest": contest,
        "source_url": source_url,
        "fetched_at": fetched_at,
        "title": title,
    }
    lines = ["---"]
    for key, value in front_matter.items():
        escaped = str(value).replace('"', '\\"')
        lines.append(f'{key}: "{escaped}"')
    lines.extend(["---", "", body, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def save_binary(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def write_contest_index(out_dir: Path, contest: str, summary: dict[str, object]) -> None:
    contest_dir = contest_output_dir(out_dir, contest)
    contest_dir.mkdir(parents=True, exist_ok=True)
    (contest_dir / "index.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
