// ─────────────────────────────────────────────────────────────
// Persistent Document Store
// • Saves extracted text index to .doc_store.json
// • Saves actual files to /uploaded_docs/ folder
// • Survives server restarts & terminal closes ✅
// ─────────────────────────────────────────────────────────────
import fs from 'fs'
import path from 'path'

export interface DocRecord {
  id: string
  name: string
  content: string
  size: number
  uploadedAt: string
  filePath: string  // actual file path on disk
}

const STORE_JSON = path.join(process.cwd(), '.doc_store.json')
const UPLOADS_DIR = path.join(process.cwd(), 'uploaded_docs')

// Ensure uploads folder exists
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR, { recursive: true })

function loadFromDisk(): Map<string, DocRecord> {
  try {
    if (fs.existsSync(STORE_JSON)) {
      const arr: DocRecord[] = JSON.parse(fs.readFileSync(STORE_JSON, 'utf-8'))
      const map = new Map<string, DocRecord>()
      // Only load records whose files still exist on disk
      arr.forEach(d => {
        if (fs.existsSync(d.filePath)) map.set(d.id, d)
      })
      return map
    }
  } catch (e) { console.error('[DocStore] Load error:', e) }
  return new Map()
}

function saveToDisk(docs: Map<string, DocRecord>) {
  try {
    fs.writeFileSync(STORE_JSON, JSON.stringify(Array.from(docs.values()), null, 2), 'utf-8')
  } catch (e) { console.error('[DocStore] Save error:', e) }
}

class DocStore {
  private docs: Map<string, DocRecord>
  constructor() {
    this.docs = loadFromDisk()
    console.log(`[DocStore] ✅ Loaded ${this.docs.size} doc(s) from disk`)
  }
  add(d: DocRecord) {
    this.docs.set(d.id, d)
    saveToDisk(this.docs)
  }
  remove(id: string) {
    const doc = this.docs.get(id)
    if (doc) {
      // Delete actual file from disk too
      try { if (fs.existsSync(doc.filePath)) fs.unlinkSync(doc.filePath) } catch {}
    }
    this.docs.delete(id)
    saveToDisk(this.docs)
  }
  getAll(): DocRecord[] { return Array.from(this.docs.values()) }
  count() { return this.docs.size }
  getUploadsDir() { return UPLOADS_DIR }
  getContext(): string {
    if (!this.docs.size) return ''
    return this.getAll().map(d => `[FILE: ${d.name}]\n${d.content}`).join('\n\n===\n\n')
  }
  getNames(): string { return this.getAll().map(d => d.name).join(', ') }
}

const g = global as any
if (!g.__docStore) g.__docStore = new DocStore()
export const docStore: DocStore = g.__docStore
