'use client'
import { useState, useRef, useEffect } from 'react'
import { Send, Square, Plus, Trash2, Clock, MessageSquare, Copy, Check } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Msg { id: string; role: 'user' | 'assistant'; content: string; ts: string }
interface Session { id: string; title: string; messages: Msg[]; createdAt: string }

const STORE = 'la_sessions'
const ACTIVE = 'la_active'

function loadSessions(): Session[] {
  try { return JSON.parse(localStorage.getItem(STORE) || '[]') } catch { return [] }
}
function saveSessions(s: Session[]) {
  try { localStorage.setItem(STORE, JSON.stringify(s)) } catch {}
}

export default function ChatPanel({ docCount }: { docCount: number }) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeId, setActiveId] = useState<string>('')
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textRef = useRef<HTMLTextAreaElement>(null)

  // Load from localStorage on mount
  useEffect(() => {
    const s = loadSessions()
    setSessions(s)
    const aid = localStorage.getItem(ACTIVE) || ''
    if (s.find(x => x.id === aid)) setActiveId(aid)
    else if (s.length) { setActiveId(s[0].id); localStorage.setItem(ACTIVE, s[0].id) }
  }, [])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) })

  const active = sessions.find(s => s.id === activeId)

  const newSession = () => {
    const s: Session = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
    const updated = [s, ...sessions]
    setSessions(updated)
    saveSessions(updated)
    setActiveId(s.id)
    localStorage.setItem(ACTIVE, s.id)
  }

  const deleteSession = (id: string) => {
    const updated = sessions.filter(s => s.id !== id)
    setSessions(updated)
    saveSessions(updated)
    if (activeId === id) {
      const next = updated[0]?.id || ''
      setActiveId(next)
      localStorage.setItem(ACTIVE, next)
    }
  }

  const updateSession = (id: string, msgs: Msg[]) => {
    setSessions(prev => {
      const updated = prev.map(s => {
        if (s.id !== id) return s
        const title = msgs[0]?.content.substring(0, 35) || 'New Chat'
        return { ...s, messages: msgs, title }
      })
      saveSessions(updated)
      return updated
    })
  }

  const send = async (text: string) => {
    if (!text.trim() || streaming) return

    let sid = activeId
    // Auto-create session if none
    if (!sid) {
      const s: Session = {
        id: Date.now().toString(),
        title: text.substring(0, 35),
        messages: [],
        createdAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setSessions(prev => { const u = [s, ...prev]; saveSessions(u); return u })
      sid = s.id
      setActiveId(sid)
      localStorage.setItem(ACTIVE, sid)
    }

    const userMsg: Msg = {
      id: Date.now().toString(),
      role: 'user',
      content: text.trim(),
      ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    const currentMsgs = sessions.find(s => s.id === sid)?.messages ?? []
    const withUser = [...currentMsgs, userMsg]
    updateSession(sid, withUser)
    setInput('')
    setStreaming(true)

    const aiId = (Date.now() + 1).toString()
    const aiMsg: Msg = { id: aiId, role: 'assistant', content: '', ts: '' }
    const withAi = [...withUser, aiMsg]
    updateSession(sid, withAi)

    try {
      abortRef.current = new AbortController()
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: abortRef.current.signal,
        body: JSON.stringify({ messages: withUser.map(m => ({ role: m.role, content: m.content })) }),
      })

      if (!res.ok || !res.body) throw new Error(await res.text())

      const reader = res.body.getReader()
      const dec = new TextDecoder()
      let full = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        full += dec.decode(value, { stream: true })
        setSessions(prev => {
          const u = prev.map(s => {
            if (s.id !== sid) return s
            return { ...s, messages: s.messages.map(m => m.id === aiId ? { ...m, content: full, ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) } : m) }
          })
          saveSessions(u)
          return u
        })
      }
    } catch (e: any) {
      if (e.name === 'AbortError') return
      setSessions(prev => {
        const u = prev.map(s => {
          if (s.id !== sid) return s
          return { ...s, messages: s.messages.map(m => m.id === aiId ? { ...m, content: `❌ ${e.message}`, ts: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) } : m) }
        })
        saveSessions(u)
        return u
      })
    } finally {
      setStreaming(false)
      textRef.current?.focus()
    }
  }

  const copyText = async (id: string, text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 1500)
  }

  return (
    <div className="flex h-full">
      {/* Sessions sidebar */}
      <div className="w-48 bg-input border-r border-border flex flex-col">
        <div className="p-3 border-b border-border">
          <button onClick={newSession}
            className="w-full flex items-center justify-center gap-2 py-2 bg-accent hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors">
            <Plus className="w-3.5 h-3.5" /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessions.length === 0 && (
            <p className="text-xs text-subtle text-center mt-4 px-2">No chats yet.<br/>Click New Chat</p>
          )}
          {sessions.map(s => (
            <div key={s.id} onClick={() => { setActiveId(s.id); localStorage.setItem(ACTIVE, s.id) }}
              className={`w-full text-left p-2 rounded-lg group transition-all cursor-pointer ${
                s.id === activeId ? 'bg-accent/20 border border-accent/30' : 'hover:bg-hover'
              }`}>
              <div className="flex items-start justify-between gap-1">
                <p className="text-xs font-medium text-primary truncate flex-1">{s.title}</p>
                <button onClick={e => { e.stopPropagation(); deleteSession(s.id) }}
                  className="opacity-0 group-hover:opacity-100 text-subtle hover:text-red-400">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
              <div className="flex items-center gap-1 mt-0.5">
                <Clock className="w-2.5 h-2.5 text-subtle" />
                <p className="text-xs text-subtle">{s.createdAt}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-5 py-3 border-b border-border bg-sidebar flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold text-primary">Document Q&A</span>
            {docCount > 0 && (
              <span className="text-xs bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-0.5 rounded-full">
                {docCount} doc{docCount > 1 ? 's' : ''} loaded
              </span>
            )}
          </div>
          <span className="text-xs text-subtle">RAG • Retrieves from YOUR documents only</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {!active || active.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center fade-up">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent to-cyan-400 flex items-center justify-center mb-4 shadow-xl">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-lg font-bold text-primary mb-2">Ask about your documents</h3>
              <p className="text-sm text-muted max-w-xs">
                {docCount > 0
                  ? `${docCount} document(s) loaded. Ask me anything from them!`
                  : 'Upload documents from the left panel, then ask questions.'}
              </p>
              {docCount > 0 && (
                <div className="mt-5 grid grid-cols-1 gap-2 w-full max-w-sm">
                  {['Summarize all key concepts', 'What are the main topics?', 'List important definitions', 'Explain the most complex topic'].map(s => (
                    <button key={s} onClick={() => send(s)}
                      className="text-sm text-left px-4 py-2.5 bg-surface hover:bg-hover border border-border rounded-xl text-primary transition-all">
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            active.messages.map(msg => (
              <div key={msg.id} className={`flex gap-3 fade-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  msg.role === 'user' ? 'bg-accent text-white' : 'bg-hover text-accent'
                }`}>
                  {msg.role === 'user' ? 'U' : 'AI'}
                </div>
                <div className={`max-w-[78%] group ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                  <div className={`px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-accent text-white rounded-tr-sm'
                      : 'bg-surface border border-border/50 rounded-tl-sm text-primary'
                  }`}>
                    {msg.role === 'user' ? (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    ) : msg.content === '' ? (
                      <div className="flex gap-1 items-center h-5 px-1">
                        <span className="w-2 h-2 rounded-full bg-slate-400 dot1 inline-block" />
                        <span className="w-2 h-2 rounded-full bg-slate-400 dot2 inline-block" />
                        <span className="w-2 h-2 rounded-full bg-slate-400 dot3 inline-block" />
                      </div>
                    ) : (
                      <div className="md text-sm"><ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown></div>
                    )}
                  </div>
                  <div className={`flex items-center gap-2 mt-1 px-1 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    {msg.ts && <span className="text-xs text-subtle">{msg.ts}</span>}
                    {msg.role === 'assistant' && msg.content && (
                      <button onClick={() => copyText(msg.id, msg.content)}
                        className="opacity-0 group-hover:opacity-100 text-subtle hover:text-primary transition-all">
                        {copied === msg.id ? <Check className="w-3 h-3 text-green-400" /> : <Copy className="w-3 h-3" />}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-5 py-4 bg-sidebar border-t border-border">
          <div className="flex gap-2 items-end bg-input border border-border rounded-2xl px-4 py-3 focus-within:border-accent/50 transition-colors">
            <textarea ref={textRef} value={input}
              onChange={e => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px' }}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}
              placeholder="Ask about your documents… (Enter to send)"
              rows={1} style={{ resize: 'none', minHeight: '24px' }}
              className="flex-1 bg-transparent text-sm text-primary placeholder:text-subtle outline-none" />
            {streaming ? (
              <button onClick={() => abortRef.current?.abort()}
                className="w-8 h-8 rounded-xl bg-red-600 flex items-center justify-center flex-shrink-0 hover:bg-red-700">
                <Square className="w-3.5 h-3.5 text-white" />
              </button>
            ) : (
              <button onClick={() => send(input)} disabled={!input.trim()}
                className="w-8 h-8 rounded-xl bg-accent flex items-center justify-center flex-shrink-0 hover:bg-blue-700 disabled:opacity-30 transition-all">
                <Send className="w-3.5 h-3.5 text-white" />
              </button>
            )}
          </div>
          <p className="text-xs text-center text-muted mt-2">👨‍💻 Developed by Sathwik Goundla</p>
        </div>
      </div>
    </div>
  )
}
