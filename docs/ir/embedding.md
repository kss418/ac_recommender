# Embedding Generation

This document defines how to generate embedding documents from Editorial IR.
The IR is the source of truth; embeddings are derived text views.

## Embedding Views

Each problem may produce multiple embedding documents:

- `problem_semantic`
- `solution_structure`
- `skill`
- `combined`

## Metadata-only Fields

Use these fields for filtering, joins, display, or reranking. Do not include
them directly in embedding text unless a view explicitly says so.

- `ir_version`
- `platform`
- `event`
- `problem.id`
- `problem.url`
- `source.url`
- `source.kind`
- `source.author`

Use `problem.difficulty` for filtering or reranking, not for embedding.

## `problem_semantic`

Purpose: capture the problem identity at a light semantic level.

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
Platform: atcoder
Event: abc457
Problem: D - Raise Minimum
```

## `solution_structure`

Purpose: retrieve problems with similar solution structure.

Use:

- `solution.primary_paradigm`
- `solution.algorithm_template`
- `solution.problem_models`
- `solution.solution_signature`
- `solution.template_specific`
- `solution.core_computation`
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
Algorithm template: binary_search_on_answer
Problem models: monotonic_feasibility_optimization, maximize_minimum_under_budget
Main object: target minimum value x
Main condition: required_increments(x) <= K
Structural property: monotone feasible region
Update or transition: move the lower bound upward when x is feasible
Answer extraction: maximum feasible x
Template-specific: search over answer x with monotone feasible predicate
Core computation: required_increments = sum(max(0, x - a_i))
Complexity: O(N log V), where V is answer search range
```

## `skill`

Purpose: retrieve problems that exercise similar fine-grained skills.

Use:

- `solution.skill_atoms`
- `solution.primary_paradigm`
- `solution.algorithm_template`

Sort skill atoms by role and descending weight.

Suggested text:

```text
Primary skills: binary_search.answer, binary_search.monotone_predicate
Supporting skills: array.linear_scan, math.sum_of_deficits
Paradigm: binary_search
Template: binary_search_on_answer
```

## `combined`

Purpose: broad retrieval when only one embedding view is available.

Use a compact combination of:

- `problem.name`
- `solution.primary_paradigm`
- `solution.algorithm_template`
- `solution.problem_models`
- `solution.skill_atoms`
- `solution.solution_signature`
- `solution.core_computation`

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
Template: binary_search_on_answer
Models: monotonic_feasibility_optimization, maximize_minimum_under_budget
Skills: binary_search.answer, binary_search.monotone_predicate, array.linear_scan, math.sum_of_deficits
Signature: target minimum value x; required_increments(x) <= K; monotone feasible region; maximize feasible x
Core computation: sum(max(0, x - a_i))
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
