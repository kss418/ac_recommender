# Template-specific Schemas

## General Rule

`template_specific` should only contain fields that naturally belong to the
selected algorithm template. Do not add unrelated fields with `null`.

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

## `binary_search_on_answer`

Use when the solution searches over the answer value and checks a monotone
feasibility predicate.

```json
{
  "type": "binary_search_on_answer",
  "objective": {
    "type": "maximize_feasible_value",
    "target": "x",
    "condition": "feasible(x)",
    "canonical_form": "maximize x such that feasible(x) is true"
  },
  "search_space": {
    "variable": "x",
    "meaning": "target minimum value",
    "lower_bound": "1",
    "upper_bound": "A_1 + K + 1"
  },
  "predicate": {
    "name": "feasible",
    "definition": "required_operations(x) <= K",
    "evaluation": "sum(ceil((x - a_i) / i) for i where a_i < x) <= K",
    "cost": "O(N)"
  },
  "monotonicity": {
    "direction": "true_to_smaller_values",
    "statement": "If feasible(x), then feasible(y) for every y <= x."
  }
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

## Future Templates

Likely future templates:

- `segment_tree`
- `fenwick_tree`
- `shortest_path`
- `flow`
- `matching`
- `number_theory`
- `combinatorics`
- `geometry`
- `string_algorithm`
