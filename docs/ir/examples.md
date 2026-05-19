# Examples

Some examples in this document are synthetic and are intended to demonstrate
schema shape rather than represent real problems.

## AtCoder ABC457 D - Raise Minimum

Binary search on answer.

```json
{
  "ir_version": "1.0",
  "platform": {
    "name": "ac"
  },
  "event": {
    "series": "ABC",
    "number": 457,
    "id": "abc457",
    "name": "AtCoder Beginner Contest 457"
  },
  "problem": {
    "id": "abc457_d",
    "index": "D",
    "name": "Raise Minimum",
    "difficulty": {
      "rating": null,
      "source": null
    },
    "url": "https://atcoder.jp/contests/abc457/tasks/abc457_d"
  },
  "source": {
    "url": "https://atcoder.jp/contests/abc457/editorial/20138?editorialLang=en&lang=en",
    "kind": "official_solution",
    "language": "en",
    "author": "en_translator"
  },
  "solution": {
    "primary_paradigm": "binary_search",
    "algorithm_template": "binary_search_on_answer",
    "solution_models": [
      {
        "id": "monotonic_feasibility_optimization",
        "weight": 1.0
      },
      {
        "id": "maximize_minimum_under_budget",
        "weight": 0.8
      }
    ],
    "skill_atoms": [
      {
        "id": "binary_search.answer",
        "role": "primary",
        "weight": 1.0
      },
      {
        "id": "binary_search.monotone_predicate",
        "role": "primary",
        "weight": 0.9
      },
      {
        "id": "array.linear_scan",
        "role": "supporting",
        "weight": 0.4
      },
      {
        "id": "math.ceil_division",
        "role": "supporting",
        "weight": 0.5
      },
      {
        "id": "implementation.overflow_guard",
        "role": "supporting",
        "weight": 0.3
      }
    ],
    "solution_signature": {
      "main_object": "target minimum value x",
      "main_condition": "required_operations(x) <= K",
      "structural_property": "monotone feasible region",
      "update_or_transition": "move the lower bound upward when x is feasible",
      "answer_extraction": "maximum feasible x",
      "complexity_bottleneck": "O(N) feasibility check using integer ceiling division"
    },
    "template_specific": {
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
    },
    "core_computations": [
      {
        "name": "required_operations",
        "expression": "sum(ceil((x - a_i) / i) for i where a_i < x)",
        "role": "feasibility check"
      },
      {
        "name": "integer_ceil_division",
        "expression": "(x - a_i + i - 1) // i",
        "role": "compute required operations for one element"
      }
    ],
    "procedure": [
      "Binary search x over the answer space.",
      "For each candidate x, compute the total operations needed to make every element at least x.",
      "Use integer ceiling division for elements below x.",
      "Return the maximum feasible x."
    ],
    "complexity": {
      "time": {
        "raw": "O(N log(A_1 + K))",
        "variables": {
          "N": "number of elements",
          "A_1 + K": "binary search range upper scale"
        }
      },
      "space": {
        "auxiliary": "O(1)",
        "total": "O(N)"
      }
    }
  }
}
```

## Synthetic Dynamic Programming

```json
{
  "ir_version": "1.0",
  "platform": {
    "name": "ac"
  },
  "event": {
    "series": "ABC",
    "number": 999,
    "id": "abc999",
    "name": "AtCoder Beginner Contest 999"
  },
  "problem": {
    "id": "abc999_e",
    "index": "E",
    "name": "Select K Items",
    "difficulty": {
      "rating": null,
      "source": null
    },
    "url": "https://atcoder.jp/contests/abc999/tasks/abc999_e"
  },
  "source": {
    "url": "https://atcoder.jp/contests/abc999/editorial/99999?editorialLang=en&lang=en",
    "kind": "official_solution",
    "language": "en",
    "author": "example_author"
  },
  "solution": {
    "primary_paradigm": "dp",
    "algorithm_template": "dynamic_programming",
    "solution_models": [
      {
        "id": "sequence_dp",
        "weight": 1.0
      }
    ],
    "skill_atoms": [
      {
        "id": "dp.state_design",
        "role": "primary",
        "weight": 1.0
      },
      {
        "id": "dp.transition_optimization",
        "role": "supporting",
        "weight": 0.6
      }
    ],
    "solution_signature": {
      "main_object": "dp state over prefix length and selected count",
      "main_condition": "optimal substructure over previous states",
      "structural_property": "transition depends only on smaller prefix",
      "update_or_transition": "take max over previous compatible states",
      "answer_extraction": "final DP state",
      "complexity_bottleneck": "number of states times transition cost"
    },
    "template_specific": {
      "type": "dynamic_programming",
      "state_definition": "dp[i][j] = maximum value using first i items and selecting j items",
      "transition": "dp[i + 1][j] = max(dp[i + 1][j], dp[i][j]); dp[i + 1][j + 1] = max(dp[i + 1][j + 1], dp[i][j] + value[i])",
      "base_cases": [
        "dp[0][0] = 0"
      ],
      "iteration_order": "increasing i, increasing j",
      "answer_extraction": "dp[N][K]"
    },
    "core_computations": [
      {
        "name": "dp_transition",
        "expression": "max(skip current item, take current item)",
        "role": "state update"
      }
    ],
    "procedure": [
      "Define prefix-count DP states.",
      "Iterate states in increasing prefix order.",
      "Apply skip and take transitions.",
      "Read the answer from dp[N][K]."
    ],
    "complexity": {
      "time": {
        "raw": "O(NK)",
        "variables": {
          "N": "number of items",
          "K": "number of selected items"
        }
      },
      "space": {
        "auxiliary": "O(NK)",
        "total": "O(NK)"
      }
    }
  }
}
```

## Synthetic Graph Traversal

```json
{
  "ir_version": "1.0",
  "platform": {
    "name": "ac"
  },
  "event": {
    "series": "ABC",
    "number": 999,
    "id": "abc999",
    "name": "AtCoder Beginner Contest 999"
  },
  "problem": {
    "id": "abc999_f",
    "index": "F",
    "name": "Grid State Search",
    "difficulty": {
      "rating": null,
      "source": null
    },
    "url": "https://atcoder.jp/contests/abc999/tasks/abc999_f"
  },
  "source": {
    "url": "https://atcoder.jp/contests/abc999/editorial/99998?editorialLang=en&lang=en",
    "kind": "official_solution",
    "language": "en",
    "author": "example_author"
  },
  "solution": {
    "primary_paradigm": "graph",
    "algorithm_template": "graph_traversal",
    "solution_models": [
      {
        "id": "grid_graph_traversal",
        "weight": 1.0
      },
      {
        "id": "implicit_graph_search",
        "weight": 0.8
      }
    ],
    "skill_atoms": [
      {
        "id": "graph.bfs",
        "role": "primary",
        "weight": 1.0
      },
      {
        "id": "graph.state_expansion",
        "role": "primary",
        "weight": 0.9
      }
    ],
    "solution_signature": {
      "main_object": "shortest distance to each expanded grid state",
      "main_condition": "valid moves preserve remaining resource",
      "structural_property": "state-expanded graph preserves feasible paths",
      "update_or_transition": "push unvisited neighboring states into BFS queue",
      "answer_extraction": "minimum distance among target states",
      "complexity_bottleneck": "state transitions over grid cells and resource values"
    },
    "template_specific": {
      "type": "graph_traversal",
      "graph_model": "implicit grid graph with resource-expanded states",
      "node_definition": "cell position and remaining resource",
      "edge_definition": "valid movement to adjacent cells",
      "traversal_order": "BFS by distance",
      "visited_state": "visited[row][col][resource]"
    },
    "core_computations": [
      {
        "name": "neighbor_generation",
        "expression": "valid adjacent cells with updated resource",
        "role": "graph transition"
      }
    ],
    "procedure": [
      "Treat each cell-resource pair as a graph state.",
      "Run BFS from the initial state.",
      "Generate valid adjacent states.",
      "Take the minimum distance to a target state."
    ],
    "complexity": {
      "time": {
        "raw": "O(HWR)",
        "variables": {
          "H": "grid height",
          "W": "grid width",
          "R": "number of resource states"
        }
      },
      "space": {
        "auxiliary": "O(HWR)",
        "total": "O(HWR)"
      }
    }
  }
}
```

## Synthetic Greedy

```json
{
  "ir_version": "1.0",
  "platform": {
    "name": "cf"
  },
  "event": {
    "series": "Div2",
    "number": 1878,
    "id": "1878",
    "name": "Codeforces Round 1878"
  },
  "problem": {
    "id": "1878A",
    "index": "A",
    "name": "Interval Selection",
    "difficulty": {
      "rating": 900,
      "source": "cf"
    },
    "url": "https://codeforces.com/problemset/problem/1878/A"
  },
  "source": {
    "url": "https://codeforces.com/blog/entry/example",
    "kind": "official_solution",
    "language": "en",
    "author": null
  },
  "solution": {
    "primary_paradigm": "greedy",
    "algorithm_template": "greedy",
    "solution_models": [
      {
        "id": "local_greedy_selection",
        "weight": 1.0
      },
      {
        "id": "interval_decomposition",
        "weight": 0.7
      }
    ],
    "skill_atoms": [
      {
        "id": "greedy.sorting_key",
        "role": "primary",
        "weight": 1.0
      },
      {
        "id": "greedy.exchange_argument",
        "role": "supporting",
        "weight": 0.7
      }
    ],
    "solution_signature": {
      "main_object": "set of selected non-overlapping intervals",
      "main_condition": "next interval must start after the last selected end",
      "structural_property": "earliest finishing interval leaves maximum remaining space",
      "update_or_transition": "select the earliest finishing compatible interval",
      "answer_extraction": "number of selected intervals",
      "complexity_bottleneck": "sorting intervals by end time"
    },
    "template_specific": {
      "type": "greedy",
      "sorting_key": "increasing end time",
      "greedy_choice": "select the interval with earliest finishing time",
      "invariant": "chosen intervals leave maximum remaining space",
      "exchange_argument": "any optimal solution can replace its first interval with the earliest finishing interval"
    },
    "core_computations": [
      {
        "name": "compatibility_check",
        "expression": "interval.start > last_selected_end",
        "role": "selection condition"
      }
    ],
    "procedure": [
      "Sort intervals by end time.",
      "Scan intervals in sorted order.",
      "Select an interval when it is compatible with the last selected interval.",
      "Return the selected count."
    ],
    "complexity": {
      "time": {
        "raw": "O(N log N)",
        "variables": {
          "N": "number of intervals"
        }
      },
      "space": {
        "auxiliary": "O(1)",
        "total": "O(N)"
      }
    }
  }
}
```

## BOJ Standalone Problem

`event` is `null` for a problem without contest context.

```json
{
  "ir_version": "1.0",
  "platform": {
    "name": "boj"
  },
  "event": null,
  "problem": {
    "id": "1918",
    "index": null,
    "name": "Postfix Notation",
    "difficulty": {
      "rating": 12,
      "source": "solved_ac"
    },
    "url": "https://www.acmicpc.net/problem/1918"
  },
  "source": {
    "url": "https://github.com/kss418/boj/blob/main/%EB%B0%B1%EC%A4%80/Gold/1918.%E2%80%85%ED%9B%84%EC%9C%84%E2%80%85%ED%91%9C%EA%B8%B0%EC%8B%9D/%ED%9B%84%EC%9C%84%E2%80%85%ED%91%9C%EA%B8%B0%EC%8B%9D.cc",
    "kind": "user_solution_code",
    "language": "cpp",
    "author": "kss418"
  },
  "solution": {
    "primary_paradigm": "data_structure",
    "algorithm_template": "stack_expression_parsing",
    "solution_models": [
      {
        "id": "expression_parsing",
        "weight": 1.0
      }
    ],
    "skill_atoms": [
      {
        "id": "data_structure.stack",
        "role": "primary",
        "weight": 1.0
      },
      {
        "id": "parsing.operator_precedence",
        "role": "primary",
        "weight": 0.9
      }
    ],
    "solution_signature": {
      "main_object": "operator stack and output expression",
      "main_condition": "operators must be emitted according to precedence and parentheses",
      "structural_property": "stack stores unresolved operators in precedence order",
      "update_or_transition": "push operators or pop higher-priority operators to output",
      "answer_extraction": "final output expression after flushing the stack",
      "complexity_bottleneck": "single pass over expression characters"
    },
    "template_specific": {
      "type": "stack_expression_parsing",
      "operator_stack": "stores unresolved operators",
      "output_rule": "append operands immediately and pop operators by precedence",
      "parentheses_rule": "pop until matching opening parenthesis"
    },
    "core_computations": [
      {
        "name": "precedence_comparison",
        "expression": "priority(top_operator) >= priority(current_operator)",
        "role": "operator emission condition"
      }
    ],
    "procedure": [
      "Scan the expression from left to right.",
      "Append operands to the output.",
      "Use a stack to delay operators until precedence allows emission.",
      "Flush remaining operators at the end."
    ],
    "complexity": {
      "time": {
        "raw": "O(N)",
        "variables": {
          "N": "expression length"
        }
      },
      "space": {
        "auxiliary": "O(N)",
        "total": "O(N)"
      }
    }
  }
}
```
