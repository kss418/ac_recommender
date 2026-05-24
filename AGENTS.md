# ac_recommender Agent Notes

This project is a small competitive-programming recommendation data workspace.
The current focus is:

1. fetch AtCoder editorial markdown files,
2. normalize selected editorial/problem solutions into Editorial IR v1 JSON,
3. validate IR shape and taxonomy references,
4. zip docs/scripts/data bundles for handoff.

Keep this file as an agent-facing map. Do not treat it as end-user README
content.

## Current Data State

- AtCoder editorial markdown currently exists under `editorials/ac/abc/450`
  through `editorials/ac/abc/457`.
- Pilot IR JSON currently exists under `ir/v1/ac/abc/450` through
  `ir/v1/ac/abc/457`.
- Pilot IR mirrors the editorial filename stem. If an editorial file is
  `editorials/ac/abc/457/D-raise-minimum.md`, the IR file is
  `ir/v1/ac/abc/457/D-raise-minimum.json`.
- The generated `ir/` and `editorials/` directories are ignored by git.
- There is no IR generator script by design right now. Existing IR files were
  manually created from fetched editorials.

## Important Directories

```text
docs/ir/                         Human-facing IR documentation
schema/editorial-ir-v1.schema.json
                                  Machine JSON Schema for Editorial IR v1
taxonomies/solution-models.json   Machine-readable solution model ids
taxonomies/skill-atoms/           Machine-readable skill atom ids, split by parent
scripts/                          Fetch, validate, and zip utilities
scripts/atcoder_editorials/       Fetcher helper modules
editorials/                       Fetched editorial markdown data, gitignored
ir/                               Generated IR JSON data, gitignored
dist/                             Misc output area, currently not central
```

## Editorial Folder Layout

Current fetched editorial layout mirrors AtCoder contest series and number:

```text
editorials/<platform>/<series>/<contest-number>/<PROBLEM_INDEX>-<problem-name>.md
editorials/<platform>/<series>/<contest-number>/index.json
```

Examples:

```text
editorials/ac/abc/457/D-raise-minimum.md
editorials/ac/abc/457/index.json
```

Notes:

- `platform` is `ac` for AtCoder.
- `series` is currently `abc`; the fetcher also supports `arc` and `agc`.
- Contest directory names use only the numeric part, such as `457`, because the
  series is already in the parent directory.
- `index.json` stores fetch metadata and the saved path/source records.
- Fetching prefers English editorial pages. If a section has no English
  editorial, the script can fall back to Japanese.
- When multiple editorial links exist for one problem section, the fetcher
  prefers `official_solution`.

## IR Folder Layout

Current pilot data keeps `ir/v1` as the version root, then mirrors the
editorial path after a short platform id:

```text
ir/v1/<platform>/<series>/<contest-number>/<PROBLEM_INDEX>-<problem-name>.json
```

Examples:

```text
ir/v1/ac/abc/457/D-raise-minimum.json
ir/v1/ac/abc/450/A-3-2-1-go.json
```

For standalone problems, use `problems` after the platform id, for example
`ir/v1/boj/problems/1918.json`. For Codeforces contest problems, use the contest
or round id after `cf`, for example `ir/v1/cf/1878/1878A.json`.

Platform ids are short stable keys: `ac` for AtCoder, `boj` for Baekjoon, and
`cf` for Codeforces.

## Editorial IR v1 Shape

Each IR JSON document is built around:

```json
{
  "ir_version": "1.0",
  "ir_language": "en",
  "platform": {},
  "event": null,
  "problem": {},
  "source": {},
  "solution": {}
}
```

Inside `solution`, the important retrieval fields are:

- `primary_paradigm`: broad category, for example `binary_search`, `dp`,
  `graph`, `greedy`, `data_structure`. Keep this field coarse and use only the
  documented enum values.
- `specific_paradigm`: detailed human-readable variant, for example
  `persistent_segment_tree`, `two_pointer_data_structure`, or
  `recursive_dynamic_programming`.
- `algorithm_template`: concrete template id.
- `solution_models`: weighted retrieval-oriented solution model ids from
  `taxonomies/solution-models.json`.
- `skill_atoms`: weighted fine-grained skill ids from
  `taxonomies/skill-atoms/*.json`.
- `solution_signature`: general retrieval fingerprint fields.
- `template_specific`: fields that belong naturally to the selected template.
- `core_computations`: one or more central expressions/operations.
- `procedure`: non-boilerplate algorithm outline.
- `complexity`: structured time/space complexity.

`source.language` is the original solution source language. `ir_language` is
the language used by normalized IR text fields and is currently `en`.

In v1, `solution.algorithm_template` should match
`solution.template_specific.type`.

## IR Docs

```text
docs/ir/README.md          Short index only
docs/ir/editorial-ir-v1.md Core schema skeleton and file layout
docs/ir/field-rules.md     Field meanings and empty-value policy
docs/ir/templates.md       Template-specific schema shapes
docs/ir/taxonomies.md      Human taxonomy policy and tables
docs/ir/examples.md        Complete examples
docs/ir/embedding.md       Rules for generating embedding text from IR
```

Keep long examples out of `editorial-ir-v1.md`; put complete examples in
`examples.md`. Keep concrete problem formulas out of `templates.md`; that file
should show generic template shapes.

## Script Map

### `scripts/fetch_atcoder_editorials.py`

Orchestrates AtCoder editorial fetching. It should remain mostly orchestration;
helper responsibilities live in `scripts/atcoder_editorials/`.

Useful commands:

```powershell
python scripts\fetch_atcoder_editorials.py abc457 --insecure
python scripts\fetch_atcoder_editorials.py --series ABC --from 450 --to 457 --insecure
python scripts\fetch_atcoder_editorials.py abc457 --dry-run
python scripts\fetch_atcoder_editorials.py abc457 --max-editorials 2 --insecure
```

Important options:

- positional contests: `abc457`, `arc180`, `agc001`, etc.
- `--series ABC --from 450 --to 457`: builds a contest range.
- `--out editorials`: output root. Default is `editorials`.
- `--editorial-lang en`: primary editorial language. Default is English.
- `--fallback-editorial-lang ja`: fallback when English is missing. Use `none`
  to disable fallback.
- `--insecure`: disables TLS verification. This local Python environment has
  had CA verification failures against AtCoder, so this is often needed here.
- `--dry-run`: discover links without saving files.

Fetcher helper modules:

```text
scripts/atcoder_editorials/cli.py
  argparse and contest-range construction

scripts/atcoder_editorials/contest.py
  contest id normalization, AtCoder URL construction, language params

scripts/atcoder_editorials/http_client.py
  urllib fetching, retries, decoding, TLS-error detection

scripts/atcoder_editorials/parsing.py
  editorial link extraction and HTML-to-markdown conversion

scripts/atcoder_editorials/storage.py
  output path construction, markdown/PDF saving, contest index writing

scripts/atcoder_editorials/models.py
  FetchResult and EditorialLink data models; source kind inference

scripts/atcoder_editorials/text.py
  whitespace cleanup and filename slugification

scripts/atcoder_editorials/constants.py
  supported series and default User-Agent
```

Current `source.kind` values used in IR/docs include:

```text
official_solution
user_editorial
user_solution_code
generated
unknown
```

For AtCoder official editorials, use `official_solution`.

### `scripts/validate_ir.py`

Validates IR JSON files and taxonomy references.

Useful commands:

```powershell
python scripts\validate_ir.py ir --skip-schema
python scripts\validate_ir.py ir --examples-md docs\ir\examples.md --skip-schema
python scripts\validate_ir.py ir --examples-md docs\ir\examples.md
```

Notes:

- Without `--skip-schema`, the script requires the `jsonschema` Python package.
- Taxonomy reference validation always checks that
  `solution.solution_models[].id` and `solution.skill_atoms[].id` exist in the
  JSON taxonomy files. Skill atom files are read from `taxonomies/skill-atoms/`.

### `scripts/zip_project_bundle.py`

Creates a timestamped project bundle zip in the repo root.

```powershell
python scripts\zip_project_bundle.py
python scripts\zip_project_bundle.py -o project-bundle-custom.zip
```

Default output:

```text
project-bundle-YYMMDD-HHMMSS.zip
```

Included roots:

```text
docs/ir/
schema/
scripts/
taxonomies/
```

Generated data under `editorials/` and `ir/` is not included in this bundle.

### `scripts/zip_data_bundle.py`

Creates timestamped data bundle zips in the repo root, split by data root.

```powershell
python scripts\zip_data_bundle.py
python scripts\zip_data_bundle.py -o data-bundle-custom.zip
```

Default outputs:

```text
data-bundle-YYMMDD-HHMMSS-editorials.zip
data-bundle-YYMMDD-HHMMSS-embeddings.zip
data-bundle-YYMMDD-HHMMSS-ir.zip
```

Included roots, one zip per root:

```text
editorials/
embeddings/
ir/
```

### `scripts/embed_ir.py`

Generates embedding documents and vectors from Editorial IR JSON. The script
implements the text views documented in `docs/ir/embedding.md`.

Useful local commands:

```powershell
python scripts\embed_ir.py --model-size 0.6b --overwrite
python scripts\embed_ir.py --model-size 0.6b --views skill combined --limit 10 --overwrite
python scripts\embed_ir.py --model-size 0.6b --views problem_identity --text-only --overwrite
python scripts\embed_ir.py --model-size 0.6b --text-only --overwrite
```

Default output:

```text
embeddings/qwen3-embedding-0.6b-all/
```

Output files:

```text
documents.jsonl
embeddings.npy
manifest.json
```

Notes:

- `--model-size 0.6b` maps to `Qwen/Qwen3-Embedding-0.6B`.
- Defaults are all IR files under `ir/` and recommendation views:
  `solution_structure`, `skill`, and `combined`.
- `problem_identity` is not generated by default. Generate it only for a
  separate debug/name-search index, for example with `--views problem_identity`.
- CPU-only PyTorch is slow for the full pilot set. Prefer a CUDA environment
  for full vector generation.

### `scripts/analyze_embeddings.py`

Analyzes an embedding output directory or standalone `.npy` file. If given an
embedding directory, it auto-loads `manifest.json` and `documents.jsonl`.

Useful commands:

```powershell
python scripts\analyze_embeddings.py embeddings\abc450-457\qwen3-embedding-0.6b-all
python scripts\analyze_embeddings.py embeddings\abc450-457\qwen3-embedding-0.6b-all --exclude-same-problem
python scripts\analyze_embeddings.py embeddings\abc450-457\qwen3-embedding-0.6b-all --no-pairs --json-output dist\embedding-analysis.json
```

It reports matrix shape, dtype, finite-value checks, row-norm statistics,
manifest/document consistency, view/event counts, exact duplicate rows, and
nearest cosine-similarity pairs. Pairwise analysis defaults to recommendation
semantics: `problem_identity` is excluded, same-problem pairs are excluded, and
`solution_structure`, `skill`, and `combined` are compared only against the
same view. Use `--include-problem-identity`, `--include-same-problem`, or
`--cross-view` only for debugging.

### `scripts/runpod_embed.py`

Runs `scripts/embed_ir.py` on a RunPod SSH GPU pod. This is a simple SSH/SCP
wrapper, not a RunPod API client. Create a GPU pod first, then pass its SSH
target, port, and optional key.

Useful commands:

```powershell
python scripts\runpod_embed.py root@ssh.runpod.io --port 12345 --identity-file "$env:USERPROFILE\.ssh\id_ed25519" --model-size 0.6b
python scripts\runpod_embed.py root@ssh.runpod.io --port 12345 --identity-file "$env:USERPROFILE\.ssh\id_ed25519" --limit 5 --views skill combined
python scripts\runpod_embed.py root@ssh.runpod.io --port 12345 --dry-run --limit 1
```

What it does:

```text
zip requirements/docs/schema/scripts/taxonomies/ir
upload bundle to the pod
create .venv-runpod on the pod
install requirements.txt
verify CUDA when --device cuda is used
run embed_ir.py remotely
download and extract the result zip into embeddings/
```

RunPod setup notes:

- Use a PyTorch + CUDA image or template. A plain Python/Ubuntu image will need
  extra CUDA/PyTorch setup and is not the intended path.
- The remote venv defaults to `--system-site-packages` so it can reuse the
  image's GPU-enabled `torch`.
- If the image already has all dependencies, pass `--skip-install`.
- If CUDA is not visible, the script stops before embedding.

## Validation Checklist

After editing docs or IR, run the smallest relevant checks:

```powershell
python scripts\validate_ir.py ir --skip-schema
python -c "import json, pathlib; json.loads(pathlib.Path(r'ir\v1\ac\abc\457\D-raise-minimum.json').read_text(encoding='utf-8')); print('json ok')"
git diff --check
```

If `jsonschema` is installed, prefer full validation:

```powershell
python scripts\validate_ir.py ir --examples-md docs\ir\examples.md
```

## Working Notes For Future Agents

- Do not add a README unless the user explicitly asks. This project currently
  uses `AGENTS.md` for agent-facing orientation and `docs/ir/README.md` only as
  a short IR-doc index.
- Do not introduce an IR generator unless the user asks for one. The user
  explicitly rejected adding a generator during the pilot IR creation.
- Preserve the split between:
  - raw fetched editorial markdown in `editorials/`,
  - normalized retrieval IR in `ir/`,
  - human schema docs in `docs/ir/`,
  - machine schema/taxonomy data in `schema/` and `taxonomies/`.
- Prefer adding new taxonomy ids to both the JSON data and `docs/ir/taxonomies.md`
  before using them in IR.
- For full embedding runs, prefer `scripts/runpod_embed.py` on a CUDA RunPod
  pod. Local Windows `.venv` may have CPU-only PyTorch; check with
  `python -c "import torch; print(torch.cuda.is_available())"` before assuming
  GPU acceleration.
- For recommendation search, use metadata view filters. Compare
  `solution_structure` with `solution_structure`, `skill` with `skill`, and
  `combined` with `combined`. Exclude `problem_identity` from recommendation
  scores; keep it only for debugging, joins, display, or problem-name lookup.
- Use `core_computations` as an array, even if there is only one central
  computation.
- Avoid boilerplate in `procedure`; do not include generic steps like "read
  input" unless input handling is itself the core trick.
- Do not use `greedy` as a fallback template. Prefer narrower templates such as
  `exhaustive_enumeration`, `two_pointer`, `segment_tree`,
  `data_structure_simulation`, `prefix_counting`, or `query_processing` when
  those better describe the solution.
- For binary-search-on-answer IR, keep the retrieval fingerprint in
  `solution_signature`, and put concrete search bounds/predicate details in
  `template_specific`.
