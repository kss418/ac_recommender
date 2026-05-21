# Embedding Generation

This document defines how to generate embedding documents from Editorial IR.
The IR is the source of truth; embeddings are derived text views.

## Embedding Views

Each problem may produce multiple embedding documents:

- `problem_identity`
- `solution_structure`
- `skill`
- `combined`

By default, embedding generation should produce only recommendation views:

- `solution_structure`
- `skill`
- `combined`

Do not include `problem_identity` in default embedding outputs.

Recommendation retrieval must apply a metadata view filter:

- compare `solution_structure` only with `solution_structure`,
- compare `skill` only with `skill`,
- compare `combined` only with `combined`.

Even if all views share one vector index, recommendation search must filter on
`metadata.view`. Do not mix views when computing recommendation scores.

Use only these views for recommendation scoring:

- `solution_structure`
- `skill`
- `combined`

`problem_identity` is for debugging, joins, display, and problem-name lookup.
Generate it only for a separate debug/name-search index when explicitly
requested, for example with `--views problem_identity`. Exclude it from
recommendation scores.

## Metadata-only Fields

Use these fields for filtering, joins, display, or reranking. Do not include
them directly in embedding text unless a view explicitly says so.

- `ir_version`
- `ir_language`
- `platform`
- `event`
- `problem.id`
- `problem.url`
- `source.url`
- `source.kind`
- `source.author`
- `source.fetched_at`

Use `problem.difficulty` for filtering or reranking, not for embedding.

## `problem_identity`

Purpose: capture the source problem identity for lookup and weak lexical
matching. This is not a true semantic view of the problem statement.

Use:

- `platform.name`
- `event.id`
- `problem.index`
- `problem.name`

Do not include:

- source URL
- author
- difficulty rating

Suggested text:

```text
Platform: ac
Event: abc457
Problem: D - Raise Minimum
```

## Future `problem_semantic`

Do not generate a `problem_semantic` view from identity fields alone. A true
problem semantic view requires a structured statement-side signature such as:

```json
{
  "problem_signature": {
    "domain": "array",
    "objects": ["array", "increment_budget", "target_minimum"],
    "objective": "maximize the minimum value after at most K increments",
    "operations": ["increment array elements"],
    "constraint_signal": "answer search is needed over a large value range"
  }
}
```

If `problem_signature` is added in a later IR version, `problem_semantic`
should be generated from that object rather than from platform, event, or
problem id metadata.

## `solution_structure`

Purpose: retrieve problems with similar solution structure.

Use:

- `solution.primary_paradigm`
- `solution.specific_paradigm`
- `solution.algorithm_template`
- `solution.solution_models`
- `solution.solution_signature`
- `solution.template_specific`
- `solution.core_computations`
- `solution.complexity.time.raw`
- `solution.complexity.time.variables`

Do not include:

- raw editorial prose
- source URL
- author
- event name
- difficulty rating

Suggested text:

```text
Primary paradigm: binary_search
Specific paradigm: binary_search_on_answer
Algorithm template: binary_search_on_answer
Solution models: monotonic_feasibility_optimization, maximize_minimum_under_budget
Main object: target minimum value x
Main condition: required_operations(x) <= K
Structural property: monotone feasible region
Update or transition: move the lower bound upward when x is feasible
Answer extraction: maximum feasible x
Template-specific: search over answer x with monotone feasible predicate
Core computations: required_operations = sum(ceil((x - a_i) / i) for i where a_i < x)
Complexity: O(N log(A_1 + K)), where A_1 + K is the binary search range upper scale
```

## `skill`

Purpose: retrieve problems that exercise similar fine-grained skills.

Use:

- `solution.skill_atoms`
- `solution.primary_paradigm`
- `solution.specific_paradigm`
- `solution.algorithm_template`

Sort skill atoms by role and descending weight.

Suggested text:

```text
Primary skills: binary_search.answer, binary_search.monotone_predicate
Supporting skills: array.linear_scan, math.ceil_division, implementation.overflow_guard
Paradigm: binary_search
Specific paradigm: binary_search_on_answer
Template: binary_search_on_answer
```

## `combined`

Purpose: broad retrieval when only one embedding view is available.

Use a compact combination of:

- `problem.name`
- `solution.primary_paradigm`
- `solution.specific_paradigm`
- `solution.algorithm_template`
- `solution.solution_models`
- `solution.skill_atoms`
- `solution.solution_signature`
- `solution.core_computations`

Do not include:

- raw editorial prose
- boilerplate input/output steps
- source URL
- author
- difficulty rating

Suggested text:

```text
Problem: Raise Minimum
Paradigm: binary_search
Specific paradigm: binary_search_on_answer
Template: binary_search_on_answer
Solution models: monotonic_feasibility_optimization, maximize_minimum_under_budget
Skills: binary_search.answer, binary_search.monotone_predicate, array.linear_scan, math.ceil_division, implementation.overflow_guard
Signature: target minimum value x; required_operations(x) <= K; monotone feasible region; maximize feasible x
Core computations: sum(ceil((x - a_i) / i) for i where a_i < x)
```

## Difficulty

Do not embed difficulty directly.

Use difficulty for:

- candidate filtering
- reranking
- curriculum ordering
- avoiding recommendations that are too easy or too hard

Example reranking signal:

```text
Prefer candidates within +/- 300 rating of the user's current solved range.
```

## Normalization Rules

- Use taxonomy ids instead of prose when possible.
- Keep generated text deterministic.
- Omit fields that are unknown.
- Do not include fields with `null` values.
- Do not include navigation text, author boilerplate, or raw editorial prose.
- Prefer compact lines over paragraphs.
