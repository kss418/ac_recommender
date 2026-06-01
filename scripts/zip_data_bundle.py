#!/usr/bin/env python3
"""Create separate zip archives for generated editorial, IR, and embedding data."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Zip editorial, IR, and embedding data into separate archives."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=(
            "Output zip base path. Defaults to data-bundle-YYMMDD-HHMMSS.zip in "
            "the repo root; suffixes like -editorials.zip, -embeddings.zip, "
            "and -ir.zip are added."
        ),
    )
    return parser.parse_args(argv)


def zip_data_bundle(*, repo_root: Path, output: Path) -> list[Path]:
    source_roots = [
        ("editorials", repo_root / "editorials"),
        ("embeddings", repo_root / "embeddings"),
        ("ir", repo_root / "ir"),
    ]
    for _, source_root in source_roots:
        if not source_root.is_dir():
            raise FileNotFoundError(f"Source directory not found: {source_root}")

    output_base = output if output.is_absolute() else repo_root / output
    output_base.parent.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=len(source_roots)) as executor:
        futures = [
            executor.submit(
                zip_source_root,
                repo_root=repo_root,
                output_base=output_base,
                bundle_name=bundle_name,
                source_root=source_root,
            )
            for bundle_name, source_root in source_roots
        ]
        return [future.result() for future in futures]


def zip_source_root(
    *,
    repo_root: Path,
    output_base: Path,
    bundle_name: str,
    source_root: Path,
) -> Path:
    output_path = bundle_output_path(output_base, bundle_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=1,
    ) as archive:
        write_directory_entry(archive, source_root.relative_to(repo_root))
        for path in sorted(source_root.rglob("*")):
            if path.is_dir():
                if should_include_dir(path):
                    write_directory_entry(archive, path.relative_to(repo_root))
            elif should_include_file(path):
                archive.write(
                    path,
                    path.relative_to(repo_root).as_posix(),
                    compress_type=compression_for_file(path),
                )
    return output_path


def bundle_output_path(output_base: Path, bundle_name: str) -> Path:
    if output_base.suffix == ".zip":
        return output_base.with_name(f"{output_base.stem}-{bundle_name}.zip")
    return output_base / f"{bundle_name}.zip"


def write_directory_entry(archive: zipfile.ZipFile, path: Path) -> None:
    archive.writestr(path.as_posix().rstrip("/") + "/", b"")


def should_include_dir(path: Path) -> bool:
    return "__pycache__" not in path.parts


def should_include_file(path: Path) -> bool:
    if "__pycache__" in path.parts:
        return False
    return path.suffix != ".pyc"


def compression_for_file(path: Path) -> int:
    if path.suffix.lower() in {".npy", ".zip"}:
        return zipfile.ZIP_STORED
    return zipfile.ZIP_DEFLATED


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    output = args.output or Path(f"data-bundle-{datetime.now():%y%m%d-%H%M%S}.zip")
    output_paths = zip_data_bundle(repo_root=repo_root, output=output)
    for output_path in output_paths:
        print(f"Created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
