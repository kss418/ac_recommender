#!/usr/bin/env python3
"""Create a zip archive containing the IR project bundle."""

from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zip the IR project bundle into an archive.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to project-bundle-YYMMDD-HHMMSS.zip in the repo root.",
    )
    return parser.parse_args(argv)


def zip_project_bundle(*, repo_root: Path, output: Path) -> Path:
    source_roots = [
        repo_root / "docs" / "ir",
        repo_root / "schema",
        repo_root / "scripts",
        repo_root / "taxonomies",
    ]
    for source_root in source_roots:
        if not source_root.is_dir():
            raise FileNotFoundError(f"Source directory not found: {source_root}")

    output_path = output if output.is_absolute() else repo_root / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source_root in source_roots:
            for path in sorted(source_root.rglob("*")):
                if path.is_file() and should_include_file(path):
                    archive.write(path, path.relative_to(repo_root).as_posix())

    return output_path


def should_include_file(path: Path) -> bool:
    if "__pycache__" in path.parts:
        return False
    return path.suffix != ".pyc"


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    output = args.output or Path(f"project-bundle-{datetime.now():%y%m%d-%H%M%S}.zip")
    output_path = zip_project_bundle(repo_root=repo_root, output=output)
    print(f"Created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
