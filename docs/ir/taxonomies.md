# Taxonomies

This document defines normalized ids used by Editorial IR v1.

Machine-readable taxonomy data lives in:

- `../../taxonomies/solution-models.json`
- `../../taxonomies/skill-atoms/*.json`

Skill atom JSON files are split by parent namespace, for example
`../../taxonomies/skill-atoms/graph.json`. Extractor and validator code should
read all JSON files under the directory. This Markdown file is for naming
rules, review policy, and human-readable summaries.

## Reference Validation

JSON Schema validates the shape of taxonomy references. A second validation
step must verify that every referenced id exists in the taxonomy data:

```text
solution.solution_models[].id in taxonomies/solution-models.json
solution.skill_atoms[].id in taxonomies/skill-atoms/*.json
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

Treat common aliases as naming hints, not additional ids. For Fenwick tree /
binary indexed tree / BIT, use the canonical id `data_structure.fenwick_tree`.

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
| `simple_condition_check` | Decision problem solved by a small fixed set of direct conditions. |
| `fixed_output_construction` | Construct the output directly from fixed formatting or coordinate rules. |
| `direct_access_query` | Answer by mapping a requested index or key to one stored value. |
| `linear_scan_accumulation` | Single pass that maintains a small amount of accumulated state. |
| `exhaustive_enumeration` | Enumerate the feasible candidate space directly and test each candidate. |
| `incremental_counting` | Accumulate counts or deltas while scanning independent records. |
| `data_structure_simulation` | Simulate updates and queries with an explicit data structure. |
| `precomputed_lookup` | Build a lookup table so later feasibility checks are local or constant time. |
| `quotient_interval_decomposition` | Group consecutive indices with the same quotient or arithmetic behavior. |
| `suffix_array_distinct_counting` | Count distinct substrings or subarrays using suffix array and LCP subtraction. |
| `combinatorial_formula` | Reduce the answer to a closed-form or inclusion-exclusion count. |
| `constructive_algorithm` | Build an object directly while preserving stated constraints. |
| `linked_structure_simulation` | Maintain predecessor and successor links under update operations. |
| `segment_tree_aggregation` | Maintain range aggregates with a segment tree or lazy propagation. |
| `prefix_counting` | Count valid intervals or substrings by comparing prefix-state keys. |
| `sliding_window_hashing` | Maintain a moving window and hash/frequency state for counting. |
| `math_formula_transformation` | Transform the statement into a direct mathematical formula or decomposition. |
| `block_decomposition` | Locate or count answers by decomposing a sequence into fixed blocks. |
| `poset_lis_reduction` | Reduce a partial-order chain or antichain problem to LIS-style tail updates. |
| `cyclic_rotation_scan` | Scan rotations of a sorted cyclic representation while maintaining an invariant. |
| `endpoint_query_processing` | Answer interval queries using preprocessed endpoint-indexed structures. |

## Skill Atoms

| ID | Meaning |
|---|---|
| `binary_search.answer` | Binary search over an answer value. |
| `binary_search.monotone_predicate` | Design or use a monotone feasibility predicate. |
| `binary_search.lower_bound` | Use lower_bound-style binary search over sorted data. |
| `binary_search.real_number` | Binary search over continuous values. |
| `binary_search.parametric_search` | Parametric search framing with a decision procedure. |
| `bitwise.bit_greedy` | Choose bits from most significant to least significant while preserving feasibility or optimality. |
| `bitwise.bitset_optimization` | Use packed bitsets and word-level operations to accelerate pair, subset, reachability, or parity computations. |
| `bitwise.parity_counting` | Count or maintain values by odd/even parity using XOR, popcount, or bit-level accumulators. |
| `bitwise.xor_pair_counting` | Count pairs of values subject to an XOR threshold, equality, or ordering condition. |
| `brute_force.subset_enumeration` | Enumerate subset masks or assignments and evaluate each candidate directly. |
| `brute_force.permutation_enumeration` | Enumerate permutations of a small set of elements. |
| `brute_force.backtracking` | Recursively explore candidates while maintaining and undoing local state. |
| `brute_force.meet_in_the_middle` | Split an exponential search into halves and combine partial results by lookup, sorting, or two-pointer matching. |
| `brute_force.reconstruction` | Recover an explicit witness, assignment, path, or operation sequence from enumerated states or matched partial results. |
| `geometry.convex_hull` | Build or use the convex hull of points to restrict feasible or optimal candidates. |
| `geometry.orientation_test` | Use cross products or signed area to determine orientation, convexity, or turn direction of points. |
| `geometry.half_plane_or_support_function` | Use a linear inequality, separating line, or support-function query over a convex set. |
| `geometry.symmetry_reduction` | Normalize geometric configurations by translation, rotation, reflection, or other symmetries. |
| `geometry.lattice_distance` | Compute distances or movement costs over grid, lattice, tiling, or coordinate-parity geometry. |
| `geometry.euclidean_distance` | Compute or compare Euclidean distances between coordinate points, often by squared distance. |
| `geometry.line_intersection` | Construct or compare intersections of lines, segments, or pair-defined geometric constraints. |
| `geometry.candidate_enumeration` | Enumerate a finite geometric candidate set induced by points, lines, intersections, tangencies, or boundaries. |
| `hashing.zobrist_hash` | Assign random values to objects and combine them additively or by XOR to compare multisets, states, or occurrence patterns. |
| `hashing.rolling_hash` | Maintain substring or sequence hashes with incremental window updates or prefix-hash differences. |
| `hashing.modular_fingerprint` | Represent large objects or algebraic expressions by residue vectors under one or more moduli for probabilistic equality checks. |
| `sorting.key_ordering` | Sort records by a key as preprocessing for scanning, searching, grouping, or aggregation without implying a greedy choice. |
| `array.linear_scan` | Linear scan over an array or sequence. |
| `array.prefix_sum` | Prefix sums or cumulative aggregates. |
| `array.difference_array` | Represent range additions or toggles by endpoint deltas and recover point values with a prefix scan. |
| `array.imos` | Use one-dimensional or multidimensional Imos difference updates to batch interval or rectangle coverage counts. |
| `array.suffix_aggregation` | Suffix aggregates or reverse cumulative values. |
| `array.indexing` | Use direct positional access, offset calculations, or kth-element indexing in an array or sequence. |
| `math.sum_of_deficits` | Sum deficits from a target value or threshold. |
| `math.ceil_division` | Integer ceiling division for counts or operation requirements. |
| `math.modular_arithmetic` | Modular arithmetic operations or identities. |
| `math.convolution` | Combine coefficient sequences by polynomial or distribution convolution. |
| `math.concave_convolution` | Exploit concavity or monotone slopes to merge DP sequences faster than naive max-plus convolution. |
| `math.ntt` | Use NTT-friendly modular convolution for polynomial or sequence multiplication. |
| `math.generating_function` | Encode counts or probabilities as coefficients of a generating function. |
| `math.formal_power_series` | Manipulate formal power series with polynomial arithmetic, inverses, products, or coefficient extraction. |
| `math.bostan_mori` | Extract coefficients of rational generating functions with Bostan-Mori even/odd polynomial reductions. |
| `math.linear_recurrence` | Model a sequence by a linear recurrence or rational generating function to compute distant terms or aggregates. |
| `math.dirichlet_convolution` | Combine arithmetic functions by divisor/product convolution, often through Dirichlet generating functions. |
| `math.power_projection` | Compute selected coefficients across powers of a polynomial or formal power series. |
| `math.floor_sum` | Evaluate sums of floor((a*i+b)/m) or equivalent quotient decompositions. |
| `math.binomial_coefficient` | Use binomial coefficients, factorial normalization, or modular combinations. |
| `math.gaussian_integer` | Reason about factors, norms, or residues in Gaussian integers. |
| `math.prime_factorization` | Factor integers and use prime exponents or prime classes in the solution. |
| `math.residue_distribution` | Maintain counts or probabilities over residue classes, often modulo one or more dimensions. |
| `math.xor_basis` | Build or use a linear basis over XOR values to reduce, test, or optimize bitwise combinations. |
| `math.determinant` | Compute a matrix determinant, often modulo a prime or as part of a graph-counting reduction. |
| `math.matrix_exponentiation` | Exponentiate a transition matrix or linear operator to apply many identical DP or automaton steps. |
| `math.case_reduction` | Reduce many apparent cases to a small set of canonical cases using invariants, recurrences, or normalization. |
| `probability.generating_function` | Represent probability distributions or hitting probabilities with generating functions. |
| `probability.expected_value` | Derive or compute expected values, expected costs, or expected scores from a random process. |
| `probability.probability_formula` | Compute a probability directly from cases, counts, or closed-form probability expressions. |
| `probability.probability_dp` | Maintain probability distributions, hitting probabilities, or win probabilities with dynamic programming transitions. |
| `probability.linearity_of_expectation` | Compute an expectation by summing expected contributions term by term, regardless of independence. |
| `dp.state_design` | Define DP states that capture necessary information. |
| `dp.tree` | Dynamic programming over rooted or unrooted tree structure. |
| `dp.rerooting` | Move a tree DP root across edges by reusing parent-side and child-side contributions. |
| `dp.knapsack` | Dynamic programming over capacity, budget, count, or resource constraints. |
| `dp.bitmask` | Dynamic programming with states indexed by masks over a small set of items or vertices. |
| `dp.digit` | Dynamic programming over digits with prefix, tightness, residue, or digit-sum state. |
| `dp.interval` | Dynamic programming over intervals, subarrays, substrings, or circular interval ranges. |
| `dp.lis` | Longest-increasing-subsequence style chain DP, including reductions to ordered tails or posets. |
| `dp.subset` | Dynamic programming over subsets with transitions between masks or subset partitions. |
| `dp.probability` | Dynamic programming over probabilities, expected values, or probability distributions. |
| `dp.alien` | Lagrangian-relaxation DP that searches a penalty parameter to recover a constrained optimum. |
| `dp.monge_optimization` | Optimize DP or labeling transitions using Monge, quadrangle inequality, or monotone-decision structure. |
| `dp.transition_optimization` | Optimize transition cost or transition enumeration. |
| `dp.slope_trick` | Represent and update a convex piecewise-linear DP cost function by slope changes or breakpoints. |
| `graph.bfs` | Breadth-first search. |
| `graph.dfs` | Depth-first search, including recursive traversal over graph or grid states. |
| `graph.dijkstra` | Dijkstra shortest path with non-negative edge weights. |
| `graph.matrix_tree_theorem` | Count spanning trees or directed arborescences using Laplacian minors and the Matrix-Tree theorem. |
| `graph.eulerian_trail_counting` | Count Eulerian circuits or trails in a graph, including reductions using the BEST theorem. |
| `graph.degree_condition` | Use vertex degrees or degree bounds to characterize, validate, or count graph structures. |
| `graph.lca` | Answer ancestor, path, or distance queries on a rooted tree using lowest common ancestors. |
| `graph.euler_tour` | Flatten a rooted tree into entry/exit order so subtree or path relationships become interval operations. |
| `graph.virtual_tree` | Compress marked tree vertices and their LCAs into an auxiliary tree preserving ancestor and path relationships. |
| `graph.heavy_light_decomposition` | Decompose tree paths or recursive tree processing into heavy paths and light transitions. |
| `graph.reachability` | Compute or maintain which vertices or states are reachable under graph constraints. |
| `graph.shortest_path_update` | Maintain shortest-path distances under added, removed, or restored edges. |
| `graph.state_expansion` | Expand graph nodes with extra state dimensions. |
| `graph.dag_game_dp` | Compute winning and losing states on an acyclic directed game graph. |
| `greedy.sorting_key` | Sort by a key that directly enables a greedy choice; use `sorting.key_ordering` for non-greedy preprocessing. |
| `greedy.exchange_argument` | Justify greedy choice by exchange argument. |
| `greedy.local_choice` | Make an immediately determined local choice that cannot hurt future feasibility or optimality. |
| `greedy.extreme_choice` | Choose the largest, smallest, earliest, latest, or otherwise extreme feasible option at each step. |
| `greedy.priority_queue_choice` | Repeatedly choose the currently best candidate from a priority queue or heap. |
| `greedy.reverse_processing` | Process operations in reverse so only the last effective choice for each object contributes. |
| `greedy.prefix_optimality` | Maintain an optimal prefix, selected prefix length, or prefix aggregate justified by greedy dominance. |
| `data_structure.segment_tree` | Segment tree for range queries or updates. |
| `data_structure.segment_tree_monoid` | Design a segment-tree aggregate as an associative monoid with custom merge semantics. |
| `data_structure.compressed_monoid` | Store a compact representative of a monoid value while preserving enough information for merges or queries. |
| `data_structure.fenwick_tree` | Fenwick tree, also known as a binary indexed tree or BIT, for prefix aggregates, point updates, and prefix lower_bound. |
| `data_structure.stack` | Stack used to manage nested, delayed, or last-in-first-out state. |
| `data_structure.cartesian_tree` | Build or use a Cartesian tree, often with a monotonic stack, to decompose ranges by minimum or maximum elements. |
| `data_structure.dynamic_array` | Maintain an appendable sequence with direct indexed access. |
| `data_structure.rollback_dsu` | Maintain disjoint-set union states with undo operations for offline divide-and-conquer or DFS traversal. |
| `string.z_algorithm` | Compute longest common prefixes from each string position using the Z-algorithm. |
| `string.manacher` | Compute palindrome radii around all centers in linear time using Manacher's algorithm or an equivalent scan. |
| `string.palindrome_algorithm` | Use palindrome-specific structure such as radii, mirrored positions, or longest palindromic prefix/suffix construction. |
| `string.rotation_matching` | Reduce string rotation equality to pattern matching in a doubled string. |
| `string.suffix_array` | Build or use a suffix array to order suffixes of a string or sequence. |
| `string.lcp_array` | Build or use longest-common-prefix values between adjacent suffix-array entries. |
| `string.distinct_substring_counting` | Count distinct substrings or subarrays using suffix ordering, LCP subtraction, or equivalent structure. |
| `string.run_length_encoding` | Compress consecutive equal symbols into runs and reason over run values or lengths. |
| `string.suffix_automaton` | Build or use a suffix automaton to represent substrings and transitions. |
| `string.aho_corasick` | Build or use an Aho-Corasick automaton for multi-pattern matching with failure links and output masks. |
| `string.game_dp` | Model game states over strings, substrings, or string automata and compute winning states. |
| `string.lexicographic_comparator` | Compare strings or concatenations lexicographically using LCP or equivalent structure. |
| `game.impartial_game_dp` | Classify impartial game positions as winning or losing from legal moves. |
| `parsing.operator_precedence` | Handle operators according to precedence and parentheses rules. |
| `implementation.overflow_guard` | Avoid overflow in accumulated values or search bounds. |
| `data_structure.disjoint_set_union` | Maintain connected components with union-find. |
| `graph.bipartite_coloring` | Assign or maintain two-color parity constraints in a graph. |
| `graph.shortest_path_dag` | Filter or orient edges that lie on shortest paths and reason on the resulting directed acyclic structure. |
| `graph.topological_order` | Process a DAG in topological order or use topological elimination for reachability, DP, or cycle detection. |
| `graph.scc` | Contract directed strongly connected components and reason on the condensation DAG. |
| `graph.bipartite_matching` | Find a maximum, perfect, or weighted matching in a bipartite graph, directly or through a flow reduction. |
| `graph.dag_path_cover` | Reduce a minimum path cover on a DAG to bipartite matching or maximum flow. |
| `graph.max_flow` | Compute a maximum feasible flow in a capacitated network. |
| `graph.min_cost_flow` | Send required flow while minimizing total edge cost, including weighted matching and circulation reductions. |
| `graph.min_cut` | Use the source-side residual reachability or cut capacity after max flow. |
| `graph.bridge_detection` | Find edges whose removal disconnects a graph or a relevant subgraph, often with DFS order and lowlink values. |
| `graph.flow_network_modeling` | Reduce constraints or choices to nodes, edges, capacities, and source/sink structure. |
| `graph.bipartite_independent_set` | Recover a maximum independent set in a bipartite graph via matching or min-cut duality. |
| `graph.flow_reconstruction` | Convert saturated or positive-flow edges back into explicit decisions or output objects. |
| `data_structure.small_to_large` | Merge smaller sets or containers into larger ones to bound total movement. |
| `data_structure.set` | Maintain explicit sets of elements with insertion, deletion, or membership checks. |
| `data_structure.frequency_table` | Maintain counts of values or keys under insertions, deletions, and frequency-based queries. |
| `data_structure.sqrt_decomposition` | Split data or queries into square-root sized blocks or heavy/light classes to balance rebuild, scan, and precomputation costs. |
| `data_structure.mo_algorithm` | Order offline range queries by block so adjacent queries can be answered by incremental endpoint moves. |
| `data_structure.block_list` | Maintain a sequence as blocks that can be split, trimmed, removed, inserted, or searched with amortized costs. |
| `data_structure.mergeable_blocks` | Maintain blocks that can be merged into equivalent larger blocks while preserving query behavior. |
| `data_structure.monoid_composition` | Compose associative transformations or summaries so multiple operations can be applied as one aggregate. |
| `data_structure.binary_counter` | Maintain power-of-two sized blocks and repeatedly merge equal-size blocks like binary carrying. |
| `data_structure.trie` | Store sequences or bit patterns in a prefix tree for traversal, lookup, or counting. |
| `data_structure.binary_trie` | Store integer bit patterns in a binary trie for XOR queries, pair counting, or bitwise order statistics. |
| `data_structure.priority_queue` | Maintain elements or states ordered by a maximum or minimum priority key. |
| `data_structure.order_statistic_tree` | Maintain dynamic ordered elements with rank, kth-element, or prefix lower_bound queries. |
| `data_structure.functional_graph` | Model one-outgoing-edge transitions with cycles, trees into cycles, or binary lifting tables. |
| `graph.spanning_tree` | Choose or use a spanning tree to define traversal labels, fundamental cycles, or connected structure. |
| `graph.tree_centroid` | Find or use a tree centroid as a balanced separator without recursively decomposing the tree. |
| `graph.centroid_decomposition` | Recursively decompose a tree by centroids so path or subtree contributions are counted at balanced separators. |
| `graph.minimum_spanning_tree` | Construct or reason about a minimum spanning tree. |
| `graph.tree_distance_verification` | Verify that a tree realizes required pairwise distances. |
| `graph.all_pairs_tree_distance` | Compute or check distances between all pairs of vertices in a tree. |
| `data_structure.persistent_segment_tree` | Maintain versioned segment tree roots under updates. |
| `data_structure.path_copying` | Create persistent updates by cloning nodes along an update path. |
| `data_structure.range_sum_query` | Query sums over an interval. |
| `data_structure.lazy_segment_tree` | Segment tree with lazy propagation for range updates. |
| `math.aggregate_formula` | Use an algebraic formula over maintained aggregates. |
| `math.sum_and_square_sum` | Maintain or use both sum and sum of squares. |
| `implementation.condition_check` | Evaluate a direct boolean condition. |
| `implementation.direct_formula` | Compute the answer with a direct formula. |
| `implementation.output_formatting` | Produce output in the exact required format. |
| `math.interval_length` | Compute the number of integers or values in an interval. |
