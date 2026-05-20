#!/usr/bin/env python3
"""Validate Editorial IR JSON files against schema and taxonomy ids."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Iterator


JsonObject = dict[str, Any]
PRIMARY_PARADIGMS = {
    "implementation",
    "brute_force",
    "math",
    "greedy",
    "binary_search",
    "dp",
    "graph",
    "data_structure",
    "string",
    "constructive",
}


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Editorial IR JSON files and taxonomy references."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="IR JSON files or directories containing IR JSON files.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schema/editorial-ir-v1.schema.json"),
        help="JSON Schema path.",
    )
    parser.add_argument(
        "--solution-models",
        type=Path,
        default=Path("taxonomies/solution-models.json"),
        help="Solution model taxonomy JSON path.",
    )
    parser.add_argument(
        "--skill-atoms",
        type=Path,
        default=Path("taxonomies/skill-atoms"),
        help="Skill atom taxonomy JSON path or directory.",
    )
    parser.add_argument(
        "--examples-md",
        type=Path,
        default=None,
        help="Validate IR JSON code blocks from an examples Markdown file.",
    )
    parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="Skip JSON Schema validation and run taxonomy reference validation only.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]

    schema_path = resolve_path(repo_root, args.schema)
    solution_models_path = resolve_path(repo_root, args.solution_models)
    skill_atoms_path = resolve_path(repo_root, args.skill_atoms)

    inputs = list(load_inputs(repo_root, args.paths, args.examples_md))
    if not inputs:
        print("error: provide at least one IR JSON path or --examples-md", file=sys.stderr)
        return 2

    schema_validator = None
    if not args.skip_schema:
        schema_validator = load_schema_validator(schema_path)

    solution_model_ids = load_taxonomy_ids(solution_models_path, expected_kind="solution_models")
    skill_atom_ids = load_taxonomy_ids(skill_atoms_path, expected_kind="skill_atoms")

    errors: list[str] = []
    for label, instance in inputs:
        if schema_validator is not None:
            errors.extend(validate_schema(schema_validator, label, instance))
        errors.extend(validate_primary_paradigm(label, instance))
        errors.extend(validate_template_invariant(label, instance))
        errors.extend(
            validate_taxonomy_references(
                label,
                instance,
                solution_model_ids=solution_model_ids,
                skill_atom_ids=skill_atom_ids,
            )
        )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    if args.skip_schema:
        print("Schema validation skipped.")
    print(f"Validated {len(inputs)} IR document(s).")
    return 0


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_schema_validator(schema_path: Path) -> Any:
    try:
        import jsonschema
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "error: jsonschema is required for JSON Schema validation. "
            "Install it with `python -m pip install jsonschema`, or pass "
            "`--skip-schema` to run taxonomy reference validation only."
        ) from exc

    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def validate_schema(validator: Any, label: str, instance: JsonObject) -> list[str]:
    messages: list[str] = []
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    for error in errors:
        path = json_path(error.path)
        messages.append(f"{label}: schema error at {path}: {error.message}")
    return messages


def validate_primary_paradigm(label: str, instance: JsonObject) -> list[str]:
    solution = instance.get("solution")
    if not isinstance(solution, dict):
        return [f"{label}: paradigm error at $.solution: missing or invalid solution object"]

    primary = solution.get("primary_paradigm")
    if primary not in PRIMARY_PARADIGMS:
        allowed = ", ".join(sorted(PRIMARY_PARADIGMS))
        return [
            f"{label}: paradigm error at $.solution.primary_paradigm: "
            f"expected one of {{{allowed}}}, got {primary!r}"
        ]

    specific = solution.get("specific_paradigm")
    if not isinstance(specific, str) or not specific:
        return [
            f"{label}: paradigm error at $.solution.specific_paradigm: "
            "expected a non-empty string"
        ]
    return []


def validate_template_invariant(label: str, instance: JsonObject) -> list[str]:
    solution = instance.get("solution")
    if not isinstance(solution, dict):
        return [f"{label}: invariant error at $.solution: missing or invalid solution object"]

    algorithm_template = solution.get("algorithm_template")
    template_specific = solution.get("template_specific")
    if not isinstance(template_specific, dict):
        return [
            f"{label}: invariant error at $.solution.template_specific: "
            "missing or invalid template_specific object"
        ]

    template_type = template_specific.get("type")
    if algorithm_template != template_type:
        return [
            f"{label}: invariant error: $.solution.algorithm_template "
            f"{algorithm_template!r} must equal $.solution.template_specific.type {template_type!r}"
        ]
    return []


def load_taxonomy_ids(path: Path, *, expected_kind: str) -> set[str]:
    ids: list[str] = []
    for taxonomy_path, data in load_taxonomy_objects(path):
        kind = data.get("kind")
        if kind != expected_kind:
            raise SystemExit(
                f"error: {taxonomy_path} has kind {kind!r}; expected {expected_kind!r}"
            )

        items = data.get("items")
        if not isinstance(items, list):
            raise SystemExit(f"error: {taxonomy_path} must contain an items array")

        parent = data.get("parent")
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise SystemExit(
                    f"error: {taxonomy_path} item {index} must contain a string id"
                )
            if parent is not None and item.get("parent") != parent:
                raise SystemExit(
                    f"error: {taxonomy_path} item {index} has parent "
                    f"{item.get('parent')!r}; expected {parent!r}"
                )
            ids.append(item["id"])

    seen: set[str] = set()
    duplicates: set[str] = set()
    for taxonomy_id in ids:
        if taxonomy_id in seen:
            duplicates.add(taxonomy_id)
        seen.add(taxonomy_id)
    if duplicates:
        raise SystemExit(f"error: duplicate ids in {path}: {', '.join(sorted(duplicates))}")
    return set(ids)


def load_taxonomy_objects(path: Path) -> Iterator[tuple[Path, JsonObject]]:
    if path.is_dir():
        json_paths = sorted(path.rglob("*.json"))
        if not json_paths:
            raise SystemExit(f"error: taxonomy directory contains no JSON files: {path}")
        for json_path_file in json_paths:
            yield json_path_file, load_json(json_path_file)
        return

    yield path, load_json(path)


def validate_taxonomy_references(
    label: str,
    instance: JsonObject,
    *,
    solution_model_ids: set[str],
    skill_atom_ids: set[str],
) -> list[str]:
    solution = instance.get("solution")
    if not isinstance(solution, dict):
        return [f"{label}: taxonomy error at $.solution: missing or invalid solution object"]

    messages: list[str] = []
    messages.extend(
        validate_id_list(
            label,
            solution.get("solution_models"),
            path="$.solution.solution_models",
            allowed_ids=solution_model_ids,
        )
    )
    messages.extend(
        validate_id_list(
            label,
            solution.get("skill_atoms"),
            path="$.solution.skill_atoms",
            allowed_ids=skill_atom_ids,
        )
    )
    return messages


def validate_id_list(
    label: str,
    value: Any,
    *,
    path: str,
    allowed_ids: set[str],
) -> list[str]:
    if not isinstance(value, list):
        return [f"{label}: taxonomy error at {path}: expected an array"]

    messages: list[str] = []
    for index, item in enumerate(value):
        item_path = f"{path}[{index}].id"
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            messages.append(f"{label}: taxonomy error at {item_path}: expected a string id")
            continue
        taxonomy_id = item["id"]
        if taxonomy_id not in allowed_ids:
            messages.append(
                f"{label}: taxonomy error at {item_path}: unknown taxonomy id {taxonomy_id!r}"
            )
    return messages


def load_inputs(
    repo_root: Path,
    paths: Iterable[Path],
    examples_md: Path | None,
) -> Iterator[tuple[str, JsonObject]]:
    for path in paths:
        resolved = resolve_path(repo_root, path)
        if resolved.is_dir():
            for json_path_file in sorted(resolved.rglob("*.json")):
                yield str(json_path_file), load_json(json_path_file)
        else:
            yield str(resolved), load_json(resolved)

    if examples_md is not None:
        resolved_examples = resolve_path(repo_root, examples_md)
        text = resolved_examples.read_text(encoding="utf-8")
        for index, match in enumerate(re.finditer(r"```json\n(.*?)\n```", text, re.S), start=1):
            yield f"{resolved_examples}#json-block-{index}", json.loads(match.group(1))


def load_json(path: Path) -> JsonObject:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"error: file not found: {path}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"error: expected JSON object: {path}")
    return data


def json_path(parts: Iterable[Any]) -> str:
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}"
    return out


if __name__ == "__main__":
    raise SystemExit(main())
