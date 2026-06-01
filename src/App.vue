<template>
  <main class="app-shell">
    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="kicker">AC Recommender</p>
          <h1>Embedding Inspector</h1>
        </div>
        <div class="health" :class="{ ok: isAligned, warn: hasLoadedFiles && !isAligned }">
          {{ alignmentLabel }}
        </div>
      </header>

      <section class="upload-grid" aria-label="File inputs">
        <label class="file-tile">
          <span>embeddings.npy</span>
          <strong>{{ npyFileName || 'Not loaded' }}</strong>
          <input type="file" accept=".npy" @change="loadNpy" />
        </label>

        <label class="file-tile">
          <span>documents.jsonl</span>
          <strong>{{ jsonlFileName || 'Not loaded' }}</strong>
          <input type="file" accept=".jsonl,.json,application/json" @change="loadJsonl" />
        </label>

        <label class="file-tile">
          <span>manifest.json</span>
          <strong>{{ manifestFileName || 'Optional' }}</strong>
          <input type="file" accept=".json,application/json" @change="loadManifest" />
        </label>
      </section>

      <section class="metrics" aria-label="Embedding summary">
        <article class="metric">
          <span>Rows</span>
          <strong>{{ formatNumber(npyInfo?.shape?.[0] ?? documentRecords.length) }}</strong>
        </article>
        <article class="metric">
          <span>Dimension</span>
          <strong>{{ formatNumber(vectorDimension) }}</strong>
        </article>
        <article class="metric">
          <span>Problems</span>
          <strong>{{ formatNumber(problemCount) }}</strong>
        </article>
        <article class="metric">
          <span>Views</span>
          <strong>{{ viewsLabel }}</strong>
        </article>
      </section>

      <section v-if="errors.length" class="message-list" aria-label="Errors">
        <p v-for="error in errors" :key="error">{{ error }}</p>
      </section>

      <section class="content-grid">
        <article class="panel">
          <div class="panel-heading">
            <h2>Vector File</h2>
            <span>{{ npyInfo ? npyInfo.version : '-' }}</span>
          </div>

          <dl class="detail-list">
            <div>
              <dt>dtype</dt>
              <dd>{{ npyInfo?.dtype || '-' }}</dd>
            </div>
            <div>
              <dt>shape</dt>
              <dd>{{ npyInfo ? npyInfo.shape.join(' x ') : '-' }}</dd>
            </div>
            <div>
              <dt>order</dt>
              <dd>{{ npyInfo ? (npyInfo.fortranOrder ? 'Fortran' : 'C') : '-' }}</dd>
            </div>
            <div>
              <dt>bytes</dt>
              <dd>{{ formatBytes(npyInfo?.dataBytes) }}</dd>
            </div>
          </dl>
        </article>

        <article class="panel">
          <div class="panel-heading">
            <h2>Manifest</h2>
            <span>{{ manifest ? 'Loaded' : '-' }}</span>
          </div>

          <dl class="detail-list">
            <div>
              <dt>model</dt>
              <dd>{{ manifest?.model_id || '-' }}</dd>
            </div>
            <div>
              <dt>documents</dt>
              <dd>{{ formatNumber(manifest?.document_count) }}</dd>
            </div>
            <div>
              <dt>ir</dt>
              <dd>{{ formatNumber(manifest?.ir_count) }}</dd>
            </div>
            <div>
              <dt>normalized</dt>
              <dd>{{ formatBoolean(manifest?.normalize_embeddings) }}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section class="table-panel">
        <div class="table-toolbar">
          <div>
            <h2>Contests</h2>
            <span>{{ formatNumber(filteredContests.length) }} contests</span>
          </div>
          <input v-model="query" type="search" placeholder="contest, problem id, name" />
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Contest</th>
                <th>Problems</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="contest in visibleContests"
                :key="contest.contest_id"
                :class="{ selected: contest.problems.some((problem) => problem.problem_id === selectedProblem?.problem_id) }"
              >
                <td>
                  <strong class="contest-id">{{ contest.contest_id }}</strong>
                  <span class="contest-count">{{ contest.problems.length }} problems</span>
                </td>
                <td class="problem-cell">
                  <div class="problem-strip" :style="{ '--slot-count': contest.slots.length }">
                    <template v-for="slot in contest.slots" :key="slot.key">
                      <button
                        v-if="slot.problem"
                        type="button"
                        class="problem-chip"
                        :class="{ active: selectedProblem?.problem_id === slot.problem.problem_id }"
                        :title="slot.problem.problem_name || slot.problem.problem_id"
                        @click="selectedProblemId = slot.problem.problem_id"
                      >
                        {{ problemSlotLabel(slot) }}
                      </button>
                      <span
                        v-else
                        class="problem-chip empty"
                        :title="`${slot.label} empty`"
                        aria-hidden="true"
                      ></span>
                    </template>
                  </div>
                </td>
              </tr>
              <tr v-if="!visibleContests.length">
                <td colspan="2" class="empty-cell">No contests</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="selection-panel">
        <div class="panel-heading">
          <h2>Selected Problem</h2>
          <span>{{ selectedProblemLabel }}</span>
        </div>

        <div v-if="selectedViewOptions.length" class="view-picker" aria-label="Embedding view">
          <button
            v-for="option in selectedViewOptions"
            :key="option.id"
            type="button"
            class="view-button"
            :class="{ active: selectedView === option.id }"
            @click="selectedView = option.id"
          >
            <strong>{{ viewLabel(option.id) }}</strong>
            <span>row {{ option.record.embedding_index }}</span>
          </button>
        </div>

        <div class="selected-grid">
          <dl class="detail-list">
            <div>
              <dt>embedding_id</dt>
              <dd>{{ selectedRecord?.embedding_id || '-' }}</dd>
            </div>
            <div>
              <dt>problem_url</dt>
              <dd>
                <a
                  v-if="selectedRecord?.metadata.problem_url"
                  :href="selectedRecord.metadata.problem_url"
                  target="_blank"
                  rel="noreferrer"
                >
                  {{ selectedRecord.metadata.problem_url }}
                </a>
                <span v-else>-</span>
              </dd>
            </div>
            <div>
              <dt>source_kind</dt>
              <dd>{{ selectedRecord?.metadata.source_kind || '-' }}</dd>
            </div>
            <div>
              <dt>ir_path</dt>
              <dd>{{ selectedRecord?.metadata.ir_path || '-' }}</dd>
            </div>
          </dl>

          <pre class="sample">{{ selectedVectorSample }}</pre>
          <pre class="sample ir-preview">{{ selectedIrPreview }}</pre>
        </div>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { parseNpy, readNpyValues } from './utils/npy'

const DEFAULT_EMBEDDING_DIR = '/embeddings/qwen3-embedding-0.6b-all'
const VIEW_ORDER = ['skill', 'solution_structure', 'combined']
const DEFAULT_PROBLEM_INDEX_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

const npyFileName = ref('')
const jsonlFileName = ref('')
const manifestFileName = ref('')
const npyInfo = ref(null)
const documentRecords = ref([])
const manifest = ref(null)
const query = ref('')
const selectedProblemId = ref(null)
const selectedView = ref('skill')
const errors = ref([])
const isAutoLoading = ref(false)
const selectedIr = ref(null)
const irError = ref('')
let irRequestId = 0

const hasLoadedFiles = computed(() => Boolean(npyInfo.value || documentRecords.value.length))
const vectorDimension = computed(() => npyInfo.value?.shape?.at(-1) ?? manifest.value?.vector_dimension)
const problemRecords = computed(() => groupRecordsByProblem(documentRecords.value))
const problemById = computed(() => new Map(problemRecords.value.map((problem) => [problem.problem_id, problem])))
const problemSlotLabels = computed(() => buildProblemSlotLabels(problemRecords.value))
const contestRecords = computed(() => groupProblemsByContest(problemRecords.value, problemSlotLabels.value))
const problemCount = computed(() => problemRecords.value.length || manifest.value?.ir_count || 0)
const views = computed(() => {
  const values = new Set(
    documentRecords.value
      .map((record) => record.view || record.metadata.view || inferView(record.embedding_id))
      .filter(Boolean),
  )
  return sortViews([...values])
})
const viewsLabel = computed(() => (views.value.length ? views.value.map(viewLabel).join(', ') : '-'))
const isAligned = computed(() => {
  if (!npyInfo.value || !documentRecords.value.length) return false
  return npyInfo.value.shape[0] === documentRecords.value.length
})
const alignmentLabel = computed(() => {
  if (isAutoLoading.value) return 'Loading 0.6B'
  if (!hasLoadedFiles.value) return 'Idle'
  if (!npyInfo.value) return 'JSONL only'
  if (!documentRecords.value.length) return 'NPY only'
  return isAligned.value ? 'Rows aligned' : 'Row mismatch'
})
const filteredContests = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return contestRecords.value
  return contestRecords.value.filter((contest) => contest.searchText.includes(term))
})
const visibleContests = computed(() => filteredContests.value.slice(0, 200))
const selectedProblem = computed(
  () => problemById.value.get(selectedProblemId.value) ?? visibleContests.value[0]?.problems[0] ?? null,
)
const selectedViewOptions = computed(() => {
  if (!selectedProblem.value) return []
  return selectedProblem.value.viewNames.map((view) => ({
    id: view,
    record: selectedProblem.value.views.get(view),
  }))
})
const selectedRecord = computed(() => {
  const problem = selectedProblem.value
  if (!problem) return null
  return problem.views.get(selectedView.value) ?? problem.views.get(problem.viewNames[0]) ?? problem.records[0] ?? null
})
const selectedProblemLabel = computed(() => selectedProblem.value?.problem_id || '-')
const selectedVectorSample = computed(() => {
  if (!npyInfo.value || !selectedRecord.value) return '[]'
  try {
    const values = readNpyValues(npyInfo.value, selectedRecord.value.embedding_index, 8)
    return JSON.stringify(values, null, 2)
  } catch (error) {
    return String(error.message || error)
  }
})
const selectedIrPreview = computed(() => {
  if (irError.value) return irError.value
  if (!selectedIr.value) return '{}'

  return JSON.stringify(
    {
      problem: selectedIr.value.problem,
      event: selectedIr.value.event,
      solution: {
        primary_paradigm: selectedIr.value.solution?.primary_paradigm,
        specific_paradigm: selectedIr.value.solution?.specific_paradigm,
        algorithm_template: selectedIr.value.solution?.algorithm_template,
        complexity: selectedIr.value.solution?.complexity,
      },
    },
    null,
    2,
  )
})

onMounted(() => {
  loadDefaultBundle()
})

watch(selectedProblem, (problem) => {
  if (!problem) return
  if (!problem.views.has(selectedView.value)) {
    selectedView.value = preferredView(problem)
  }
})

watch(selectedRecord, (record) => {
  loadSelectedIr(record)
})

async function loadDefaultBundle() {
  isAutoLoading.value = true
  errors.value = []
  try {
    const [manifestData, jsonlText, npyBuffer] = await Promise.all([
      fetchJson(`${DEFAULT_EMBEDDING_DIR}/manifest.json`),
      fetchText(`${DEFAULT_EMBEDDING_DIR}/documents.jsonl`),
      fetchBuffer(`${DEFAULT_EMBEDDING_DIR}/embeddings.npy`),
    ])

    manifest.value = manifestData
    documentRecords.value = parseJsonl(jsonlText)
    npyInfo.value = parseNpy(npyBuffer)
    manifestFileName.value = 'qwen3-embedding-0.6b-all/manifest.json'
    jsonlFileName.value = 'qwen3-embedding-0.6b-all/documents.jsonl'
    npyFileName.value = 'qwen3-embedding-0.6b-all/embeddings.npy'
    selectFirstProblem()
  } catch (error) {
    errors.value.push(`0.6B default load failed: ${String(error.message || error)}`)
  } finally {
    isAutoLoading.value = false
  }
}

async function loadNpy(event) {
  const file = event.target.files?.[0]
  if (!file) return
  npyFileName.value = file.name
  await runFileTask(async () => {
    const buffer = await file.arrayBuffer()
    npyInfo.value = parseNpy(buffer)
    if (!selectedProblemId.value && documentRecords.value.length) {
      selectFirstProblem()
    }
  })
}

async function loadJsonl(event) {
  const file = event.target.files?.[0]
  if (!file) return
  jsonlFileName.value = file.name
  await runFileTask(async () => {
    const text = await file.text()
    documentRecords.value = parseJsonl(text)
    selectFirstProblem()
  })
}

async function loadManifest(event) {
  const file = event.target.files?.[0]
  if (!file) return
  manifestFileName.value = file.name
  await runFileTask(async () => {
    manifest.value = JSON.parse(await file.text())
  })
}

async function runFileTask(task) {
  errors.value = []
  try {
    await task()
  } catch (error) {
    errors.value.push(String(error.message || error))
  }
}

async function loadSelectedIr(record) {
  const requestId = ++irRequestId
  selectedIr.value = null
  irError.value = ''

  const irPath = record?.metadata?.ir_path
  if (!irPath) return

  try {
    const data = await fetchJson(`/${irPath}`)
    if (requestId === irRequestId) {
      selectedIr.value = data
    }
  } catch (error) {
    if (requestId === irRequestId) {
      irError.value = `IR load failed: ${String(error.message || error)}`
    }
  }
}

function parseJsonl(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const record = JSON.parse(line)
      if (!Number.isInteger(record.embedding_index)) {
        throw new Error(`documents.jsonl line ${index + 1}: missing integer embedding_index`)
      }
      return {
        embedding_index: record.embedding_index,
        embedding_id: record.embedding_id ?? String(record.embedding_index),
        view: record.view ?? null,
        text: record.text ?? '',
        text_sha256: record.text_sha256 ?? '',
        metadata: record.metadata && typeof record.metadata === 'object' ? record.metadata : {},
      }
    })
}

function groupRecordsByProblem(records) {
  const byProblem = new Map()

  for (const record of records) {
    const metadata = record.metadata
    const view = record.view || metadata.view || inferView(record.embedding_id)
    const problemId =
      metadata.problem_id || inferProblemId(record.embedding_id) || `row-${record.embedding_index}`

    if (!byProblem.has(problemId)) {
      byProblem.set(problemId, {
        problem_id: problemId,
        problem_index: metadata.problem_index || '',
        problem_name: metadata.problem_name || '',
        problem_url: metadata.problem_url || '',
        event_id: metadata.event_id || '',
        event_series: metadata.event_series || '',
        event_number: metadata.event_number || '',
        ir_path: metadata.ir_path || '',
        records: [],
        rows: [],
        views: new Map(),
      })
    }

    const problem = byProblem.get(problemId)
    problem.records.push(record)
    problem.rows.push(record.embedding_index)

    if (view) {
      problem.views.set(view, record)
    }

    problem.problem_name ||= metadata.problem_name || ''
    problem.problem_index ||= metadata.problem_index || ''
    problem.problem_url ||= metadata.problem_url || ''
    problem.event_id ||= metadata.event_id || ''
    problem.event_series ||= metadata.event_series || ''
    problem.event_number ||= metadata.event_number || ''
    problem.ir_path ||= metadata.ir_path || ''
  }

  return [...byProblem.values()].map((problem) => {
    const sortedRows = [...problem.rows].sort((left, right) => left - right)
    const viewNames = sortViews([...problem.views.keys()])
    return {
      ...problem,
      rowLabel: formatRows(sortedRows),
      viewNames,
      searchText: [
        problem.problem_id,
        problem.problem_index,
        problem.problem_name,
        problem.problem_url,
        problem.event_id,
        problem.ir_path,
        ...viewNames,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase(),
    }
  })
}

function groupProblemsByContest(problems, slotLabels) {
  const byContest = new Map()

  for (const problem of problems) {
    const contestId = problem.event_id || inferContestId(problem.problem_id) || 'standalone'

    if (!byContest.has(contestId)) {
      byContest.set(contestId, {
        contest_id: contestId,
        event_series: problem.event_series || '',
        event_number: problem.event_number || '',
        problems: [],
      })
    }

    byContest.get(contestId).problems.push(problem)
  }

  return [...byContest.values()].map((contest) => {
    const problemsInOrder = sortProblems(contest.problems)
    const problemsBySlot = new Map(
      problemsInOrder.map((problem) => [canonicalProblemSlot(problem.problem_index), problem]),
    )
    return {
      ...contest,
      problems: problemsInOrder,
      slots: slotLabels.map((label) => ({
        key: `${contest.contest_id}-${label}`,
        label,
        problem: problemsBySlot.get(canonicalProblemIndex(label)) ?? null,
      })),
      searchText: [
        contest.contest_id,
        contest.event_series,
        contest.event_number,
        ...problemsInOrder.flatMap((problem) => [
          problem.problem_id,
          problem.problem_index,
          problem.problem_name,
          problem.ir_path,
        ]),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase(),
    }
  })
}

function sortProblems(problems) {
  return [...problems].sort((left, right) => {
    const indexOrder = compareProblemIndices(left.problem_index, right.problem_index)
    if (indexOrder !== 0) return indexOrder
    return left.problem_id.localeCompare(right.problem_id, undefined, { numeric: true, sensitivity: 'base' })
  })
}

function buildProblemSlotLabels(problems) {
  const labels = new Set(DEFAULT_PROBLEM_INDEX_ORDER)
  for (const problem of problems) {
    const label = canonicalProblemSlot(problem.problem_index)
    if (label) labels.add(label)
  }
  return [...labels].sort(compareProblemIndices)
}

function compareProblemIndices(left, right) {
  const leftRank = problemIndexRank(left)
  const rightRank = problemIndexRank(right)
  if (leftRank !== rightRank) return leftRank - rightRank
  return String(left || '').localeCompare(String(right || ''), undefined, {
    numeric: true,
    sensitivity: 'base',
  })
}

function problemIndexRank(index) {
  const label = canonicalProblemIndex(index)
  if (!label) return 900
  if (label.toLowerCase() === 'ex') return 1000

  const defaultIndex = DEFAULT_PROBLEM_INDEX_ORDER.indexOf(label)
  if (defaultIndex !== -1) return defaultIndex

  if (/^[A-Z]$/i.test(label)) {
    return label.toUpperCase().charCodeAt(0) - 'A'.charCodeAt(0)
  }

  return 800
}

function canonicalProblemIndex(index) {
  if (index === null || index === undefined) return ''
  const label = String(index).trim()
  if (label.toLowerCase() === 'ex') return 'Ex'
  return label.toUpperCase()
}

function canonicalProblemSlot(index) {
  const label = canonicalProblemIndex(index)
  return label === 'Ex' ? 'H' : label
}

function selectFirstProblem() {
  const firstProblem = contestRecords.value[0]?.problems[0] ?? null
  selectedProblemId.value = firstProblem?.problem_id ?? null
  selectedView.value = firstProblem ? preferredView(firstProblem) : 'skill'
}

function preferredView(problem) {
  return VIEW_ORDER.find((view) => problem.views.has(view)) ?? problem.viewNames[0] ?? 'skill'
}

function sortViews(viewNames) {
  return viewNames.sort((left, right) => {
    const leftIndex = VIEW_ORDER.indexOf(left)
    const rightIndex = VIEW_ORDER.indexOf(right)
    if (leftIndex !== -1 || rightIndex !== -1) {
      return (leftIndex === -1 ? VIEW_ORDER.length : leftIndex) - (rightIndex === -1 ? VIEW_ORDER.length : rightIndex)
    }
    return left.localeCompare(right)
  })
}

function viewLabel(view) {
  if (view === 'solution_structure') return 'solution_structure'
  if (view === 'combined') return 'combined'
  return view
}

function inferView(embeddingId) {
  if (typeof embeddingId !== 'string' || !embeddingId.includes('#')) return ''
  return embeddingId.split('#').at(-1) || ''
}

function inferProblemId(embeddingId) {
  if (typeof embeddingId !== 'string' || !embeddingId.includes('#')) return ''
  return embeddingId.split('#')[0] || ''
}

function inferContestId(problemId) {
  if (typeof problemId !== 'string') return ''
  const match = problemId.match(/^(.+?)_[a-z0-9]+$/i)
  return match?.[1] ?? ''
}

function problemSlotLabel(slot) {
  if (!slot.problem) return slot.label
  return canonicalProblemIndex(slot.problem.problem_index) || slot.label
}

function formatRows(rows) {
  if (!rows.length) return '-'
  if (rows.length === 1) return String(rows[0])
  if (rows.length <= 3) return rows.join(', ')
  return `${rows[0]}-${rows.at(-1)} (${rows.length})`
}

async function fetchJson(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${url} returned ${response.status}`)
  return response.json()
}

async function fetchText(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${url} returned ${response.status}`)
  return response.text()
}

async function fetchBuffer(url) {
  const response = await fetch(url)
  if (!response.ok) throw new Error(`${url} returned ${response.status}`)
  return response.arrayBuffer()
}

function formatNumber(value) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString() : '-'
}

function formatBytes(value) {
  if (!Number.isFinite(Number(value))) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = Number(value)
  let unit = 0
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024
    unit += 1
  }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`
}

function formatBoolean(value) {
  if (value === true) return 'true'
  if (value === false) return 'false'
  return '-'
}
</script>
