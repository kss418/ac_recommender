#!/usr/bin/env python3
"""Generate Qwen3 embeddings from Editorial IR documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence


JsonObject = dict[str, Any]
AVAILABLE_VIEWS = ("problem_identity", "solution_structure", "skill", "combined")
DEFAULT_VIEWS = ("solution_structure", "skill", "combined")
MODEL_ALIASES = {
    "0.6": "Qwen/Qwen3-Embedding-0.6B",
    "0.6b": "Qwen/Qwen3-Embedding-0.6B",
    "0.6B": "Qwen/Qwen3-Embedding-0.6B",
    "4": "Qwen/Qwen3-Embedding-4B",
    "4b": "Qwen/Qwen3-Embedding-4B",
    "4B": "Qwen/Qwen3-Embedding-4B",
    "8": "Qwen/Qwen3-Embedding-8B",
    "8b": "Qwen/Qwen3-Embedding-8B",
    "8B": "Qwen/Qwen3-Embedding-8B",
}


@dataclass(frozen=True)
class EmbeddingDocument:
    embedding_id: str
    view: str
    text: str
    metadata: JsonObject


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate embedding documents from Editorial IR according to "
            "docs/ir/embedding.md and embed them with Qwen3-Embedding."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("ir")],
        help="IR JSON files or directories. Defaults to ir/.",
    )
    parser.add_argument(
        "--model-size",
        default="0.6b",
        choices=sorted(MODEL_ALIASES),
        help="Qwen3 embedding size alias. Defaults to 0.6b.",
    )
    parser.add_argument(
        "--model-id",
        default=None,
        help="Override the Hugging Face model id.",
    )
    parser.add_argument(
        "--views",
        nargs="+",
        choices=AVAILABLE_VIEWS,
        default=list(DEFAULT_VIEWS),
        help=(
            "Embedding views to generate. Defaults to recommendation views "
            "(solution_structure, skill, combined)."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("embeddings"),
        help="Output root directory. Defaults to embeddings/.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="SentenceTransformer encode batch size.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional SentenceTransformer device, for example cuda, cpu, or mps.",
    )
    parser.add_argument(
        "--dimensions",
        type=int,
        default=None,
        help="Optional output dimension. If smaller than the model output, vectors are truncated and renormalized.",
    )
    parser.add_argument(
        "--max-seq-length",
        type=int,
        default=None,
        help="Optional model max sequence length override.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Do not L2-normalize embeddings.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of IR files before view expansion. Useful for smoke tests.",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Write embedding documents and manifest without loading the model or writing vectors.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated embedding texts without writing files or loading the model.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output directory.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    model_id = args.model_id or MODEL_ALIASES[args.model_size]
    ir_paths = list(load_ir_paths(repo_root, args.paths))
    if args.limit is not None:
        ir_paths = ir_paths[: args.limit]
    if not ir_paths:
        print("error: no IR JSON files found", file=sys.stderr)
        return 2

    documents = [
        document
        for ir_path in ir_paths
        for document in build_documents(ir_path, repo_root=repo_root, views=args.views)
    ]
    if args.dry_run:
        print(f"IR files: {len(ir_paths)}")
        print(f"Embedding documents: {len(documents)}")
        for document in documents:
            print(f"\n--- {document.embedding_id} [{document.view}] ---")
            print(document.text)
        return 0

    output_dir = make_output_dir(
        repo_root=repo_root,
        output_root=args.output_root,
        model_size=args.model_size,
        views=args.views,
        overwrite=args.overwrite,
    )
    write_documents(output_dir / "documents.jsonl", documents)

    manifest = build_manifest(
        args=args,
        model_id=model_id,
        ir_count=len(ir_paths),
        documents=documents,
        vector_dimension=None,
        vector_file=None,
    )
    if args.text_only:
        write_json(output_dir / "manifest.json", manifest)
        print(f"Wrote {len(documents)} embedding document(s) to {output_dir}")
        print("Text-only mode: embeddings.npy was not generated.")
        return 0

    embeddings = encode_documents(
        model_id=model_id,
        texts=[document.text for document in documents],
        batch_size=args.batch_size,
        device=args.device,
        normalize=not args.no_normalize,
        dimensions=args.dimensions,
        max_seq_length=args.max_seq_length,
    )
    vector_path = output_dir / "embeddings.npy"
    save_vectors(vector_path, embeddings)
    manifest["vector_dimension"] = int(embeddings.shape[1])
    manifest["vector_file"] = vector_path.name
    write_json(output_dir / "manifest.json", manifest)
    print(f"Wrote {len(documents)} embedding document(s) to {output_dir}")
    print(f"Vector dimension: {embeddings.shape[1]}")
    return 0


def load_ir_paths(repo_root: Path, paths: Sequence[Path]) -> Iterator[Path]:
    for path in paths:
        resolved = path if path.is_absolute() else repo_root / path
        if resolved.is_dir():
            yield from sorted(
                child
                for child in resolved.rglob("*.json")
                if "__pycache__" not in child.parts
            )
        elif resolved.is_file():
            yield resolved
        else:
            raise SystemExit(f"error: path not found: {path}")


def build_documents(path: Path, *, repo_root: Path, views: Sequence[str]) -> list[EmbeddingDocument]:
    data = load_json(path)
    relative_path = path.relative_to(repo_root).as_posix()
    metadata = build_metadata(data, relative_path=relative_path)
    documents: list[EmbeddingDocument] = []
    for view in views:
        text = build_view_text(data, view)
        if not text:
            continue
        embedding_id = f"{metadata['problem_id']}#{view}"
        documents.append(
            EmbeddingDocument(
                embedding_id=embedding_id,
                view=view,
                text=text,
                metadata={**metadata, "view": view},
            )
        )
    return documents


def build_metadata(data: JsonObject, *, relative_path: str) -> JsonObject:
    platform = data.get("platform") or {}
    event = data.get("event") or {}
    problem = data.get("problem") or {}
    difficulty = problem.get("difficulty") or {}
    source = data.get("source") or {}
    return omit_nulls(
        {
            "ir_path": relative_path,
            "ir_version": data.get("ir_version"),
            "ir_language": data.get("ir_language"),
            "platform": platform.get("name"),
            "event_id": event.get("id"),
            "event_series": event.get("series"),
            "event_number": event.get("number"),
            "problem_id": problem.get("id"),
            "problem_index": problem.get("index"),
            "problem_name": problem.get("name"),
            "problem_url": problem.get("url"),
            "difficulty_rating": difficulty.get("rating"),
            "difficulty_source": difficulty.get("source"),
            "source_kind": source.get("kind"),
            "source_author": source.get("author"),
            "source_fetched_at": source.get("fetched_at"),
        }
    )


def build_view_text(data: JsonObject, view: str) -> str:
    if view == "problem_identity":
        return build_problem_identity_text(data)
    if view == "solution_structure":
        return build_solution_structure_text(data)
    if view == "skill":
        return build_skill_text(data)
    if view == "combined":
        return build_combined_text(data)
    raise ValueError(f"unknown view: {view}")


def build_problem_identity_text(data: JsonObject) -> str:
    platform = data.get("platform") or {}
    event = data.get("event") or {}
    problem = data.get("problem") or {}
    problem_label = join_nonempty(" - ", [problem.get("index"), problem.get("name")])
    return join_lines(
        [
            line("Platform", platform.get("name")),
            line("Event", event.get("id")),
            line("Problem", problem_label),
        ]
    )


def build_solution_structure_text(data: JsonObject) -> str:
    solution = data.get("solution") or {}
    signature = solution.get("solution_signature") or {}
    complexity = solution.get("complexity") or {}
    time = complexity.get("time") or {}
    return join_lines(
        [
            line("Primary paradigm", solution.get("primary_paradigm")),
            line("Specific paradigm", solution.get("specific_paradigm")),
            line("Algorithm template", solution.get("algorithm_template")),
            line("Solution models", ids_from_weighted(solution.get("solution_models"))),
            line("Main object", signature.get("main_object")),
            line("Main condition", signature.get("main_condition")),
            line("Structural property", signature.get("structural_property")),
            line("Update or transition", signature.get("update_or_transition")),
            line("Answer extraction", signature.get("answer_extraction")),
            line("Template-specific", compact_value(solution.get("template_specific"))),
            line("Core computations", compact_core_computations(solution.get("core_computations"))),
            line("Complexity", compact_complexity(time)),
        ]
    )


def build_skill_text(data: JsonObject) -> str:
    solution = data.get("solution") or {}
    grouped = group_skill_atoms(solution.get("skill_atoms"))
    return join_lines(
        [
            line("Primary skills", grouped.get("primary")),
            line("Supporting skills", grouped.get("supporting")),
            line("Incidental skills", grouped.get("incidental")),
            line("Paradigm", solution.get("primary_paradigm")),
            line("Specific paradigm", solution.get("specific_paradigm")),
            line("Template", solution.get("algorithm_template")),
        ]
    )


def build_combined_text(data: JsonObject) -> str:
    problem = data.get("problem") or {}
    solution = data.get("solution") or {}
    signature = solution.get("solution_signature") or {}
    signature_parts = [
        signature.get("main_object"),
        signature.get("main_condition"),
        signature.get("structural_property"),
        signature.get("answer_extraction"),
    ]
    return join_lines(
        [
            line("Problem", problem.get("name")),
            line("Paradigm", solution.get("primary_paradigm")),
            line("Specific paradigm", solution.get("specific_paradigm")),
            line("Template", solution.get("algorithm_template")),
            line("Solution models", ids_from_weighted(solution.get("solution_models"))),
            line("Skills", ids_from_weighted(solution.get("skill_atoms"))),
            line("Signature", join_nonempty("; ", signature_parts)),
            line("Core computations", compact_core_computations(solution.get("core_computations"))),
        ]
    )


def group_skill_atoms(skill_atoms: Any) -> dict[str, str]:
    if not isinstance(skill_atoms, list):
        return {}
    role_order = {"primary": 0, "supporting": 1, "incidental": 2}
    grouped: dict[str, list[str]] = {"primary": [], "supporting": [], "incidental": []}
    sorted_atoms = sorted(
        (atom for atom in skill_atoms if isinstance(atom, dict)),
        key=lambda atom: (
            role_order.get(str(atom.get("role")), 99),
            -float(atom.get("weight") or 0.0),
            str(atom.get("id") or ""),
        ),
    )
    for atom in sorted_atoms:
        role = atom.get("role")
        atom_id = atom.get("id")
        if role in grouped and atom_id:
            grouped[role].append(str(atom_id))
    return {role: ", ".join(ids) for role, ids in grouped.items() if ids}


def ids_from_weighted(items: Any) -> str | None:
    if not isinstance(items, list):
        return None
    ids = [str(item.get("id")) for item in items if isinstance(item, dict) and item.get("id")]
    return ", ".join(ids) if ids else None


def compact_core_computations(items: Any) -> str | None:
    if not isinstance(items, list):
        return None
    parts: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        expression = item.get("expression")
        role = item.get("role")
        if name and expression and role:
            parts.append(f"{name} = {expression} ({role})")
        elif name and expression:
            parts.append(f"{name} = {expression}")
        elif expression:
            parts.append(str(expression))
    return "; ".join(parts) if parts else None


def compact_complexity(time: Any) -> str | None:
    if not isinstance(time, dict):
        return None
    raw = time.get("raw")
    variables = time.get("variables")
    if not raw:
        return None
    if not isinstance(variables, dict) or not variables:
        return str(raw)
    definitions = ", ".join(f"{key} is {value}" for key, value in sorted(variables.items()))
    return f"{raw}, where {definitions}"


def compact_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [compact_value(item) for item in value]
        return ", ".join(part for part in parts if part)
    if isinstance(value, dict):
        parts: list[str] = []
        for key in sorted(value):
            item = value[key]
            if item is None or key == "type":
                continue
            compacted = compact_value(item)
            if compacted:
                parts.append(f"{key}: {compacted}")
        return "; ".join(parts) if parts else str(value.get("type") or "")
    return str(value)


def line(label: str, value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    if value == "":
        return None
    return f"{label}: {value}"


def join_lines(lines: Iterable[str | None]) -> str:
    return "\n".join(item for item in lines if item)


def join_nonempty(separator: str, values: Iterable[Any]) -> str:
    return separator.join(str(value) for value in values if value is not None and str(value) != "")


def omit_nulls(value: JsonObject) -> JsonObject:
    return {key: item for key, item in value.items() if item is not None}


def make_output_dir(
    *,
    repo_root: Path,
    output_root: Path,
    model_size: str,
    views: Sequence[str],
    overwrite: bool,
) -> Path:
    root = output_root if output_root.is_absolute() else repo_root / output_root
    view_part = "all" if tuple(views) == DEFAULT_VIEWS else "-".join(views)
    output_dir = root / f"qwen3-embedding-{canonical_model_size(model_size)}-{view_part}"
    if output_dir.exists():
        if not overwrite:
            raise SystemExit(f"error: output directory exists: {output_dir} (pass --overwrite)")
        remove_generated_outputs(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def canonical_model_size(model_size: str) -> str:
    normalized = model_size.lower()
    if normalized in {"0.6", "0.6b"}:
        return "0.6b"
    if normalized in {"4", "4b"}:
        return "4b"
    if normalized in {"8", "8b"}:
        return "8b"
    raise SystemExit(f"error: unsupported model size: {model_size}")


def remove_generated_outputs(output_dir: Path) -> None:
    for filename in ("documents.jsonl", "embeddings.npy", "manifest.json"):
        path = output_dir / filename
        if path.exists():
            path.unlink()


def write_documents(path: Path, documents: Sequence[EmbeddingDocument]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for index, document in enumerate(documents):
            record = {
                "embedding_index": index,
                "embedding_id": document.embedding_id,
                "view": document.view,
                "text": document.text,
                "text_sha256": sha256_text(document.text),
                "metadata": document.metadata,
            }
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_manifest(
    *,
    args: argparse.Namespace,
    model_id: str,
    ir_count: int,
    documents: Sequence[EmbeddingDocument],
    vector_dimension: int | None,
    vector_file: str | None,
) -> JsonObject:
    return omit_nulls(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Editorial IR v1",
            "embedding_text_rules": "docs/ir/embedding.md",
            "model_size": canonical_model_size(args.model_size),
            "model_id": model_id,
            "views": list(args.views),
            "ir_count": ir_count,
            "document_count": len(documents),
            "documents_file": "documents.jsonl",
            "vector_file": vector_file,
            "vector_dimension": vector_dimension,
            "normalize_embeddings": not args.no_normalize,
            "requested_dimensions": args.dimensions,
            "batch_size": args.batch_size,
            "max_seq_length": args.max_seq_length,
            "query_instruction": (
                "Instruct: Given a competitive programming solution query, "
                "retrieve relevant Editorial IR embedding documents.\nQuery: {query}"
            ),
        }
    )


def encode_documents(
    *,
    model_id: str,
    texts: Sequence[str],
    batch_size: int,
    device: str | None,
    normalize: bool,
    dimensions: int | None,
    max_seq_length: int | None,
) -> Any:
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "error: embedding dependencies are missing. Install them with "
            "`.\\.venv\\bin\\python -m pip install -r requirements.txt`."
        ) from exc

    model_kwargs = {"device": device} if device else {}
    model = SentenceTransformer(model_id, **model_kwargs)
    if max_seq_length is not None:
        model.max_seq_length = max_seq_length

    embeddings = model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    if dimensions is not None:
        if dimensions <= 0:
            raise SystemExit("error: --dimensions must be positive")
        if dimensions > embeddings.shape[1]:
            raise SystemExit(
                f"error: --dimensions {dimensions} exceeds model output dimension {embeddings.shape[1]}"
            )
        embeddings = embeddings[:, :dimensions]
        if normalize:
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0.0] = 1.0
            embeddings = embeddings / norms
    return embeddings


def save_vectors(path: Path, embeddings: Any) -> None:
    try:
        import numpy as np
    except ModuleNotFoundError as exc:
        raise SystemExit("error: numpy is required to write embeddings.npy") from exc
    np.save(path, embeddings)


def write_json(path: Path, data: JsonObject) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(path: Path) -> JsonObject:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"error: expected JSON object: {path}")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
