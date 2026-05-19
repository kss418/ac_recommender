# Taxonomies

This document defines normalized ids used by Editorial IR v1.

Machine-readable taxonomy data lives in:

- `../../taxonomies/solution-models.json`
- `../../taxonomies/skill-atoms.json`

Extractor and validator code should read the JSON files. This Markdown file is
for naming rules, review policy, and human-readable summaries.

## Reference Validation

JSON Schema validates the shape of taxonomy references. A second validation
step must verify that every referenced id exists in the taxonomy data:

```text
solution.solution_models[].id in taxonomies/solution-models.json
solution.skill_atoms[].id in taxonomies/skill-atoms.json
```

Use `../../scripts/validate_ir.py` for this check.

## ID Naming Convention

Use lowercase dot-separated ids for skill atoms.

Examples:

- `binary_search.answer`
- `graph.state_expansion`
- `dp.state_design`

Use lowercase snake_case ids for solution models.

Examples:

- `monotonic_feasibility_optimization`
- `state_space_shortest_path`
- `prefix_suffix_aggregation`

Prefer one canonical namespace. For example, use `graph.dijkstra`; do not also
add `graph.shortest_path.dijkstra` or `shortest_path.dijkstra` unless there is
a clear, distinct meaning.

## Adding New IDs

Add a new id only when no existing id captures the concept.

Before adding an id:

- Check whether an existing broader id is sufficient.
- Prefer extending the existing namespace over creating a synonym.
- Keep ids stable once they are used by generated IR.
- Add a short meaning to the table in this document.

## Weight Rules

Weights are relevance scores from `0.0` to `1.0`.

- `1.0`: central to the solution.
- `0.7` to `0.9`: important but not the only core idea.
- `0.3` to `0.6`: supporting technique.
- `0.1` to `0.2`: incidental or minor.

## Role Rules

Skill atom roles:

- `primary`: required to understand the main solution.
- `supporting`: useful or repeatedly used, but not the main idea.
- `incidental`: present in implementation but not useful for recommendation.

## Solution Models

Solution models are retrieval-oriented abstractions of solution structure. They
are not statement-side problem categories.

| ID | Meaning |
|---|---|
| `monotonic_feasibility_optimization` | Optimization problem reducible to monotone feasibility. |
| `maximize_minimum_under_budget` | Maximize a minimum value subject to a limited resource or budget. |
| `state_space_shortest_path` | Shortest path over expanded or implicit state graph. |
| `prefix_suffix_aggregation` | Combine prefix and suffix aggregates to answer or optimize. |
| `interval_decomposition` | Decompose the problem into intervals or interval events. |
| `local_greedy_selection` | Repeated local choice directly determines the solution. |
| `global_invariant_greedy` | Greedy solution justified by a maintained global invariant. |
| `counting_combinatorics` | Count valid objects using combinatorial structure. |
| `graph_connectivity_under_constraints` | Connectivity problem with constraints on edges, vertices, or states. |
| `range_query_update` | Maintain values under range queries and/or updates. |
| `subset_state_optimization` | Optimize over subset masks or subset states. |
| `tree_dp` | Dynamic programming over a tree structure. |
| `sequence_dp` | Dynamic programming over a sequence or prefix. |
| `grid_graph_traversal` | Traverse or search a grid as a graph. |
| `implicit_graph_search` | Search graph states generated on demand. |
| `meet_in_the_middle` | Split the search space and combine partial enumerations. |
| `two_pointer_window` | Maintain a moving window with two pointers. |
| `offline_query_processing` | Reorder or batch queries before answering. |
| `expression_parsing` | Parse or transform expressions using grammar, precedence, or stack structure. |

## Skill Atoms

| ID | Meaning |
|---|---|
| `binary_search.answer` | Binary search over an answer value. |
| `binary_search.monotone_predicate` | Design or use a monotone feasibility predicate. |
| `binary_search.lower_bound` | Use lower_bound-style binary search over sorted data. |
| `binary_search.real_number` | Binary search over continuous values. |
| `binary_search.parametric_search` | Parametric search framing with a decision procedure. |
| `array.linear_scan` | Linear scan over an array or sequence. |
| `array.prefix_sum` | Prefix sums or cumulative aggregates. |
| `array.suffix_aggregation` | Suffix aggregates or reverse cumulative values. |
| `math.sum_of_deficits` | Sum deficits from a target value or threshold. |
| `math.modular_arithmetic` | Modular arithmetic operations or identities. |
| `dp.state_design` | Define DP states that capture necessary information. |
| `dp.transition_optimization` | Optimize transition cost or transition enumeration. |
| `graph.bfs` | Breadth-first search. |
| `graph.dijkstra` | Dijkstra shortest path with non-negative edge weights. |
| `graph.state_expansion` | Expand graph nodes with extra state dimensions. |
| `greedy.sorting_key` | Sort by a key that enables greedy choices. |
| `greedy.exchange_argument` | Justify greedy choice by exchange argument. |
| `data_structure.segment_tree` | Segment tree for range queries or updates. |
| `data_structure.fenwick_tree` | Fenwick tree for prefix aggregates or point updates. |
| `data_structure.stack` | Stack used to manage nested, delayed, or last-in-first-out state. |
| `parsing.operator_precedence` | Handle operators according to precedence and parentheses rules. |
