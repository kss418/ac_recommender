#!/usr/bin/env python3
"""Analyze embedding .npy files and optional embedding metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class DocumentRecord:
    embedding_index: int
    embedding_id: str
    view: str | None
    metadata: JsonObject


@dataclass(frozen=True)
class PairRecord:
    similarity: float
    left: int
    right: int


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze embeddings.npy. If PATH is an embedding output directory, "
            "manifest.json and documents.jsonl are loaded automatically."
        )
    )
    parser.add_argument(
        "path",
        type=Path,
        help="Embedding output directory or .npy file.",
    )
    parser.add_argument(
        "--documents",
        type=Path,
        default=None,
        help="Optional documents.jsonl path. Auto-detected for directory inputs.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional manifest.json path. Auto-detected for directory inputs.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of nearest non-identical pairs to print. Defaults to 20.",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.995,
        help="Count pairs with cosine similarity at or above this value. Defaults to 0.995.",
    )
    parser.add_argument(
        "--exclude-same-problem",
        action="store_true",
        help="Exclude pairs whose documents share the same metadata.problem_id.",
    )
    parser.add_argument(
        "--no-pairs",
        action="store_true",
        help="Skip pairwise cosine analysis.",
    )
    parser.add_argument(
        "--pair-block-size",
        type=int,
        default=256,
        help="Rows per block for pairwise cosine analysis. Defaults to 256.",
    )
    parser.add_argument(
        "--max-pair-rows",
        type=int,
        default=5000,
        help="Skip pairwise analysis when row count exceeds this value. Defaults to 5000.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path to write a machine-readable JSON report.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        raise SystemExit("error: numpy is required. Install requirements.txt first.") from exc

    vector_path, documents_path, manifest_path = resolve_inputs(args)
    embeddings = np.load(vector_path)
    if embeddings.ndim != 2:
        raise SystemExit(f"error: expected a 2D embedding matrix, got shape {embeddings.shape}")

    documents = load_documents(documents_path) if documents_path else []
    manifest = load_json(manifest_path) if manifest_path else {}
    report = build_report(
        vector_path=vector_path,
        documents_path=documents_path,
        manifest_path=manifest_path,
        embeddings=embeddings,
        documents=documents,
        manifest=manifest,
        top_k=args.top_k,
        similarity_threshold=args.similarity_threshold,
        exclude_same_problem=args.exclude_same_problem,
        no_pairs=args.no_pairs,
        pair_block_size=args.pair_block_size,
        max_pair_rows=args.max_pair_rows,
    )

    print_report(report)
    if args.json_output is not None:
        write_json(args.json_output, report)
        print(f"\nWrote JSON report: {args.json_output}")
    return 0


def resolve_inputs(args: argparse.Namespace) -> tuple[Path, Path | None, Path | None]:
    path = args.path
    if path.is_dir():
        vector_path = path / "embeddings.npy"
        documents_path = args.documents or path / "documents.jsonl"
        manifest_path = args.manifest or path / "manifest.json"
    else:
        vector_path = path
        documents_path = args.documents
        manifest_path = args.manifest

    if not vector_path.is_file():
        raise SystemExit(f"error: embeddings file not found: {vector_path}")
    if documents_path is not None and not documents_path.is_file():
        documents_path = None
    if manifest_path is not None and not manifest_path.is_file():
        manifest_path = None
    return vector_path, documents_path, manifest_path


def load_documents(path: Path) -> list[DocumentRecord]:
    records: list[DocumentRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"error: invalid JSON at {path}:{line_number}: {exc}") from exc
        if not isinstance(data, dict):
            raise SystemExit(f"error: expected JSON object at {path}:{line_number}")
        index = data.get("embedding_index")
        if not isinstance(index, int):
            raise SystemExit(f"error: missing integer embedding_index at {path}:{line_number}")
        metadata = data.get("metadata")
        records.append(
            DocumentRecord(
                embedding_index=index,
                embedding_id=str(data.get("embedding_id") or index),
                view=str(data.get("view")) if data.get("view") is not None else None,
                metadata=metadata if isinstance(metadata, dict) else {},
            )
        )
    return records


def load_json(path: Path) -> JsonObject:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"error: expected JSON object: {path}")
    return data


def build_report(
    *,
    vector_path: Path,
    documents_path: Path | None,
    manifest_path: Path | None,
    embeddings: Any,
    documents: Sequence[DocumentRecord],
    manifest: JsonObject,
    top_k: int,
    similarity_threshold: float,
    exclude_same_problem: bool,
    no_pairs: bool,
    pair_block_size: int,
    max_pair_rows: int,
) -> JsonObject:
    import numpy as np

    row_count, dimension = embeddings.shape
    finite_mask = np.isfinite(embeddings)
    finite_rows = np.all(finite_mask, axis=1)
    row_norms = np.linalg.norm(np.nan_to_num(embeddings, copy=True), axis=1)

    report: JsonObject = {
        "files": {
            "vectors": str(vector_path),
            "documents": str(documents_path) if documents_path else None,
            "manifest": str(manifest_path) if manifest_path else None,
        },
        "matrix": {
            "shape": [int(row_count), int(dimension)],
            "dtype": str(embeddings.dtype),
            "bytes": int(embeddings.nbytes),
            "size_mb": round(embeddings.nbytes / (1024 * 1024), 3),
        },
        "finite": {
            "finite_values": int(finite_mask.sum()),
            "total_values": int(finite_mask.size),
            "nonfinite_values": int(finite_mask.size - finite_mask.sum()),
            "nonfinite_rows": [int(index) for index in np.flatnonzero(~finite_rows)[:50]],
        },
        "values": describe_array(embeddings[np.isfinite(embeddings)]),
        "row_norms": describe_array(row_norms),
        "zero_rows": [int(index) for index in np.flatnonzero(row_norms == 0.0)[:50]],
        "manifest": summarize_manifest(manifest, row_count, dimension),
        "documents": summarize_documents(documents, row_count),
        "exact_duplicates": exact_duplicate_summary(embeddings),
    }

    if not no_pairs:
        if row_count > max_pair_rows:
            report["pairwise"] = {
                "skipped": True,
                "reason": f"row count {row_count} exceeds --max-pair-rows {max_pair_rows}",
            }
        else:
            report["pairwise"] = analyze_pairs(
                embeddings=embeddings,
                documents=documents,
                top_k=top_k,
                threshold=similarity_threshold,
                exclude_same_problem=exclude_same_problem,
                block_size=pair_block_size,
            )
    else:
        report["pairwise"] = {"skipped": True, "reason": "--no-pairs"}

    return report


def describe_array(values: Any) -> JsonObject:
    import numpy as np

    if values.size == 0:
        return {"count": 0}
    percentiles = np.percentile(values, [0, 1, 5, 25, 50, 75, 95, 99, 100])
    return {
        "count": int(values.size),
        "min": float(percentiles[0]),
        "p01": float(percentiles[1]),
        "p05": float(percentiles[2]),
        "p25": float(percentiles[3]),
        "p50": float(percentiles[4]),
        "p75": float(percentiles[5]),
        "p95": float(percentiles[6]),
        "p99": float(percentiles[7]),
        "max": float(percentiles[8]),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
    }


def summarize_manifest(manifest: JsonObject, row_count: int, dimension: int) -> JsonObject:
    if not manifest:
        return {"loaded": False}
    expected_count = manifest.get("document_count")
    expected_dimension = manifest.get("vector_dimension")
    return {
        "loaded": True,
        "model_id": manifest.get("model_id"),
        "model_size": manifest.get("model_size"),
        "normalize_embeddings": manifest.get("normalize_embeddings"),
        "ir_count": manifest.get("ir_count"),
        "document_count": expected_count,
        "vector_dimension": expected_dimension,
        "views": manifest.get("views"),
        "document_count_matches": expected_count == row_count,
        "dimension_matches": expected_dimension == dimension,
    }


def summarize_documents(documents: Sequence[DocumentRecord], row_count: int) -> JsonObject:
    if not documents:
        return {"loaded": False}

    indices = [record.embedding_index for record in documents]
    view_counts = Counter(record.view or "" for record in documents)
    event_counts = Counter(str(record.metadata.get("event_id") or "") for record in documents)
    problem_ids = [str(record.metadata.get("problem_id") or "") for record in documents]
    problem_counts = Counter(problem_ids)
    missing_indices = sorted(set(range(row_count)) - set(indices))
    duplicate_indices = sorted(index for index, count in Counter(indices).items() if count > 1)
    out_of_range_indices = sorted(index for index in indices if index < 0 or index >= row_count)

    return {
        "loaded": True,
        "count": len(documents),
        "count_matches": len(documents) == row_count,
        "index_range": [min(indices), max(indices)] if indices else None,
        "missing_indices_sample": missing_indices[:50],
        "duplicate_indices_sample": duplicate_indices[:50],
        "out_of_range_indices_sample": out_of_range_indices[:50],
        "view_counts": sorted_counter(view_counts),
        "event_counts": sorted_counter(event_counts),
        "problem_count": len({problem_id for problem_id in problem_ids if problem_id}),
        "problems_with_multiple_records": sum(1 for count in problem_counts.values() if count > 1),
    }


def exact_duplicate_summary(embeddings: Any) -> JsonObject:
    duplicates: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(embeddings):
        digest = hashlib.sha256(row.tobytes()).hexdigest()
        duplicates[digest].append(index)
    groups = [indices for indices in duplicates.values() if len(indices) > 1]
    groups.sort(key=lambda indices: (-len(indices), indices[0]))
    return {
        "duplicate_group_count": len(groups),
        "duplicate_row_count": sum(len(indices) for indices in groups),
        "groups_sample": groups[:10],
    }


def analyze_pairs(
    *,
    embeddings: Any,
    documents: Sequence[DocumentRecord],
    top_k: int,
    threshold: float,
    exclude_same_problem: bool,
    block_size: int,
) -> JsonObject:
    import numpy as np

    if top_k < 0:
        raise SystemExit("error: --top-k must be non-negative")
    if block_size <= 0:
        raise SystemExit("error: --pair-block-size must be positive")

    normalized = normalize_rows(embeddings)
    row_count = normalized.shape[0]
    problem_ids = problem_ids_by_index(documents, row_count)
    top_pairs: list[PairRecord] = []
    above_threshold = 0
    compared_pairs = 0
    max_similarity = -math.inf

    for start in range(0, row_count, block_size):
        stop = min(start + block_size, row_count)
        scores = normalized[start:stop] @ normalized.T
        for local_i in range(stop - start):
            i = start + local_i
            row_scores = scores[local_i]
            row_scores[: i + 1] = -math.inf
            if exclude_same_problem and problem_ids is not None:
                same_problem = problem_ids == problem_ids[i]
                row_scores[same_problem] = -math.inf
            finite_scores = row_scores[np.isfinite(row_scores)]
            compared_pairs += int(finite_scores.size)
            if finite_scores.size:
                row_max = float(finite_scores.max())
                if row_max > max_similarity:
                    max_similarity = row_max
                above_threshold += int(np.count_nonzero(finite_scores >= threshold))
            if top_k:
                candidate_count = min(top_k, finite_scores.size)
                if candidate_count:
                    candidate_indices = np.argpartition(row_scores, -candidate_count)[-candidate_count:]
                    for j in candidate_indices:
                        score = float(row_scores[j])
                        if math.isfinite(score):
                            top_pairs.append(PairRecord(score, i, int(j)))
        if len(top_pairs) > top_k * 8:
            top_pairs = sorted(top_pairs, key=lambda pair: pair.similarity, reverse=True)[:top_k]

    top_pairs = sorted(top_pairs, key=lambda pair: pair.similarity, reverse=True)[:top_k]
    return {
        "skipped": False,
        "cosine_assumes_row_normalization": True,
        "exclude_same_problem": exclude_same_problem,
        "compared_pairs": compared_pairs,
        "max_similarity": None if max_similarity == -math.inf else max_similarity,
        "threshold": threshold,
        "pairs_at_or_above_threshold": above_threshold,
        "top_pairs": [format_pair(pair, documents) for pair in top_pairs],
    }


def normalize_rows(embeddings: Any) -> Any:
    import numpy as np

    matrix = np.nan_to_num(embeddings.astype("float32", copy=False), copy=True)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def problem_ids_by_index(documents: Sequence[DocumentRecord], row_count: int) -> Any:
    import numpy as np

    if not documents:
        return None
    problem_ids = np.array([""] * row_count, dtype=object)
    for record in documents:
        if 0 <= record.embedding_index < row_count:
            problem_ids[record.embedding_index] = str(record.metadata.get("problem_id") or "")
    return problem_ids


def format_pair(pair: PairRecord, documents: Sequence[DocumentRecord]) -> JsonObject:
    return {
        "similarity": pair.similarity,
        "left": format_document(pair.left, documents),
        "right": format_document(pair.right, documents),
    }


def format_document(index: int, documents: Sequence[DocumentRecord]) -> JsonObject:
    if not documents:
        return {"index": index}
    by_index = {record.embedding_index: record for record in documents}
    record = by_index.get(index)
    if record is None:
        return {"index": index}
    return {
        "index": index,
        "embedding_id": record.embedding_id,
        "view": record.view,
        "problem_id": record.metadata.get("problem_id"),
        "problem_name": record.metadata.get("problem_name"),
        "event_id": record.metadata.get("event_id"),
    }


def sorted_counter(counter: Counter[str]) -> list[JsonObject]:
    return [
        {"key": key, "count": count}
        for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        if key
    ]


def print_report(report: JsonObject) -> None:
    matrix = report["matrix"]
    finite = report["finite"]
    manifest = report["manifest"]
    documents = report["documents"]
    row_norms = report["row_norms"]
    values = report["values"]
    duplicates = report["exact_duplicates"]

    print("Embedding Analysis")
    print("==================")
    print(f"Vectors: {report['files']['vectors']}")
    print(f"Shape: {tuple(matrix['shape'])}")
    print(f"Dtype: {matrix['dtype']}")
    print(f"Size: {matrix['size_mb']} MiB")
    print(f"Non-finite values: {finite['nonfinite_values']} / {finite['total_values']}")
    if finite["nonfinite_rows"]:
        print(f"Non-finite rows sample: {finite['nonfinite_rows']}")

    print("\nRow Norms")
    print("---------")
    print(describe_line(row_norms))
    if row_norms.get("count"):
        max_abs_delta = max(abs(row_norms["min"] - 1.0), abs(row_norms["max"] - 1.0))
        print(f"Max abs deviation from unit norm: {max_abs_delta:.8f}")
    if report["zero_rows"]:
        print(f"Zero rows sample: {report['zero_rows']}")

    print("\nValues")
    print("------")
    print(describe_line(values))

    print("\nManifest")
    print("--------")
    if manifest.get("loaded"):
        print(f"Model: {manifest.get('model_id')}")
        print(f"IR documents: {manifest.get('ir_count')}")
        print(f"Embedding documents: {manifest.get('document_count')}")
        print(f"Vector dimension: {manifest.get('vector_dimension')}")
        print(f"Document count matches matrix: {manifest.get('document_count_matches')}")
        print(f"Dimension matches matrix: {manifest.get('dimension_matches')}")
    else:
        print("No manifest loaded.")

    print("\nDocuments")
    print("---------")
    if documents.get("loaded"):
        print(f"Document rows: {documents.get('count')}")
        print(f"Count matches matrix: {documents.get('count_matches')}")
        print(f"Problem count: {documents.get('problem_count')}")
        print("Views: " + format_counter(documents.get("view_counts", [])))
        print("Events: " + format_counter(documents.get("event_counts", [])))
        for key in ("missing_indices_sample", "duplicate_indices_sample", "out_of_range_indices_sample"):
            if documents.get(key):
                print(f"{key}: {documents[key]}")
    else:
        print("No documents.jsonl loaded.")

    print("\nExact Duplicates")
    print("----------------")
    print(f"Duplicate groups: {duplicates['duplicate_group_count']}")
    print(f"Duplicate rows: {duplicates['duplicate_row_count']}")
    if duplicates["groups_sample"]:
        print(f"Groups sample: {duplicates['groups_sample']}")

    print_pairwise(report.get("pairwise") or {})


def print_pairwise(pairwise: JsonObject) -> None:
    print("\nPairwise Cosine")
    print("---------------")
    if pairwise.get("skipped"):
        print(f"Skipped: {pairwise.get('reason')}")
        return
    print(f"Compared pairs: {pairwise.get('compared_pairs')}")
    print(f"Max similarity: {pairwise.get('max_similarity')}")
    print(
        f"Pairs >= {pairwise.get('threshold')}: "
        f"{pairwise.get('pairs_at_or_above_threshold')}"
    )
    top_pairs = pairwise.get("top_pairs") or []
    if not top_pairs:
        return
    print("Top pairs:")
    for pair in top_pairs:
        left = pair["left"]
        right = pair["right"]
        left_label = left.get("embedding_id") or left.get("index")
        right_label = right.get("embedding_id") or right.get("index")
        print(f"  {pair['similarity']:.6f}  {left_label}  <->  {right_label}")


def describe_line(summary: JsonObject) -> str:
    if not summary.get("count"):
        return "No finite values."
    return (
        f"min={summary['min']:.8f}, p50={summary['p50']:.8f}, "
        f"mean={summary['mean']:.8f}, p95={summary['p95']:.8f}, "
        f"max={summary['max']:.8f}, std={summary['std']:.8f}"
    )


def format_counter(items: Sequence[JsonObject]) -> str:
    if not items:
        return "(none)"
    return ", ".join(f"{item['key']}={item['count']}" for item in items)


def write_json(path: Path, data: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
