#!/usr/bin/env python3
"""Create a zip archive containing the frontend source bundle."""

from __future__ import annotations

import argparse
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable


REQUIRED_FILES = [
    "index.html",
    "package.json",
    "vite.config.js",
]

OPTIONAL_FILES = [
    "package-lock.json",
]

SOURCE_DIRS = [
    "src",
    "public",
]

EXCLUDED_DIR_NAMES = {
    "node_modules",
    "frontend-dist",
    "dist",
    "__pycache__",
}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Zip frontend source files into an archive.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output zip path. Defaults to frontend-bundle-YYMMDD-HHMMSS.zip in the repo root.",
    )
    return parser.parse_args(argv)


def zip_frontend_bundle(*, repo_root: Path, output: Path) -> Path:
    for filename in REQUIRED_FILES:
        path = repo_root / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required frontend file not found: {path}")

    if not (repo_root / "src").is_dir():
        raise FileNotFoundError(f"Required frontend directory not found: {repo_root / 'src'}")

    output_path = output if output.is_absolute() else repo_root / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in REQUIRED_FILES + OPTIONAL_FILES:
            path = repo_root / filename
            if path.is_file() and should_include_file(path):
                archive.write(path, path.relative_to(repo_root).as_posix())

        for dirname in SOURCE_DIRS:
            source_root = repo_root / dirname
            if not source_root.is_dir():
                continue

            write_directory_entry(archive, source_root.relative_to(repo_root))
            for path in sorted(source_root.rglob("*")):
                if path.is_dir():
                    if should_include_dir(path):
                        write_directory_entry(archive, path.relative_to(repo_root))
                elif should_include_file(path):
                    archive.write(path, path.relative_to(repo_root).as_posix())

    return output_path


def write_directory_entry(archive: zipfile.ZipFile, path: Path) -> None:
    archive.writestr(path.as_posix().rstrip("/") + "/", b"")


def should_include_dir(path: Path) -> bool:
    return not any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def should_include_file(path: Path) -> bool:
    if not should_include_dir(path.parent):
        return False
    if path.suffix == ".pyc":
        return False
    return True


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    output = args.output or Path(f"frontend-bundle-{datetime.now():%y%m%d-%H%M%S}.zip")
    output_path = zip_frontend_bundle(repo_root=repo_root, output=output)
    print(f"Created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
