// ─────────────────────────────────────────────────────────────
// AI Client — Groq API (Free, 10x faster than local Ollama)
// Get free API key: https://console.groq.com
// ─────────────────────────────────────────────────────────────

const GROQ_API_KEY = process.env.GROQ_API_KEY || ''
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
const MODEL = process.env.GROQ_MODEL || 'openai/gpt-oss-120b'

export interface Msg { role: 'system' | 'user' | 'assistant'; content: string }

function headers() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${GROQ_API_KEY}`,
  }
}

/** Non-streaming call — for quiz & study plan */
export async function ollamaCall(messages: Msg[]): Promise<string> {
  if (!GROQ_API_KEY) throw new Error('❌ GROQ_API_KEY not set in .env.local — please add it!')

  const res = await fetch(GROQ_URL, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({
      model: MODEL,
      messages,
      temperature: 0.2,
      max_tokens: 2048,
      stream: false,
    }),
  })

  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Groq error ${res.status}: ${err}`)
  }

  const data = await res.json()
  return data.choices?.[0]?.message?.content ?? ''
}

/** Streaming call — for chat (returns raw fetch Response) */
export async function ollamaStream(messages: Msg[]): Promise<Response> {
  if (!GROQ_API_KEY) throw new Error('❌ GROQ_API_KEY not set in .env.local — please add it!')

  const res = await fetch(GROQ_URL, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({
      model: MODEL,
      messages,
      temperature: 0.1,
      max_tokens: 1024,
      stream: true,
    }),
  })

  if (!res.ok) throw new Error(`Groq error ${res.status}: ${await res.text()}`)
  return res
}

// Keep these exports for backward compat
export const OLLAMA_URL = GROQ_URL
export { MODEL }
