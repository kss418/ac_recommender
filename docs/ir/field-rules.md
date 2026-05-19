# Field Rules

## `ir_version`

Fixed string for migration control.

```json
{
  "ir_version": "1.0"
}
```

## `ir_language`

Language used by normalized IR text fields.

```json
{
  "ir_language": "en"
}
```

This can differ from `source.language`. For example, a Japanese editorial can
have `"source.language": "ja"` while the normalized IR remains English with
`"ir_language": "en"`.

## `platform`

Judge or problem platform identity.

```json
{
  "name": "ac"
}
```

- `name`: stable lowercase platform key, for example `ac`, `cf`, `boj`

## `event`

Contest or event identity. Use `null` when the problem has no contest or event
context, such as many Baekjoon problems.

```json
{
  "series": "ABC",
  "number": 457,
  "id": "abc457",
  "name": "AtCoder Beginner Contest 457"
}
```

- `series`: optional event series such as `ABC`, `ARC`, `AGC`, `Div2`
- `number`: optional event number
- `id`: platform-specific event id
- `name`: human-readable event name

For a problem without a contest:

```json
{
  "event": null
}
```

## `problem`

Problem identity.

```json
{
  "id": "abc457_d",
  "index": "D",
  "name": "Raise Minimum",
  "difficulty": {
    "rating": null,
    "source": null
  },
  "url": "https://atcoder.jp/contests/abc457/tasks/abc457_d"
}
```

- `id`: platform-specific problem id, for example `abc457_d`, `1918`, `1878A`
- `index`: contest-local problem index such as `A`, `B`, `C`, `D`; use `null` when absent
- `name`: official problem name
- `difficulty.rating`: numeric difficulty or rating when available, otherwise `null`
- `difficulty.source`: source of the difficulty value, for example `ac`, `cf`, `solved_ac`, otherwise `null`
- `url`: problem URL

## `source`

Solution source metadata.

```json
{
  "url": "https://atcoder.jp/contests/abc457/editorial/20138?editorialLang=en&lang=en",
  "kind": "official_solution",
  "language": "en",
  "author": "en_translator",
  "fetched_at": "2026-05-18T07:33:39.709020Z"
}
```

- `url`: source solution URL, repository URL, or `null` when the solution is generated without a concrete source URL
- `kind`: `official_solution`, `user_editorial`, `user_solution_code`, `generated`, or `unknown`
- `language`: source solution language, otherwise `null`
- `author`: solution source author when available, otherwise `null`
- `fetched_at`: UTC timestamp when the source was fetched, otherwise `null`

`generated` is reserved for AI-generated solutions. Do not use it for
user-authored repository code.

## `solution`

Structured solution model.

```json
{
  "primary_paradigm": "...",
  "specific_paradigm": "...",
  "algorithm_template": "...",
  "solution_models": [
    {
      "id": "...",
      "weight": 1.0
    }
  ],
  "skill_atoms": [
    {
      "id": "...",
      "role": "primary",
      "weight": 1.0
    }
  ],
  "solution_signature": {
    "main_object": "...",
    "main_condition": "...",
    "structural_property": "...",
    "update_or_transition": "...",
    "answer_extraction": "...",
    "complexity_bottleneck": "..."
  },
  "template_specific": {
    "type": "..."
  },
  "core_computations": [
    {
      "name": "...",
      "expression": "...",
      "role": "..."
    }
  ],
  "procedure": ["..."],
  "complexity": {}
}
```

- `primary_paradigm`: coarse family. Must be one of `implementation`, `brute_force`, `math`, `greedy`, `binary_search`, `dp`, `graph`, `data_structure`, `string`, or `constructive`
- `specific_paradigm`: more detailed human-readable paradigm, such as `persistent_segment_tree`, `two_pointer_data_structure`, or `recursive_dynamic_programming`
- `algorithm_template`: reusable pattern such as `binary_search_on_answer`
- `solution_models`: normalized retrieval-oriented solution model ids with weights, ordered from strongest to weakest
- `solution_models[].id`: taxonomy id such as `monotonic_feasibility_optimization`
- `solution_models[].weight`: relevance score from `0.0` to `1.0`
- `skill_atoms`: fine-grained reusable skills with roles and weights
- `skill_atoms[].id`: stable skill id such as `binary_search.answer`
- `skill_atoms[].role`: `primary`, `supporting`, or `incidental`
- `skill_atoms[].weight`: relevance score from `0.0` to `1.0`
- `solution_signature`: compact retrieval-oriented fingerprint of the solution
- `solution_signature.main_object`: central value, state, object, or structure manipulated by the solution
- `solution_signature.main_condition`: core constraint, transition condition, validity condition, or objective condition
- `solution_signature.structural_property`: key shape of the solution, such as monotone region, DAG state graph, shortest path, exchange argument
- `solution_signature.update_or_transition`: how the algorithm updates the object, state, candidate, or answer
- `solution_signature.answer_extraction`: how the final answer is selected or read out
- `solution_signature.complexity_bottleneck`: repeated operation that dominates time complexity
- `template_specific`: template-dependent structure; its fields depend on `template_specific.type`
- `core_computations`: main repeated computations inside the algorithm, ordered by importance
- `core_computations[].name`: stable short name for the computation
- `core_computations[].expression`: formula, recurrence, transition, or operation summary
- `core_computations[].role`: how the computation is used in the solution
- `procedure`: short normalized steps, not a prose explanation

In v1, `solution.algorithm_template` must be equal to
`solution.template_specific.type`. This invariant keeps extraction and
validation simple. Broader template names with refined `template_specific.type`
values are reserved for a later IR version.

## `complexity`

Asymptotic complexity with variable definitions and separated memory views.

```json
{
  "time": {
    "raw": "O(N log V)",
    "variables": {
      "N": "number of elements",
      "V": "answer search range"
    }
  },
  "space": {
    "auxiliary": "O(1)",
    "total": "O(N)"
  }
}
```

- `complexity.time.raw`: asymptotic time complexity expression
- `complexity.time.variables`: meaning of variables used in the raw expression
- `complexity.space.auxiliary`: additional memory beyond the input
- `complexity.space.total`: total memory including stored input

## Empty Values

Use `null` only when the field is truly unknown.

Prefer empty lists for missing repeated content:

```json
{
  "procedure": []
}
```

Prefer `null` for unknown scalar values:

```json
{
  "author": null
}
```
