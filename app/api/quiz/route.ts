import { NextRequest, NextResponse } from 'next/server'
import { ollamaCall } from '@/lib/ollama'
import { docStore } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const { topic, count = 5, difficulty = 'medium', types = ['mcq','msq','short','fillblank'] } = await req.json()
    const docs = docStore.getAll()
    const hasDoc = docs.length > 0
    const context = docStore.getContext().substring(0, 12000)
    const names = docStore.getNames()

    if (!hasDoc && !topic) return NextResponse.json({ error: 'Upload a document or enter a topic.' }, { status: 400 })

    const sourceRule = topic.trim()
      ? `Generate questions SPECIFICALLY about the topic: "${topic}"\n${hasDoc ? `Use this document content as reference:\n${context}` : 'Use your knowledge to create questions.'}`
      : hasDoc
        ? `You MUST generate questions STRICTLY from this document content ONLY. Do NOT use any outside knowledge:\n\n${context}`
        : ''

    const prompt = `You are a quiz generator.
${sourceRule}

IMPORTANT: Generate questions ONLY about the specified topic.
Generate exactly ${count} questions at ${difficulty} difficulty.
Mix these question types: ${types.join(', ')}

Return ONLY a valid JSON array — no markdown, no backticks, no explanation.
Start with [ and end with ].

Type formats:

MCQ (Single correct):
{"id":1,"type":"mcq","question":"Question?","options":["A. opt1","B. opt2","C. opt3","D. opt4"],"answer":"A. opt1","explanation":"Why."}

MSQ (Multiple correct — 2 or more correct answers):
{"id":2,"type":"msq","question":"Which of these are correct? (Select all that apply)","options":["A. opt1","B. opt2","C. opt3","D. opt4"],"answer":["A. opt1","C. opt3"],"explanation":"Why A and C."}

Short Answer:
{"id":3,"type":"short","question":"Question?","options":[],"answer":"Expected answer","explanation":"Explanation."}

Fill in the Blank:
{"id":4,"type":"fillblank","question":"___ is the process of training a model on labeled data.","options":[],"answer":"Supervised learning","explanation":"Because labeled data defines the correct output."}

CRITICAL RULES:
- mcq: exactly 4 options, answer is a single string
- msq: exactly 4 options, answer is a JSON ARRAY of correct option strings
- short: options is empty array [], answer is a string
- fillblank: options is empty array [], question MUST contain ___ placeholder, answer is what fills the blank`

    const raw = await ollamaCall([
      { role: 'system', content: 'Output only valid JSON arrays. No other text.' },
      { role: 'user', content: prompt },
    ])

    let questions: any[] = []
    try {
      const match = raw.match(/\[[\s\S]*\]/)
      if (match) {
        const parsed = JSON.parse(match[0])
        questions = parsed
          .filter((q: any) => q && q.question && q.answer !== undefined)
          .map((q: any, idx: number) => {
            const type = ['mcq','msq','short','fillblank'].includes(q.type) ? q.type : 'mcq'
            return {
              id: q.id ?? idx + 1,
              type,
              question: String(q.question),
              options: Array.isArray(q.options) ? q.options : [],
              answer: type === 'msq' ? (Array.isArray(q.answer) ? q.answer : [String(q.answer)]) : String(q.answer),
              explanation: String(q.explanation || 'No explanation provided.'),
            }
          })
      }
    } catch { questions = [] }

    if (!questions.length) return NextResponse.json({ error: 'Quiz generation failed. Please try again.' }, { status: 500 })
    return NextResponse.json({ 
      questions, 
      source: topic.trim() ? topic : (hasDoc ? names : 'Unknown') 
    })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
