import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { createReadStream } from 'node:fs'
import { stat } from 'node:fs/promises'
import path from 'node:path'

const dataRoots = new Map([
  ['/embeddings/', path.resolve(process.cwd(), 'embeddings')],
  ['/ir/', path.resolve(process.cwd(), 'ir')],
])

export default defineConfig({
  plugins: [vue(), localDataFiles()],
  build: {
    outDir: 'frontend-dist',
  },
})

function localDataFiles() {
  return {
    name: 'local-data-files',
    configureServer(server) {
      server.middlewares.use(serveLocalData)
    },
    configurePreviewServer(server) {
      server.middlewares.use(serveLocalData)
    },
  }
}

function serveLocalData(request, response, next) {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    next()
    return
  }

  const requestUrl = new URL(request.url || '/', 'http://localhost')
  const pathname = decodeURIComponent(requestUrl.pathname)
  const entry = [...dataRoots.entries()].find(([prefix]) => pathname.startsWith(prefix))

  if (!entry) {
    next()
    return
  }

  const [prefix, root] = entry
  const relativePath = pathname.slice(prefix.length).replace(/^[/\\]+/, '')
  const filePath = path.resolve(root, relativePath)

  if (!filePath.startsWith(root + path.sep)) {
    response.statusCode = 403
    response.end('Forbidden')
    return
  }

  void sendFile(filePath, response, next)
}

async function sendFile(filePath, response, next) {
  try {
    const stats = await stat(filePath)
    if (!stats.isFile()) {
      next()
      return
    }

    response.setHeader('Content-Length', String(stats.size))
    response.setHeader('Content-Type', contentType(filePath))

    const stream = createReadStream(filePath)
    stream.on('error', () => {
      if (response.headersSent) {
        response.destroy()
      } else {
        next()
      }
    })
    stream.pipe(response)
  } catch {
    next()
  }
}

function contentType(filePath) {
  const extension = path.extname(filePath).toLowerCase()
  if (extension === '.json') return 'application/json; charset=utf-8'
  if (extension === '.jsonl') return 'application/x-ndjson; charset=utf-8'
  if (extension === '.npy') return 'application/octet-stream'
  return 'application/octet-stream'
}
