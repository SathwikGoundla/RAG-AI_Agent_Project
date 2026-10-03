'use client'
import { useState } from 'react'
import { BookOpen, Loader2, Download, RotateCcw } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function StudyPlanPanel({ docCount }: { docCount: number }) {
  const [topic, setTopic] = useState('')
  const [duration, setDuration] = useState('1 week')
  const [level, setLevel] = useState('beginner')
  const [goal, setGoal] = useState('')
  const [plan, setPlan] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const generate = async () => {
    if (!topic.trim()) { setErr('Enter a topic'); return }
    setLoading(true); setErr(''); setPlan('')
    try {
      const res = await fetch('/api/studyplan', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, duration, level, goal }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      setPlan(data.plan)
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  const download = () => {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([plan], { type: 'text/markdown' }))
    a.download = `study-plan-${topic.replace(/\s+/g, '-')}.md`
    a.click()
  }

  return (
    <div className="h-full overflow-y-auto p-5 max-w-2xl mx-auto w-full">
      <div className="text-center mb-6">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-400 flex items-center justify-center mx-auto mb-3 shadow-xl">
          <BookOpen className="w-7 h-7 text-white" />
        </div>
        <h2 className="text-xl font-bold text-primary">Study Plan Generator</h2>
        <p className="text-sm text-muted mt-1">
          {docCount > 0 ? `Using your ${docCount} uploaded document(s)` : 'Create a personalized learning schedule'}
        </p>
      </div>

      <div className="bg-surface border border-border rounded-2xl p-5 space-y-4">
        <div>
          <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-2">Topic *</label>
          <input value={topic} onChange={e => setTopic(e.target.value)}
            placeholder="e.g. Machine Learning, Data Structures, NLP…"
            className="w-full bg-input border border-border rounded-xl px-4 py-3 text-sm text-primary placeholder:text-subtle focus:outline-none focus:border-emerald-500 transition-colors" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-2">Duration</label>
            <select value={duration} onChange={e => setDuration(e.target.value)}
              className="w-full bg-input border border-border rounded-xl px-3 py-2.5 text-sm text-primary focus:outline-none focus:border-emerald-500">
              {['1 day','3 days','1 week','2 weeks','1 month'].map(d => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-2">Level</label>
            <select value={level} onChange={e => setLevel(e.target.value)}
              className="w-full bg-input border border-border rounded-xl px-3 py-2.5 text-sm text-primary focus:outline-none focus:border-emerald-500">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>
        <div>
          <label className="block text-xs font-bold text-muted uppercase tracking-wider mb-2">Goal <span className="normal-case font-normal text-subtle">(optional)</span></label>
          <input value={goal} onChange={e => setGoal(e.target.value)}
            placeholder="e.g. Pass exam, Build a project, Get certified…"
            className="w-full bg-input border border-border rounded-xl px-4 py-3 text-sm text-primary placeholder:text-subtle focus:outline-none focus:border-emerald-500 transition-colors" />
        </div>
        {err && <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-2 rounded-xl">❌ {err}</p>}
        <button onClick={generate} disabled={loading || !topic.trim()}
          className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-500 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-40 hover:from-emerald-700 hover:to-teal-600 transition-all shadow-lg">
          {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</> : <><BookOpen className="w-4 h-4" /> Generate Study Plan</>}
        </button>
      </div>

      {plan && (
        <div className="mt-5 bg-surface border border-border rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-border">
            <p className="font-bold text-primary text-sm">📋 Your Study Plan</p>
            <div className="flex gap-2">
              <button onClick={() => setPlan('')}
                className="text-xs text-muted hover:text-primary flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-hover">
                <RotateCcw className="w-3 h-3" /> Reset
              </button>
              <button onClick={download}
                className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                <Download className="w-3 h-3" /> Download
              </button>
            </div>
          </div>
          <div className="p-5 md text-sm text-primary">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{plan}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}
