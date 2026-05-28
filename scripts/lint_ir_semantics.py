#!/usr/bin/env python3
"""Warn about likely mismatches between Editorial IR text and skill atoms."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


JsonObject = dict[str, Any]
GENERIC_FALLBACK_SPECIFICS = {
    "string_pattern_processing",
    "direct_output_construction",
    "linear_scan_implementation",
    "graph_reachability_traversal",
    "candidate_enumeration",
    "combinatorial_formula_counting",
    "state_transition_dynamic_programming",
    "case_analysis_implementation",
    "binary_search_on_answer",
    "sorted_greedy_selection",
    "connectivity_with_disjoint_set",
}


@dataclass(frozen=True)
class WarningMessage:
    label: str
    rule: str
    message: str

    def format(self) -> str:
        return f"{self.label}: semantic warning [{self.rule}]: {self.message}"


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint Editorial IR files for semantic skill-atom consistency."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("ir")],
        help="IR JSON files or directories containing IR JSON files. Defaults to ir/.",
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
        help="Also lint IR JSON code blocks from an examples Markdown file.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with status 1 when any semantic warning is emitted.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]

    skill_atom_ids = load_skill_atom_ids(resolve_path(repo_root, args.skill_atoms))
    inputs = list(load_inputs(repo_root, args.paths, args.examples_md))
    if not inputs:
        print("error: no IR JSON documents found", file=sys.stderr)
        return 2

    warnings: list[WarningMessage] = []
    for label, instance in inputs:
        warnings.extend(lint_instance(label, instance, skill_atom_ids=skill_atom_ids))

    for warning in warnings:
        print(warning.format())

    print(f"Semantic lint checked {len(inputs)} IR document(s).")
    if warnings:
        print(f"Emitted {len(warnings)} warning(s).")
        return 1 if args.fail_on_warning else 0
    print("No semantic warnings.")
    return 0


def lint_instance(
    label: str,
    instance: JsonObject,
    *,
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    solution = instance.get("solution")
    if not isinstance(solution, dict):
        return [
            WarningMessage(
                label,
                "invalid-solution",
                "missing or invalid $.solution object; run validate_ir.py first",
            )
        ]

    text = semantic_text(instance)
    lower_text = text.lower()
    specific = str(solution.get("specific_paradigm", "")).lower()
    algorithm_template = solution.get("algorithm_template")
    skills = weighted_ids(solution.get("skill_atoms"))
    models = weighted_ids(solution.get("solution_models"))

    warnings: list[WarningMessage] = []
    warnings.extend(lint_generic_fallback(label, specific))
    warnings.extend(lint_binomial(label, lower_text, skills, skill_atom_ids))
    warnings.extend(lint_meet_in_the_middle(label, specific, models, skills, skill_atom_ids))
    warnings.extend(lint_backtracking(label, specific, skills, skill_atom_ids))
    warnings.extend(lint_lis_template(label, algorithm_template, skills, skill_atom_ids))
    warnings.extend(lint_dp_specific(label, solution, specific, models, skills, skill_atom_ids))
    warnings.extend(lint_probability(label, lower_text, specific, skills, skill_atom_ids))
    warnings.extend(lint_string_algorithms(label, lower_text, skills, skill_atom_ids))
    warnings.extend(lint_rolling_hash_evidence(label, lower_text, skills))
    warnings.extend(lint_minimum_spanning_tree_evidence(label, specific, skills))
    return warnings


def lint_generic_fallback(label: str, specific: str) -> list[WarningMessage]:
    if specific not in GENERIC_FALLBACK_SPECIFICS:
        return []
    return [
        WarningMessage(
            label,
            "generic-fallback-specific",
            f"specific_paradigm is generic fallback value {specific!r}; replace it with a problem-specific algorithm description",
        )
    ]


def lint_binomial(
    label: str,
    lower_text: str,
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    atom = "math.binomial_coefficient"
    if atom not in skill_atom_ids or atom in skills:
        return []

    patterns = [
        r"\bc[ \t]*\([^)]*,[ \t]*\d",
        r"\bbinomial coefficient\b",
        r"\bbinom\b|\bbinom[ \t]*\(",
        r"\bncr\b",
        r"\bfactorial precomputation\b",
        r"\bprecomput(?:e|ed|ing)? factorial",
    ]
    if any(re.search(pattern, lower_text) for pattern in patterns):
        return [
            WarningMessage(
                label,
                "binomial-coefficient",
                f"text mentions combinations/binomials but skill_atoms lacks {atom}",
            )
        ]
    return []


def lint_meet_in_the_middle(
    label: str,
    specific: str,
    models: set[str],
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    atom = "brute_force.meet_in_the_middle"
    if atom not in skill_atom_ids or atom in skills:
        return []

    if has_meet_in_the_middle_token(specific) or "meet_in_the_middle" in models:
        return [
            WarningMessage(
                label,
                "meet-in-the-middle",
                f"solution model/paradigm mentions meet-in-the-middle but skill_atoms lacks {atom}",
            )
        ]
    return []


def has_meet_in_the_middle_token(specific: str) -> bool:
    return bool(re.search(r"(?<![a-z0-9])meet_in_the_middle(?![a-z0-9])", specific))


def lint_backtracking(
    label: str,
    specific: str,
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    allowed = {"brute_force.backtracking", "graph.dfs"} & skill_atom_ids
    if "backtracking" not in specific or skills & allowed:
        return []

    expected = " or ".join(sorted(allowed)) if allowed else "a backtracking/DFS atom"
    return [
        WarningMessage(
            label,
            "backtracking",
            f"specific_paradigm mentions backtracking but skill_atoms lacks {expected}",
        )
    ]


def lint_lis_template(
    label: str,
    algorithm_template: Any,
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    atom = "dp.lis"
    if atom not in skill_atom_ids or atom in skills:
        return []
    if algorithm_template == "lis_patience_sorting":
        return [
            WarningMessage(
                label,
                "lis-template",
                f"algorithm_template is lis_patience_sorting but skill_atoms lacks {atom}",
            )
        ]
    return []


def lint_dp_specific(
    label: str,
    solution: JsonObject,
    specific: str,
    models: set[str],
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    checks: list[tuple[str, str, bool]] = [
        ("digit-dp", "dp.digit", "digit_dp" in specific),
        ("knapsack-dp", "dp.knapsack", "knapsack" in specific and has_dp_context(solution, specific, models)),
        ("tree-dp", "dp.tree", has_tree_dp_specific(specific)),
        ("interval-dp", "dp.interval", "interval_dp" in specific),
        ("bitmask-dp", "dp.bitmask", "bitmask" in specific and has_dp_context(solution, specific, models)),
    ]

    warnings: list[WarningMessage] = []
    for rule, atom, triggered in checks:
        if not triggered or atom not in skill_atom_ids or atom in skills:
            continue
        warnings.append(
            WarningMessage(
                label,
                rule,
                f"specific_paradigm suggests {atom.removeprefix('dp.')} DP but skill_atoms lacks {atom}",
            )
        )
    return warnings


def has_dp_context(solution: JsonObject, specific: str, models: set[str]) -> bool:
    algorithm_template = str(solution.get("algorithm_template", "")).lower()
    primary = str(solution.get("primary_paradigm", "")).lower()
    return (
        primary == "dp"
        or "_dp" in specific
        or algorithm_template.endswith("_dp")
        or any("dp" in model for model in models)
    )


def has_tree_dp_specific(specific: str) -> bool:
    return re.search(r"(?<!segment_)tree_dp", specific) is not None


def lint_probability(
    label: str,
    lower_text: str,
    specific: str,
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    expected_atom = "probability.expected_value"
    probability_atoms = {
        "probability.expected_value",
        "probability.probability_dp",
        "probability.probability_formula",
        "probability.generating_function",
    } & skill_atom_ids

    has_expected_text = has_probability_expectation_text(lower_text)
    if has_expected_text and expected_atom in skill_atom_ids and expected_atom not in skills:
        return [
            WarningMessage(
                label,
                "probability-skill",
                f"text mentions expectation but skill_atoms lacks {expected_atom}",
            )
        ]

    if not probability_atoms or skills & probability_atoms:
        return []

    if is_randomized_algorithm_context(specific, lower_text, skills):
        return []
    if is_non_probability_algorithm_context(specific, lower_text, skills):
        return []

    if has_probability_text(lower_text):
        expected = " or ".join(sorted(probability_atoms))
        return [
            WarningMessage(
                label,
                "probability-skill",
                f"text mentions probability but skill_atoms lacks {expected}",
            )
        ]
    return []


def has_probability_expectation_text(lower_text: str) -> bool:
    return bool(
        re.search(
            r"\bexpected[-_ ]value\b|"
            r"\bexpected (?:cost|score|time|number|count|total|sum|throws|steps|turns|moves|area|rank)\b|"
            r"\bexpectation[-_ ](?:dp|formula|recurrence|system|sum)\b",
            lower_text,
        )
    )


def has_probability_text(lower_text: str) -> bool:
    return bool(re.search(r"\bprobability\b|\bprobabilit(?:y|ies|istically)\b", lower_text))


def is_randomized_algorithm_context(specific: str, lower_text: str, skills: set[str]) -> bool:
    randomized_text = re.search(
        r"\brandomized\b|"
        r"\brandom moduli\b|"
        r"\brandom large integers\b|"
        r"\bfalse equality\b|"
        r"\bwith high probability\b",
        lower_text,
    )
    if not specific.startswith("randomized_") and not randomized_text:
        return False
    if has_probability_expectation_text(lower_text):
        return False
    evidence_atoms = {
        "hashing.zobrist_hash",
        "hashing.rolling_hash",
        "hashing.modular_fingerprint",
        "math.modular_arithmetic",
    } & skills
    evidence_text = re.search(
        r"\bhash(?:ing|es)?\b|"
        r"\bzobrist\b|"
        r"\bmajority\b|"
        r"\bsampling\b|"
        r"\bfingerprint(?:s|ing)?\b|"
        r"\bmoduli\b",
        lower_text,
    )
    return bool(evidence_atoms or evidence_text)


def is_non_probability_algorithm_context(specific: str, lower_text: str, skills: set[str]) -> bool:
    if "probability mass" in lower_text and {"dp.alien", "dp.monge_optimization"} & skills:
        return True
    if "probability weight" in lower_text and "ratio_greedy" in specific:
        return True
    if "mixed strategy probability" in lower_text and "zero_sum_game" in specific:
        return True
    return False


def lint_string_algorithms(
    label: str,
    lower_text: str,
    skills: set[str],
    skill_atom_ids: set[str],
) -> list[WarningMessage]:
    rules = [
        ("suffix-array", "string.suffix_array", r"\bsuffix array\b|\bsuffix_array\b"),
        ("lcp-array", "string.lcp_array", r"\blcp array\b|\blcp_array\b"),
        ("z-algorithm", "string.z_algorithm", r"\bz[-_ ]?algorithm\b|\bz_algorithm\b"),
        ("aho-corasick", "string.aho_corasick", r"\baho[-_ ]corasick\b|\baho_corasick\b"),
        ("rolling-hash", "hashing.rolling_hash", r"\brolling hash\b|\brolling_hash\b"),
    ]

    warnings: list[WarningMessage] = []
    for rule, atom, pattern in rules:
        if atom not in skill_atom_ids or atom in skills:
            continue
        if re.search(pattern, lower_text):
            warnings.append(
                WarningMessage(
                    label,
                    rule,
                    f"text mentions {rule.replace('-', ' ')} but skill_atoms lacks {atom}",
                )
            )
    return warnings


def lint_rolling_hash_evidence(
    label: str,
    lower_text: str,
    skills: set[str],
) -> list[WarningMessage]:
    atom = "hashing.rolling_hash"
    if atom not in skills:
        return []

    evidence = (
        r"\brolling[_ -]?hash\b|"
        r"\bprefix[_ -]?hash(?:es)?\b|"
        r"\bsubstring[_ -]?hash(?:es)?\b|"
        r"\bsequence[_ -]?hash(?:es)?\b|"
        r"\bhash(?:ing|es|ed)?\b|"
        r"\bfingerprint(?:s|ing)?\b"
    )
    if re.search(evidence, lower_text):
        return []

    return [
        WarningMessage(
            label,
            "rolling-hash-evidence",
            f"skill_atoms contains {atom} but IR text does not mention a hashing-based method",
        )
    ]


def lint_minimum_spanning_tree_evidence(
    label: str,
    specific: str,
    skills: set[str],
) -> list[WarningMessage]:
    atom = "graph.minimum_spanning_tree"
    if atom not in skills:
        return []

    evidence = r"(?<![a-z0-9])mst(?![a-z0-9])|kruskal|spanning|minimum_spanning"
    if re.search(evidence, specific):
        return []

    return [
        WarningMessage(
            label,
            "minimum-spanning-tree-evidence",
            f"skill_atoms contains {atom} but specific_paradigm does not mention mst, kruskal, or spanning-tree structure",
        )
    ]


def semantic_text(instance: JsonObject) -> str:
    parts: list[str] = []
    collect_semantic_text(instance, parts, path=())
    return "\n".join(parts)


def collect_semantic_text(value: Any, parts: list[str], *, path: tuple[str, ...]) -> None:
    if isinstance(value, str):
        parts.append(value)
        return
    if isinstance(value, list):
        for item in value:
            collect_semantic_text(item, parts, path=path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if path == ("solution",) and key == "skill_atoms":
                continue
            collect_semantic_text(item, parts, path=path + (str(key),))


def weighted_ids(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item["id"] for item in value if isinstance(item, dict) and isinstance(item.get("id"), str)}


def load_skill_atom_ids(path: Path) -> set[str]:
    ids: list[str] = []
    for taxonomy_path, data in load_taxonomy_objects(path):
        if data.get("kind") != "skill_atoms":
            raise SystemExit(f"error: {taxonomy_path} is not a skill_atoms taxonomy")
        items = data.get("items")
        if not isinstance(items, list):
            raise SystemExit(f"error: {taxonomy_path} must contain an items array")
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise SystemExit(f"error: {taxonomy_path} item {index} must contain a string id")
            ids.append(item["id"])
    return set(ids)


def load_taxonomy_objects(path: Path) -> Iterator[tuple[Path, JsonObject]]:
    if path.is_dir():
        json_paths = sorted(path.rglob("*.json"))
        if not json_paths:
            raise SystemExit(f"error: taxonomy directory contains no JSON files: {path}")
        for json_path in json_paths:
            yield json_path, load_json(json_path)
        return
    yield path, load_json(path)


def load_inputs(
    repo_root: Path,
    paths: Iterable[Path],
    examples_md: Path | None,
) -> Iterator[tuple[str, JsonObject]]:
    for path in paths:
        resolved = resolve_path(repo_root, path)
        if resolved.is_dir():
            for json_path in sorted(resolved.rglob("*.json")):
                yield str(json_path), load_json(json_path)
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


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


if __name__ == "__main__":
    raise SystemExit(main())
