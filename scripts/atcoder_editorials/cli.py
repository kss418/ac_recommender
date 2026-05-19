"""CLI argument parsing and contest-list construction."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from atcoder_editorials.constants import DEFAULT_USER_AGENT, SUPPORTED_SERIES
from atcoder_editorials.contest import contest_id_from_range, normalize_contest_id


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch AtCoder editorials for ABC, ARC, and AGC contests."
    )
    parser.add_argument("contests", nargs="*", help="Contest IDs such as abc226, arc079, agc001.")
    parser.add_argument("--series", choices=sorted(SUPPORTED_SERIES), help="Build a contest range.")
    parser.add_argument("--from", dest="start", type=int, help="First contest number in the range.")
    parser.add_argument("--to", dest="end", type=int, help="Last contest number in the range.")
    parser.add_argument("--out", type=Path, default=Path("editorials"), help="Output root directory.")
    parser.add_argument("--lang", default="en", help="AtCoder UI language query value, or empty.")
    parser.add_argument(
        "--editorial-lang",
        choices=["en", "ja"],
        default="en",
        help="Primary AtCoder editorialLang query value. Defaults to English.",
    )
    parser.add_argument(
        "--fallback-editorial-lang",
        choices=["ja", "none"],
        default="ja",
        help="Fallback editorial language when the primary language has no links.",
    )
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between detail requests.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds.")
    parser.add_argument("--retries", type=int, default=2, help="Retry count for transient URL errors.")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT, help="HTTP User-Agent header.")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification; use only for local CA issues.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Only discover and print links.")
    parser.add_argument(
        "--max-editorials",
        type=int,
        default=None,
        help="Limit detail downloads per contest; useful while testing.",
    )
    return parser.parse_args(list(argv))


def build_contest_list(args: argparse.Namespace) -> list[str]:
    contests: list[str] = [normalize_contest_id(contest) for contest in args.contests]

    if args.series or args.start is not None or args.end is not None:
        if not (args.series and args.start is not None and args.end is not None):
            raise ValueError("--series, --from, and --to must be used together")
        start = min(args.start, args.end)
        end = max(args.start, args.end)
        contests.extend(contest_id_from_range(args.series, number) for number in range(start, end + 1))

    if not contests:
        raise ValueError("provide at least one contest id or a --series/--from/--to range")

    seen: set[str] = set()
    unique: list[str] = []
    for contest in contests:
        if contest not in seen:
            seen.add(contest)
            unique.append(contest)
    return unique
