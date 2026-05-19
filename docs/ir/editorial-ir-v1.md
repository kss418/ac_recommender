# Editorial IR v1

## Purpose

This IR normalizes competitive programming editorial content into a structured
solution model for retrieval and recommendation.

## File Layout

Recommended path:

```text
ir/<platform>/<event-id-or-problems>/<problem-id>.json
```

Examples:

```text
ir/atcoder/abc457/abc457_d.json
ir/baekjoon/problems/1918.json
ir/codeforces/1878/1878A.json
```

Use the platform event id when the problem belongs to a contest or event. Use
`problems` when `event` is `null`.

## Top-level Schema

```json
{
  "ir_version": "1.0",
  "platform": {},
  "event": null,
  "problem": {},
  "source": {},
  "solution": {
    "primary_paradigm": "...",
    "algorithm_template": "...",
    "problem_models": [],
    "skill_atoms": [],
    "solution_signature": {},
    "template_specific": {},
    "core_computation": {},
    "procedure": [],
    "complexity": {}
  }
}
```

## Top-level Fields

### `ir_version`

Schema version string used for migrations.

### `platform`

Judge or problem platform identity.

### `event`

Contest or event identity. Use `null` when the problem has no contest or event
context.

### `problem`

Problem identity, difficulty metadata, and canonical problem URL.

### `source`

Editorial source metadata.

### `solution`

Structured solution model used for retrieval and recommendation.
