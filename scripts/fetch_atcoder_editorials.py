#!/usr/bin/env python3
"""Orchestrate fetching AtCoder editorials for ABC, ARC, and AGC contests."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from atcoder_editorials.cli import build_contest_list, parse_args
from atcoder_editorials.contest import contest_index_url, with_language_params
from atcoder_editorials.http_client import decode_html, fetch_url, is_tls_certificate_error
from atcoder_editorials.parsing import extract_editorial_links, is_english_editorial_link
from atcoder_editorials.storage import (
    editorial_file_stem,
    record_for_link,
    save_editorial_response,
    write_contest_index,
)


def fetch_contest(
    contest: str,
    *,
    out_dir: Path,
    lang: str | None,
    editorial_lang: str | None,
    delay: float,
    timeout: float,
    retries: int,
    user_agent: str,
    verify_tls: bool,
    dry_run: bool,
    max_editorials: int | None,
) -> dict[str, object]:
    fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    index_url = contest_index_url(contest, lang=lang, editorial_lang=editorial_lang)

    print(f"[{contest}] fetching index: {index_url}", file=sys.stderr)
    index_result = fetch_url(
        index_url,
        timeout=timeout,
        retries=retries,
        user_agent=user_agent,
        verify_tls=verify_tls,
    )
    links = extract_editorial_links(
        decode_html(index_result),
        base_url=index_result.url,
        contest=contest,
    )
    links = [link for link in links if is_english_editorial_link(link)]
    for link in links:
        link.url = with_language_params(
            link.url,
            lang=lang,
            editorial_lang=editorial_lang,
        )
    if max_editorials is not None:
        links = links[:max_editorials]

    records: list[dict[str, object]] = []
    filename_counts: dict[str, int] = {}
    for number, link in enumerate(links, start=1):
        base_file_stem = editorial_file_stem(link)
        filename_counts[base_file_stem] = filename_counts.get(base_file_stem, 0) + 1
        duplicate_index = filename_counts[base_file_stem]

        print(
            f"[{contest}] discovered: {link.section} / {link.label} -> {link.url}",
            file=sys.stderr,
        )
        if dry_run:
            records.append(record_for_link(link, status="discovered"))
            continue

        if delay and number > 1:
            time.sleep(delay)
        result = fetch_url(
            link.url,
            timeout=timeout,
            retries=retries,
            user_agent=user_agent,
            verify_tls=verify_tls,
        )
        records.append(
            save_editorial_response(
                result,
                link,
                contest=contest,
                out_dir=out_dir,
                fetched_at=fetched_at,
                duplicate_index=duplicate_index,
            )
        )

    summary: dict[str, object] = {
        "contest": contest,
        "index_url": index_result.url,
        "fetched_at": fetched_at,
        "editorial_count": len(records),
        "editorials": records,
    }
    if not dry_run:
        write_contest_index(out_dir, contest, summary)
    return summary


def main(argv: Iterable[str] = sys.argv[1:]) -> int:
    try:
        args = parse_args(argv)
        contests = build_contest_list(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    summaries: list[dict[str, object]] = []
    lang = args.lang or None
    for index, contest in enumerate(contests, start=1):
        if args.delay and index > 1:
            time.sleep(args.delay)
        try:
            summaries.append(
                fetch_contest(
                    contest,
                    out_dir=args.out,
                    lang=lang,
                    editorial_lang=args.editorial_lang,
                    delay=args.delay,
                    timeout=args.timeout,
                    retries=args.retries,
                    user_agent=args.user_agent,
                    verify_tls=not args.insecure,
                    dry_run=args.dry_run,
                    max_editorials=args.max_editorials,
                )
            )
        except urllib.error.HTTPError as exc:
            print(f"[{contest}] HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        except urllib.error.URLError as exc:
            print(f"[{contest}] URL error: {exc.reason}", file=sys.stderr)
            if not args.insecure and is_tls_certificate_error(exc):
                print(
                    f"[{contest}] TLS certificate verification failed. "
                    "This Python environment cannot find a valid CA bundle; "
                    "retry with --insecure or install/update CA certificates.",
                    file=sys.stderr,
                )

    total = sum(int(summary.get("editorial_count", 0)) for summary in summaries)
    print(json.dumps({"contest_count": len(summaries), "editorial_count": total}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
