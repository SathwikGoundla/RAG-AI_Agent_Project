'use client'
import { useState } from 'react'
import { Brain, Loader2, CheckCircle, XCircle, RefreshCw, Trophy, ChevronRight, ChevronLeft, SkipForward, AlertCircle, Download } from 'lucide-react'

type QType = 'mcq' | 'msq' | 'short' | 'fillblank'
interface Q {
  id: number; type: QType; question: string; options: string[]
  answer: string | string[]; explanation: string
}
type Stage = 'setup' | 'quiz' | 'result'

const TYPE_INFO: Record<QType, { label: string; icon: string; desc: string; color: string }> = {
  mcq:       { label: 'MCQ',              icon: '🔘', desc: 'Single correct answer',          color: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  msq:       { label: 'Multi-Select',     icon: '☑️', desc: 'Select all correct answers',     color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
  short:     { label: 'Short Answer',     icon: '✏️', desc: 'Type your answer',               color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
  fillblank: { label: 'Fill in the Blank',icon: '📝', desc: 'Complete the sentence',           color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
}

export default function QuizPanel({ docCount }: { docCount: number }) {
  const [topic, setTopic] = useState('')
  const [count, setCount] = useState(5)
  const [diff, setDiff] = useState('medium')
  const [selectedTypes, setSelectedTypes] = useState<QType[]>(['mcq', 'msq', 'short', 'fillblank'])
  const [qs, setQs] = useState<Q[]>([])
  const [singleAns, setSingleAns] = useState<Record<number, string>>({})     // mcq, short, fillblank
  const [multiAns, setMultiAns] = useState<Record<number, Set<string>>>({})  // msq
  const [skipped, setSkipped] = useState<Set<number>>(new Set())
  const [cur, setCur] = useState(0)
  const [stage, setStage] = useState<Stage>('setup')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [score, setScore] = useState(0)

  const toggleType = (t: QType) => {
    setSelectedTypes(prev =>
      prev.includes(t) ? (prev.length > 1 ? prev.filter(x => x !== t) : prev) : [...prev, t]
    )
  }

  const generate = async () => {
    if (!docCount && !topic.trim()) { setErr('Upload a document or enter a topic.'); return }
    setLoading(true); setErr('')
    try {
      const res = await fetch('/api/quiz', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, count, difficulty: diff, types: selectedTypes }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error)
      if (!data.questions?.length) throw new Error('No questions. Try again.')
      setQs(data.questions)
      setSingleAns({}); setMultiAns({}); setSkipped(new Set()); setCur(0)
      setStage('quiz')
    } catch (e: any) { setErr(e.message) }
    finally { setLoading(false) }
  }

  // Check if question is answered
  const isAnswered = (q: Q) => {
    if (skipped.has(q.id)) return true
    if (q.type === 'msq') return (multiAns[q.id]?.size ?? 0) > 0
    return !!(singleAns[q.id]?.trim())
  }
  const allAnswered = qs.every(q => isAnswered(q))

  // Score calculation
  const calcScore = () => {
    let correct = 0
    qs.forEach(q => {
      if (skipped.has(q.id)) return
      if (q.type === 'msq') {
        const userSet = multiAns[q.id] ?? new Set()
        const correctSet = new Set(Array.isArray(q.answer) ? q.answer : [q.answer])
        if (userSet.size === correctSet.size && [...userSet].every(x => correctSet.has(x))) correct++
      } else {
        const ua = (singleAns[q.id] || '').toLowerCase().trim()
        const ca = (Array.isArray(q.answer) ? q.answer[0] : q.answer).toLowerCase().trim()
        if (ua === ca) correct++
      }
    })
    return correct
  }

  const submit = () => { setScore(calcScore()); setStage('result') }

  // Download quiz results as text
  const downloadResults = () => {
    const lines: string[] = [
      'LEARNAGENT — QUIZ RESULTS',
      '='.repeat(40),
      `Score: ${score} / ${qs.length} (${Math.round((score/qs.length)*100)}%)`,
      `Difficulty: ${diff.toUpperCase()}`,
      `Date: ${new Date().toLocaleString()}`,
      '='.repeat(40), '',
    ]
    qs.forEach((q, i) => {
      const skp = skipped.has(q.id)
      let ua = ''
      if (q.type === 'msq') ua = [...(multiAns[q.id] ?? [])].join(', ')
      else ua = singleAns[q.id] || ''
      const isCorrect = !skp && (() => {
        if (q.type === 'msq') {
          const us = new Set(multiAns[q.id] ?? [])
          const cs = new Set(Array.isArray(q.answer) ? q.answer : [q.answer])
          return us.size === cs.size && [...us].every(x => cs.has(x))
        }
        return ua.toLowerCase().trim() === (Array.isArray(q.answer) ? q.answer[0] : q.answer).toLowerCase().trim()
      })()
      lines.push(`Q${i+1} [${TYPE_INFO[q.type].label}] ${skp ? '⏭ SKIPPED' : isCorrect ? '✓ CORRECT' : '✗ WRONG'}`)
      lines.push(`Question: ${q.question}`)
      lines.push(`Your Answer: ${skp ? 'Skipped' : ua || '—'}`)
      lines.push(`Correct Answer: ${Array.isArray(q.answer) ? q.answer.join(', ') : q.answer}`)
      lines.push(`Explanation: ${q.explanation}`)
      lines.push('')
    })
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `quiz_results_${Date.now()}.txt`
    a.click()
  }

  // ── SETUP ──
  if (stage === 'setup') return (
    <div className="flex flex-col items-center justify-center h-full p-6 overflow-y-auto">
      <div className="w-full max-w-lg space-y-4">
        <div className="text-center mb-4">
          <div className="w-12 h-12 rounded-2xl bg-accent/20 border border-accent/30 flex items-center justify-center mx-auto mb-3">
            <Brain className="w-6 h-6 text-accent" />
          </div>
          <h2 className="text-lg font-bold text-primary">Quiz Generator</h2>
          <p className="text-xs text-muted mt-0.5">AI questions from your uploaded documents</p>
        </div>

        <div className="card space-y-4">
          <div>
            <label className="label">Topic {docCount > 0 && <span className="font-normal text-subtle normal-case ml-1">(blank = use uploaded docs)</span>}</label>
            <input value={topic} onChange={e => setTopic(e.target.value)} onKeyDown={e => e.key === 'Enter' && generate()}
              placeholder={docCount > 0 ? 'Leave blank for document-based quiz…' : 'Enter a topic…'}
              className="input w-full" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Questions</label>
              <select value={count} onChange={e => setCount(+e.target.value)} className="input w-full">
                {[3,5,7,10,15].map(n => <option key={n} value={n}>{n} Questions</option>)}
              </select>
            </div>
            <div>
              <label className="label">Difficulty</label>
              <select value={diff} onChange={e => setDiff(e.target.value)} className="input w-full">
                <option value="easy">🟢 Easy</option>
                <option value="medium">🟡 Medium</option>
                <option value="hard">🔴 Hard</option>
              </select>
            </div>
          </div>

          {/* Question type selector */}
          <div>
            <label className="label">Question Types</label>
            <div className="grid grid-cols-2 gap-2">
              {(Object.entries(TYPE_INFO) as [QType, typeof TYPE_INFO[QType]][]).map(([type, info]) => (
                <button key={type} onClick={() => toggleType(type)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-left transition-all ${
                    selectedTypes.includes(type)
                      ? `${info.color} border-current`
                      : 'border-border text-subtle hover:border-accent/30 hover:text-muted'
                  }`}>
                  <span className="text-base">{info.icon}</span>
                  <div>
                    <p className="text-xs font-semibold leading-none">{info.label}</p>
                    <p className="text-[10px] opacity-70 mt-0.5">{info.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {err && (
            <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-red-400 text-xs">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <p>{err}</p>
            </div>
          )}

          <button onClick={generate} disabled={loading || (!topic.trim() && !docCount)}
            className="btn-primary w-full">
            {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating…</> : <><Brain className="w-4 h-4" /> Generate Quiz</>}
          </button>
        </div>
      </div>
    </div>
  )

  // ── QUIZ ──
  const q = qs[cur]
  if (stage === 'quiz' && q) {
    const info = TYPE_INFO[q.type]
    const qAnswered = isAnswered(q)

    return (
      <div className="flex flex-col h-full p-5 max-w-2xl mx-auto w-full">
        {/* Header */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-bold text-primary">Q {cur + 1} / {qs.length}</span>
            <span className={`text-xs px-2.5 py-1 rounded-full font-bold border ${
              diff === 'easy' ? 'text-green-400 bg-green-500/10 border-green-500/20'
              : diff === 'medium' ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
              : 'text-red-400 bg-red-500/10 border-red-500/20'}`}>
              {diff.toUpperCase()}
            </span>
          </div>
          <div className="h-1 bg-surface rounded-full">
            <div className="h-1 bg-accent rounded-full transition-all" style={{ width: `${((cur + 1) / qs.length) * 100}%` }} />
          </div>
          <div className="flex gap-1 mt-2">
            {qs.map((x, i) => (
              <button key={x.id} onClick={() => setCur(i)}
                className={`flex-1 h-1 rounded-full transition-all ${
                  i === cur ? 'bg-accent' : skipped.has(x.id) ? 'bg-amber-500/50' : isAnswered(x) ? 'bg-green-500/60' : 'bg-border'}`} />
            ))}
          </div>
        </div>

        {/* Question card */}
        <div className="flex-1 overflow-y-auto">
          <div className="card space-y-4">
            <span className={`inline-block text-xs font-bold px-2.5 py-1 rounded-full border ${info.color}`}>
              {info.icon} {info.label}
            </span>
            <p className="text-base font-semibold text-primary leading-relaxed">{q.question}</p>

            {/* MCQ */}
            {q.type === 'mcq' && (
              <div className="space-y-2">
                {(q.options || []).map((opt, i) => (
                  <button key={i} onClick={() => !skipped.has(q.id) && setSingleAns(p => ({ ...p, [q.id]: opt }))}
                    disabled={skipped.has(q.id)}
                    className={`w-full text-left px-4 py-3 rounded-xl text-sm border-2 font-medium transition-all ${
                      singleAns[q.id] === opt ? 'border-accent bg-accent/10 text-accent' : 'border-border hover:border-accent/40 text-muted hover:text-primary'
                    } disabled:opacity-40 disabled:cursor-not-allowed`}>
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {/* MSQ */}
            {q.type === 'msq' && (
              <div className="space-y-2">
                <p className="text-xs text-purple-400 font-medium">☑️ Select ALL correct answers</p>
                {(q.options || []).map((opt, i) => {
                  const sel = multiAns[q.id]?.has(opt) ?? false
                  return (
                    <button key={i} onClick={() => {
                      if (skipped.has(q.id)) return
                      setMultiAns(p => {
                        const s = new Set(p[q.id] ?? [])
                        sel ? s.delete(opt) : s.add(opt)
                        return { ...p, [q.id]: s }
                      })
                    }}
                    disabled={skipped.has(q.id)}
                    className={`w-full text-left px-4 py-3 rounded-xl text-sm border-2 font-medium transition-all flex items-center gap-3 ${
                      sel ? 'border-purple-500 bg-purple-500/10 text-purple-300' : 'border-border hover:border-purple-400/40 text-muted hover:text-primary'
                    } disabled:opacity-40`}>
                      <div className={`w-4 h-4 rounded border-2 flex-shrink-0 flex items-center justify-center ${sel ? 'border-purple-500 bg-purple-500' : 'border-border'}`}>
                        {sel && <CheckCircle className="w-3 h-3 text-white" />}
                      </div>
                      {opt}
                    </button>
                  )
                })}
              </div>
            )}

            {/* Short Answer */}
            {q.type === 'short' && (
              <textarea value={singleAns[q.id] || ''} onChange={e => setSingleAns(p => ({ ...p, [q.id]: e.target.value }))}
                disabled={skipped.has(q.id)}
                placeholder={skipped.has(q.id) ? 'Skipped' : 'Type your answer here…'}
                rows={3}
                className="input w-full resize-none disabled:opacity-40" />
            )}

            {/* Fill in blank */}
            {q.type === 'fillblank' && (
              <div className="space-y-2">
                <p className="text-xs text-emerald-400">📝 Fill in the blank (___)</p>
                <input value={singleAns[q.id] || ''} onChange={e => setSingleAns(p => ({ ...p, [q.id]: e.target.value }))}
                  disabled={skipped.has(q.id)}
                  placeholder="Type what goes in the blank…"
                  className="input w-full disabled:opacity-40" />
              </div>
            )}

            {/* Skipped answer reveal */}
            {skipped.has(q.id) && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                <p className="text-xs text-amber-400 font-bold">⏭ Skipped</p>
                <p className="text-xs text-primary mt-1">Answer: <strong>{Array.isArray(q.answer) ? q.answer.join(', ') : q.answer}</strong></p>
                <p className="text-xs text-subtle mt-1">{q.explanation}</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <div className="mt-4 flex gap-2">
          {cur > 0 && (
            <button onClick={() => setCur(c => c - 1)} className="px-4 py-2.5 border border-border rounded-xl text-xs font-bold text-muted hover:bg-hover flex items-center gap-1">
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
          )}
          {!skipped.has(q.id) && !qAnswered && (
            <button onClick={() => { setSkipped(s => { const ns = new Set(s); ns.add(q.id); return ns }); if (cur < qs.length - 1) setCur(c => c + 1) }}
              className="px-4 py-2.5 border border-amber-500/30 bg-amber-500/10 rounded-xl text-xs font-bold text-amber-400 hover:bg-amber-500/20 flex items-center gap-1">
              <SkipForward className="w-4 h-4" /> Skip
            </button>
          )}
          {cur < qs.length - 1 ? (
            <button onClick={() => setCur(c => c + 1)} disabled={!qAnswered}
              className="flex-1 py-2.5 btn-primary disabled:opacity-30 flex items-center justify-center gap-2">
              Next <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button onClick={submit} disabled={!allAnswered}
              className="flex-1 py-2.5 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold text-sm flex items-center justify-center gap-2 disabled:opacity-30 transition-all">
              Submit <Trophy className="w-4 h-4" />
            </button>
          )}
        </div>
        {!allAnswered && cur === qs.length - 1 && (
          <p className="text-xs text-center text-subtle mt-2">Answer or skip all questions to submit</p>
        )}
      </div>
    )
  }

  // ── RESULT ──
  const pct = Math.round((score / qs.length) * 100)
  const skippedCount = skipped.size
  const [emoji, label, clr] = pct === 100 ? ['🏆','Perfect!','text-amber-400'] : pct >= 80 ? ['🌟','Excellent!','text-green-400'] : pct >= 60 ? ['👍','Good Job!','text-blue-400'] : ['📚','Keep Studying','text-orange-400']

  return (
    <div className="h-full overflow-y-auto p-5 max-w-2xl mx-auto w-full">
      {/* Score card */}
      <div className="card text-center mb-4">
        <p className="text-4xl mb-2">{emoji}</p>
        <p className={`text-3xl font-black ${clr}`}>{score}/{qs.length}</p>
        <p className={`text-base font-bold ${clr} mt-0.5`}>{label}</p>
        <div className="mt-3 h-2 bg-surface rounded-full">
          <div className="h-2 bg-accent rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex justify-center gap-5 mt-3 text-xs text-subtle">
          <span className="text-green-400">✅ {score} Correct</span>
          <span className="text-red-400">❌ {qs.length - score - skippedCount} Wrong</span>
          {skippedCount > 0 && <span className="text-amber-400">⏭ {skippedCount} Skipped</span>}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 mb-4">
        <button onClick={() => setStage('setup')}
          className="flex-1 btn-primary flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4" /> New Quiz
        </button>
        <button onClick={downloadResults}
          className="flex items-center gap-2 px-4 py-2.5 border border-border rounded-xl text-xs font-bold text-muted hover:bg-hover hover:text-primary transition-all">
          <Download className="w-4 h-4" /> Download Results
        </button>
      </div>

      {/* Detailed review */}
      <p className="text-xs font-bold text-muted mb-3 uppercase tracking-wider">📋 Review All Answers</p>
      <div className="space-y-3">
        {qs.map((q, i) => {
          const isSkipped = skipped.has(q.id)
          let ua = q.type === 'msq' ? [...(multiAns[q.id] ?? [])].join(', ') : singleAns[q.id] || ''
          let correct = false
          if (!isSkipped) {
            if (q.type === 'msq') {
              const us = new Set(multiAns[q.id] ?? [])
              const cs = new Set(Array.isArray(q.answer) ? q.answer : [q.answer])
              correct = us.size === cs.size && [...us].every(x => cs.has(x))
            } else {
              correct = ua.toLowerCase().trim() === (Array.isArray(q.answer) ? q.answer[0] : q.answer).toLowerCase().trim()
            }
          }
          const info = TYPE_INFO[q.type]
          return (
            <div key={q.id} className={`card border-2 ${isSkipped ? 'border-amber-500/30' : correct ? 'border-green-500/30' : 'border-red-500/30'}`}>
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {isSkipped ? <SkipForward className="w-4 h-4 text-amber-400" /> : correct ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-[10px] text-subtle">Q{i+1}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${info.color}`}>{info.icon} {info.label}</span>
                  </div>
                  <p className="text-sm font-semibold text-primary mb-2">{q.question}</p>
                  <div className="space-y-1 text-xs">
                    <p>Your answer: <span className={`font-bold ${isSkipped ? 'text-amber-400' : correct ? 'text-green-400' : 'text-red-400'}`}>{isSkipped ? 'Skipped' : ua || '—'}</span></p>
                    {!correct && !isSkipped && <p>Correct: <span className="font-bold text-green-400">{Array.isArray(q.answer) ? q.answer.join(', ') : q.answer}</span></p>}
                    <p className="text-subtle italic bg-hover/50 p-2 rounded-lg mt-1">{q.explanation}</p>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
