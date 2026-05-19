#!/usr/bin/env python3
"""Create a zip archive containing docs/ir."""

from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zip docs/ir into an archive.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to ir-docs-YYMMDD-HHMMSS.zip in the repo root.",
    )
    return parser.parse_args(argv)


def zip_ir_docs(*, repo_root: Path, output: Path) -> Path:
    source_dir = repo_root / "docs" / "ir"
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")

    output_path = output if output.is_absolute() else repo_root / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())

    return output_path


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    output = args.output or Path(f"ir-docs-{datetime.now():%y%m%d-%H%M%S}.zip")
    output_path = zip_ir_docs(repo_root=repo_root, output=output)
    print(f"Created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
