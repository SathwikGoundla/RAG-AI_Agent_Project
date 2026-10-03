import { NextRequest } from 'next/server'
import { docStore } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
const MODEL = process.env.GROQ_MODEL || 'openai/gpt-oss-120b'

// SERVER-SIDE keyword scoring — finds the most relevant doc
// We NEVER let the AI decide which file to cite
function findRelevantDocs(query: string) {
  const docs = docStore.getAll()
  if (!docs.length) return []

  const stopWords = new Set([
    'the','and','for','are','was','what','how','why','can','you','give',
    'tell','list','show','find','about','from','this','that','with','have',
    'will','does','did','its','into','also','just','more','explain','define',
    'describe','is','in','of','a','an','to','me','my','our','i'
  ])

  const keywords = query
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2 && !stopWords.has(w))

  if (!keywords.length) return docs

  const scored = docs.map(d => {
    const lc = d.content.toLowerCase()
    // Score: exact keyword hits + bonus for filename match
    let score = keywords.reduce((acc, kw) => {
      const hits = (lc.match(new RegExp(kw, 'g')) || []).length
      return acc + Math.min(hits, 5) // cap at 5 per keyword to avoid bias
    }, 0)
    // Bonus if filename matches the query
    const fileNameLc = d.name.toLowerCase()
    keywords.forEach(kw => { if (fileNameLc.includes(kw)) score += 10 })
    return { ...d, score }
  })

  scored.sort((a, b) => b.score - a.score)
  const relevant = scored.filter(d => d.score > 0)
  return relevant.length > 0 ? relevant : docs
}

function stripAISources(text: string): string {
  return text
    .replace(/\n*📄\s*[Ss]ource:.*$/gm, '')
    .replace(/\n*\[?[Ss]ource:.*?\]?(\n|$)/gm, '')
    .trimEnd()
}

export async function POST(req: NextRequest) {
  const apiKey = process.env.GROQ_API_KEY || ''
  const enc = new TextEncoder()

  const respond = (text: string) => new Response(
    new ReadableStream({ start(ctrl) { ctrl.enqueue(enc.encode(text)); ctrl.close() } }),
    { headers: { 'Content-Type': 'text/plain; charset=utf-8' } }
  )

  try {
    const { messages } = await req.json()
    const docs = docStore.getAll()

    if (!docs.length) return respond('⚠️ No documents uploaded yet. Please upload your study files from the left panel first!')
    if (!apiKey) return respond('❌ GROQ_API_KEY not set in .env.local — get free key at https://console.groq.com')

    const lastUserMsg = [...messages].reverse().find((m: any) => m.role === 'user')?.content || ''
    const relevantDocs = findRelevantDocs(lastUserMsg)
    const primarySource = relevantDocs[0].name  // 100% server-determined, never AI-guessed

    const topDocs = relevantDocs.slice(0, 3)
    const chunkSize = Math.floor(14000 / topDocs.length)
    const contextChunks = topDocs
      .map(d => `[FILE: "${d.name}"]\n${d.content.substring(0, chunkSize)}`)
      .join('\n\n---\n\n')

    const system = `You are LearnAgent — a strict document-only Q&A assistant.

DOCUMENT CONTENT BELOW IS YOUR ONLY SOURCE OF TRUTH:
${contextChunks}
END OF DOCUMENTS

ABSOLUTE RULES — NEVER BREAK THESE:
1. You MUST answer ONLY from the document content provided above.
2. You CANNOT use any of your pretrained / general knowledge under ANY circumstances.
3. If someone asks about something NOT in the documents above, you MUST say: NOT_FOUND
4. Do NOT write "Source:" — the system adds citations automatically.
5. Do NOT mention file names in your answer text.
6. Answer in clear bullet points using ONLY facts found in the text above.
7. Even if you know the answer from training, if it's not in the documents, say: NOT_FOUND`

    const recentMessages = messages.slice(-4).map((m: any) => ({
      role: m.role,
      content: m.role === 'assistant' ? stripAISources(m.content) : m.content
    }))

    const groqRes = await fetch(GROQ_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'system', content: system }, ...recentMessages],
        temperature: 0.0,   // zero temperature = no creativity, strict retrieval
        max_tokens: 1024,
        stream: true,
      }),
    })

    if (!groqRes.ok || !groqRes.body) throw new Error(`Groq ${groqRes.status}: ${await groqRes.text()}`)

    const stream = new ReadableStream({
      async start(ctrl) {
        const reader = groqRes.body!.getReader()
        const dec = new TextDecoder()
        let fullText = ''
        let closed = false

        const finish = () => {
          if (closed) return
          closed = true
          const notFound = /NOT_FOUND|not found in|not available in|not in the document|not covered|not mentioned/i.test(fullText)
          if (notFound) {
            ctrl.enqueue(enc.encode('\n\n⚠️ This topic is not found in your uploaded documents. Please upload a relevant document.'))
          } else {
            // Server-side citation — always accurate
            ctrl.enqueue(enc.encode(`\n\n📄 Source: ${primarySource}`))
          }
          ctrl.close()
        }

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            for (const line of dec.decode(value, { stream: true }).split('\n')) {
              const trimmed = line.trim()
              if (!trimmed.startsWith('data:')) continue
              const jsonStr = trimmed.slice(5).trim()
              if (jsonStr === '[DONE]') { finish(); return }
              try {
                const j = JSON.parse(jsonStr)
                const token = j.choices?.[0]?.delta?.content
                if (token) { fullText += token; ctrl.enqueue(enc.encode(token)) }
                if (j.choices?.[0]?.finish_reason === 'stop') { finish(); return }
              } catch {}
            }
          }
          finish()
        } catch (e) { if (!closed) { closed = true; ctrl.error(e) } }
      }
    })

    return new Response(stream, {
      headers: { 'Content-Type': 'text/plain; charset=utf-8', 'X-Accel-Buffering': 'no', 'Cache-Control': 'no-cache' },
    })
  } catch (e: any) {
    return respond(`❌ Error: ${e.message}`)
  }
}
