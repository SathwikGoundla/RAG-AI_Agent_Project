'use client'
import { useState, useRef, useEffect } from 'react'
import { Upload, FileText, Trash2, MessageSquare, Brain, BookOpen, X, CheckCircle, AlertCircle, FolderOpen, Loader2 } from 'lucide-react'
import ThemeToggle from './ThemeToggle'

interface Doc { id: string; name: string; size: number; uploadedAt?: string }
interface Props { tab: string; setTab: (t: string) => void; onDocsChange: (docs: Doc[]) => void }

function fmt(b: number) {
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB'
  return (b / 1024 / 1024).toFixed(1) + ' MB'
}

function fileIcon(name: string) {
  const ext = name.split('.').pop()?.toLowerCase()
  const colors: Record<string, string> = {
    pdf: 'text-red-400', txt: 'text-blue-400', md: 'text-purple-400',
    csv: 'text-green-400', json: 'text-yellow-400',
    png: 'text-pink-400', jpg: 'text-pink-400', jpeg: 'text-pink-400',
  }
  return colors[ext || ''] || 'text-slate-400'
}

export default function Sidebar({ tab, setTab, onDocsChange }: Props) {
  const [docs, setDocs] = useState<Doc[]>([])
  const [uploading, setUploading] = useState(false)
  const [drag, setDrag] = useState(false)
  const [toast, setToast] = useState<{ ok: boolean; msg: string } | null>(null)
  const [loadingDocs, setLoadingDocs] = useState(true)
  const ref = useRef<HTMLInputElement>(null)

  // Load persisted docs from server on mount
  useEffect(() => {
    fetch('/api/upload')
      .then(r => r.json())
      .then(data => {
        const loaded = data.docs || []
        setDocs(loaded)
        onDocsChange(loaded)
      })
      .catch(() => {})
      .finally(() => setLoadingDocs(false))
  }, [])

  const showToast = (ok: boolean, msg: string) => {
    setToast({ ok, msg })
    setTimeout(() => setToast(null), 3000)
  }

  const upload = async (file: File) => {
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      const newDoc = { id: data.id, name: file.name, size: file.size, uploadedAt: new Date().toISOString() }
      const updated = [...docs, newDoc]
      setDocs(updated)
      onDocsChange(updated)
      showToast(true, `"${file.name}" saved!`)
    } catch (e: any) {
      showToast(false, e.message || 'Upload failed')
    } finally { setUploading(false) }
  }

  const remove = async (id: string, name: string) => {
    await fetch(`/api/upload?id=${id}`, { method: 'DELETE' })
    const updated = docs.filter(d => d.id !== id)
    setDocs(updated)
    onDocsChange(updated)
    showToast(true, `"${name}" removed`)
  }

  const nav = [
    { id: 'chat', icon: MessageSquare, label: 'Chat', sub: 'Document Q&A' },
    { id: 'quiz', icon: Brain, label: 'Quiz', sub: 'Test yourself' },
    { id: 'study', icon: BookOpen, label: 'Study Plan', sub: 'Create schedule' },
  ]

  return (
    <aside className="w-64 bg-sidebar border-r border-border flex flex-col h-screen flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center shadow-glow">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="font-bold text-primary text-sm leading-none">LearnAgent</p>
            <p className="text-xs text-muted mt-0.5">by Sathwik Goundla</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="p-2 border-b border-border">
        {nav.map(n => {
          const Icon = n.icon
          const active = tab === n.id
          return (
            <button key={n.id} onClick={() => setTab(n.id)}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg mb-0.5 text-left transition-all ${
                active ? 'bg-accent/15 text-accent border border-accent/25' : 'text-muted hover:bg-hover hover:text-primary'
              }`}>
              <Icon className="w-4 h-4 flex-shrink-0" />
              <div>
                <p className="text-xs font-semibold leading-none">{n.label}</p>
                <p className="text-[10px] opacity-60 mt-0.5">{n.sub}</p>
              </div>
            </button>
          )
        })}
      </nav>

      {/* File Manager */}
      <div className="flex-1 overflow-y-auto p-3">
        <div className="flex items-center gap-2 mb-2 px-1">
          <FolderOpen className="w-3.5 h-3.5 text-accent" />
          <p className="text-xs font-bold text-muted uppercase tracking-widest">
            Documents
          </p>
          {docs.length > 0 && (
            <span className="ml-auto text-[10px] font-bold bg-accent/20 text-accent px-1.5 py-0.5 rounded-full">
              {docs.length}
            </span>
          )}
        </div>

        {/* Upload zone */}
        <div
          onDrop={e => { e.preventDefault(); setDrag(false); Array.from(e.dataTransfer.files).forEach(upload) }}
          onDragOver={e => { e.preventDefault(); setDrag(true) }}
          onDragLeave={() => setDrag(false)}
          onClick={() => !uploading && ref.current?.click()}
          className={`border-2 border-dashed rounded-xl p-3 text-center cursor-pointer transition-all mb-3 ${
            drag ? 'border-accent bg-accent/10' : 'border-border hover:border-accent/50 hover:bg-hover'
          }`}
        >
          <input ref={ref} type="file" multiple accept=".pdf,.txt,.md,.csv,.json,.png,.jpg,.jpeg,.docx" className="hidden"
            onChange={e => Array.from(e.target.files ?? []).forEach(upload)} />
          {uploading
            ? <div className="flex flex-col items-center gap-1.5">
                <Loader2 className="w-5 h-5 text-accent animate-spin" />
                <p className="text-xs text-muted">Saving to disk…</p>
              </div>
            : <div className="flex flex-col items-center gap-1.5">
                <Upload className="w-5 h-5 text-muted" />
                <p className="text-xs text-muted">Click or drag files</p>
                <p className="text-[10px] text-subtle">PDF, TXT, MD, CSV, Images</p>
              </div>
          }
        </div>

        {/* Toast */}
        {toast && (
          <div className={`mb-2 flex items-center gap-2 p-2 rounded-lg text-xs ${
            toast.ok ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
            {toast.ok ? <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" /> : <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />}
            <span className="truncate">{toast.msg}</span>
          </div>
        )}

        {/* File list — like file manager */}
        {loadingDocs ? (
          <div className="flex items-center gap-2 p-2 text-xs text-muted">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading saved files…
          </div>
        ) : docs.length === 0 ? (
          <div className="text-center py-4">
            <FolderOpen className="w-8 h-8 text-subtle mx-auto mb-2 opacity-40" />
            <p className="text-xs text-subtle">No documents yet</p>
            <p className="text-[10px] text-subtle opacity-60 mt-0.5">Upload files to get started</p>
          </div>
        ) : (
          <div className="space-y-1">
            {docs.map((d, i) => (
              <div key={d.id}
                className="flex items-center gap-2 px-2 py-2 rounded-lg bg-surface border border-border group hover:border-accent/30 hover:bg-hover transition-all">
                {/* File number badge */}
                <span className="text-[9px] font-bold text-subtle w-4 text-center flex-shrink-0">{i + 1}</span>
                <FileText className={`w-3.5 h-3.5 flex-shrink-0 ${fileIcon(d.name)}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] font-medium text-primary truncate leading-tight">{d.name}</p>
                  <p className="text-[9px] text-subtle">{fmt(d.size)}</p>
                </div>
                <button onClick={() => remove(d.id, d.name)}
                  className="opacity-0 group-hover:opacity-100 text-subtle hover:text-red-400 transition-all flex-shrink-0">
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer status */}
      <div className="p-3 border-t border-border space-y-2">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <p className="text-[10px] text-subtle">Groq AI • Fast Inference ⚡</p>
        </div>
        <ThemeToggle />
      </div>
    </aside>
  )
}
