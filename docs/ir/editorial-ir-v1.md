# Editorial IR v1

## Purpose

This IR normalizes competitive programming editorial content into a structured
solution model for retrieval and recommendation.

## File Layout

Recommended path:

```text
ir/v1/<platform>/<event-series-or-problems>/<event-number-or-id>/<problem-file>.json
```

Examples:

```text
ir/v1/ac/abc/457/D-raise-minimum.json
ir/v1/boj/problems/1918.json
ir/v1/cf/1878/1878A.json
```

For AtCoder, mirror the editorial path after the platform directory: lowercase
series, contest number, and the same problem filename stem. Use `problems` when
`event` is `null`.

## AtCoder Path Convention

For AtCoder data, use this fixed layout:

```text
editorials/ac/<series>/<contest-number>/<problem-file>.md
ir/v1/ac/<series>/<contest-number>/<problem-file>.json
```

Rules:

- `ac` is the platform key for AtCoder.
- `<series>` is lowercase: `abc`, `arc`, or `agc`.
- `<contest-number>` is the numeric contest id only, such as `450` or `457`.
- `<problem-file>` is the same filename stem in both `editorials` and `ir`.

Example:

```text
editorials/ac/abc/457/D-raise-minimum.md
ir/v1/ac/abc/457/D-raise-minimum.json
```

Do not use the older pilot paths `editorials/ABC/...`, `ir/v1/ABC/...`, or
`ir/ac/abc457/...` for AtCoder data.

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
    "solution_models": [],
    "skill_atoms": [],
    "solution_signature": {},
    "template_specific": {},
    "core_computations": [],
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
