import { NextRequest, NextResponse } from 'next/server'
import { ollamaCall } from '@/lib/ollama'
import { docStore } from '@/lib/store'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const { topic, duration, level, goal } = await req.json()
    const context = docStore.getContext().substring(0, 8000)
    const names = docStore.getNames()

    const prompt = `Create a structured study plan.
Topic: ${topic}
Duration: ${duration}
Level: ${level}
Goal: ${goal}
${names ? `Based on uploaded documents: ${names}\n\n${context}` : ''}

Write a clear study plan with:
# Study Plan: ${topic}
## Overview
## Daily/Weekly Schedule
## Key Topics to Cover
## Study Tips
## Success Criteria

Be specific and practical.`

    const plan = await ollamaCall([
      { role: 'system', content: 'You are an expert study planner. Create clear, actionable study plans in markdown format.' },
      { role: 'user', content: prompt },
    ])

    return NextResponse.json({ plan })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
