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
            <h2>Documents</h2>
            <span>{{ formatNumber(filteredRecords.length) }} records</span>
          </div>
          <input v-model="query" type="search" placeholder="problem id, name, view" />
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Problem</th>
                <th>Name</th>
                <th>View</th>
                <th>IR</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in visibleRecords"
                :key="record.embedding_id || record.embedding_index"
                :class="{ selected: selectedIndex === record.embedding_index }"
                @click="selectedIndex = record.embedding_index"
              >
                <td>{{ record.embedding_index }}</td>
                <td>{{ record.metadata.problem_id || '-' }}</td>
                <td>{{ record.metadata.problem_name || '-' }}</td>
                <td>{{ record.view || record.metadata.view || '-' }}</td>
                <td>{{ record.metadata.ir_path || '-' }}</td>
              </tr>
              <tr v-if="!visibleRecords.length">
                <td colspan="5" class="empty-cell">No records</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="selection-panel">
        <div class="panel-heading">
          <h2>Selected Row</h2>
          <span>{{ selectedIndexLabel }}</span>
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
                <a v-if="selectedRecord?.metadata.problem_url" :href="selectedRecord.metadata.problem_url" target="_blank" rel="noreferrer">
                  {{ selectedRecord.metadata.problem_url }}
                </a>
                <span v-else>-</span>
              </dd>
            </div>
            <div>
              <dt>source_kind</dt>
              <dd>{{ selectedRecord?.metadata.source_kind || '-' }}</dd>
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

const npyFileName = ref('')
const jsonlFileName = ref('')
const manifestFileName = ref('')
const npyInfo = ref(null)
const documentRecords = ref([])
const manifest = ref(null)
const query = ref('')
const selectedIndex = ref(null)
const errors = ref([])
const isAutoLoading = ref(false)
const selectedIr = ref(null)
const irError = ref('')
let irRequestId = 0

const hasLoadedFiles = computed(() => Boolean(npyInfo.value || documentRecords.value.length))
const vectorDimension = computed(() => npyInfo.value?.shape?.at(-1) ?? manifest.value?.vector_dimension)
const problemCount = computed(() => {
  const ids = new Set(documentRecords.value.map((record) => record.metadata.problem_id).filter(Boolean))
  return ids.size || manifest.value?.ir_count || 0
})
const views = computed(() => {
  const values = new Set(
    documentRecords.value
      .map((record) => record.view || record.metadata.view)
      .filter(Boolean),
  )
  return [...values].sort()
})
const viewsLabel = computed(() => views.value.length ? views.value.join(', ') : '-')
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
const filteredRecords = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return documentRecords.value
  return documentRecords.value.filter((record) => {
    const metadata = record.metadata
    return [
      record.embedding_id,
      record.view,
      metadata.problem_id,
      metadata.problem_name,
      metadata.problem_url,
      metadata.ir_path,
      metadata.event_id,
    ]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(term))
  })
})
const visibleRecords = computed(() => filteredRecords.value.slice(0, 200))
const recordByIndex = computed(() => new Map(documentRecords.value.map((record) => [record.embedding_index, record])))
const selectedRecord = computed(() => recordByIndex.value.get(selectedIndex.value) ?? visibleRecords.value[0] ?? null)
const selectedIndexLabel = computed(() => selectedRecord.value ? `row ${selectedRecord.value.embedding_index}` : '-')
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
    selectedIndex.value = documentRecords.value[0]?.embedding_index ?? null
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
    if (selectedIndex.value === null && documentRecords.value.length) {
      selectedIndex.value = documentRecords.value[0].embedding_index
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
    selectedIndex.value = documentRecords.value[0]?.embedding_index ?? null
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
