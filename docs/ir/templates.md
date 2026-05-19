# Template-specific Schemas

## General Rule

`template_specific` should only contain fields that naturally belong to the
selected algorithm template. Do not add unrelated fields with `null`.

Do not use `greedy` as a fallback for miscellaneous implementation patterns.
Use `greedy` only when the solution depends on a locally justified choice,
invariant, or exchange argument.

For Editorial IR v1, `solution.algorithm_template` and
`solution.template_specific.type` must use the same id. For example:

```json
{
  "algorithm_template": "binary_search_on_answer",
  "template_specific": {
    "type": "binary_search_on_answer"
  }
}
```

Do not use a broad/refined pair such as `shortest_path` and
`dijkstra_with_state_expansion` in v1.

## Common Structured Templates

Some templates do not yet need a bespoke field set. Use this common shape for
them instead of forcing the solution into `greedy`.

```json
{
  "type": "<template id>",
  "main_structure": "<central state, object, or search space>",
  "key_operations": [
    "<important operation or check>",
    "<important update or aggregation>"
  ],
  "answer_extraction": "<how the answer is produced>"
}
```

Current common-structured template ids:

- `block_decomposition`
- `case_analysis`
- `combinatorial_counting`
- `counting_accumulation`
- `cyclic_rotation_scan`
- `data_structure_simulation`
- `direct_access`
- `interval_decomposition`
- `linear_scan`
- `lis_patience_sorting`
- `math_formula`
- `output_construction`
- `precomputation_table`
- `prefix_counting`
- `query_processing`
- `string_algorithm`
- `two_pointer`

## `binary_search_on_answer`

Use when the solution searches over the answer value and checks a monotone
feasibility predicate.

```json
{
  "type": "binary_search_on_answer",
  "objective": {
    "type": "maximize_feasible_value",
    "target": "<candidate answer variable>",
    "condition": "feasible(<candidate>)",
    "canonical_form": "maximize candidate such that feasible(candidate) is true"
  },
  "search_space": {
    "variable": "<candidate>",
    "meaning": "<meaning of the searched answer value>",
    "lower_bound": "<initial feasible or minimum candidate expression>",
    "upper_bound": "<initial infeasible or maximum candidate expression>"
  },
  "predicate": {
    "name": "feasible",
    "definition": "<feasibility condition>",
    "evaluation": "<how to evaluate feasibility>",
    "cost": "<cost per predicate evaluation>"
  },
  "monotonicity": {
    "direction": "true_to_smaller_values or true_to_larger_values",
    "statement": "<monotonicity statement justifying binary search>"
  }
}
```

## `exhaustive_enumeration`

Use when the intended solution enumerates every candidate in a bounded search
space and tests each candidate directly.

```json
{
  "type": "exhaustive_enumeration",
  "search_space": "<all candidates being enumerated>",
  "enumeration_order": "<loop order or mask/order generation>",
  "candidate_condition": "<condition checked for each candidate>",
  "aggregation": "<how candidate results are combined>",
  "pruning": "<pruning rule, or none when full enumeration is used>",
  "answer_extraction": "<how the final answer is produced>"
}
```

## `dynamic_programming`

Use when the solution defines states and transitions over subproblems.

```json
{
  "type": "dynamic_programming",
  "state_definition": "dp[i][j] = ...",
  "transition": "dp[i][j] = ...",
  "base_cases": ["..."],
  "iteration_order": "increasing i, increasing j",
  "answer_extraction": "dp[N][K]"
}
```

## `graph_traversal`

Use when the solution models the problem as graph reachability, traversal, or
state exploration.

```json
{
  "type": "graph_traversal",
  "graph_model": "implicit grid graph",
  "node_definition": "cell position and remaining resource",
  "edge_definition": "valid movement to adjacent cells",
  "traversal_order": "BFS by distance",
  "visited_state": "visited[row][col][resource]"
}
```

## `greedy`

Use when the solution repeatedly makes a locally justified choice.

```json
{
  "type": "greedy",
  "sorting_key": "increasing end time",
  "greedy_choice": "select the interval with earliest finishing time",
  "invariant": "chosen intervals leave maximum remaining space",
  "exchange_argument": "any optimal solution can replace its first interval with the earliest finishing interval"
}
```

## `segment_tree`

Use when the solution maintains interval aggregates with a segment tree,
including lazy or persistent variants.

```json
{
  "type": "segment_tree",
  "variant": "<standard, lazy, persistent, etc.>",
  "index_domain": "<array positions, compressed coordinates, versioned roots, etc.>",
  "stored_values": [
    "<aggregate stored at each node>"
  ],
  "update_operations": [
    "<point/range update operation>"
  ],
  "query_operations": [
    "<range query operation>"
  ],
  "propagation_or_versioning": "<lazy propagation, path copying, or none>",
  "answer_extraction": "<how query results are turned into the answer>"
}
```

## `stack_expression_parsing`

Use when the solution parses an expression with an operator stack, precedence
rules, and parentheses handling.

```json
{
  "type": "stack_expression_parsing",
  "operator_stack": "stores unresolved operators",
  "output_rule": "append operands immediately and pop operators by precedence",
  "parentheses_rule": "pop until matching opening parenthesis"
}
```

## Fenwick Tree Policy

Editorial IR v1 does not define `fenwick_tree` as an `algorithm_template`.
Represent Fenwick tree solutions with the closest broader template such as
`query_processing`, `prefix_counting`, or `data_structure_simulation`, and add
`data_structure.fenwick_tree` as a primary skill atom.

Example:

```json
{
  "algorithm_template": "query_processing",
  "skill_atoms": [
    {
      "id": "data_structure.fenwick_tree",
      "role": "primary",
      "weight": 1.0
    }
  ]
}
```

If Fenwick tree problems become common enough to need dedicated retrieval
structure, add `fenwick_tree` as a v1.1 template.

## Future Templates

Likely future templates:

- `fenwick_tree`
- `shortest_path`
- `flow`
- `matching`
- `number_theory`
- `combinatorics`
- `geometry`
