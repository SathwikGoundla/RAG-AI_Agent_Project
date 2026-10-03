import { NextRequest, NextResponse } from 'next/server'
import { docStore } from '@/lib/store'
import fs from 'fs'
import path from 'path'
import { v4 as uuid } from 'uuid'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function POST(req: NextRequest) {
  try {
    const form = await req.formData()
    const file = form.get('file') as File | null
    if (!file) return NextResponse.json({ error: 'No file' }, { status: 400 })
    if (file.size > 25 * 1024 * 1024)
      return NextResponse.json({ error: 'Max file size is 25MB' }, { status: 400 })

    const buf = Buffer.from(await file.arrayBuffer())
    const id = uuid()

    // Save actual file to uploaded_docs/ folder
    const uploadsDir = docStore.getUploadsDir()
    const safeFileName = `${id}_${file.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`
    const filePath = path.join(uploadsDir, safeFileName)
    fs.writeFileSync(filePath, buf)

    // Extract text content
    let content = ''
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      try {
        const pdf = await import('pdf-parse')
        const data = await pdf.default(buf)
        content = data.text || ''
      } catch { content = '[PDF parse failed — try a text-based PDF]' }
    } else if (file.type.startsWith('image/')) {
      content = `[Image file: ${file.name} — ${(file.size / 1024).toFixed(1)} KB]`
    } else {
      content = buf.toString('utf-8')
    }

    content = content.substring(0, 15000)

    docStore.add({
      id,
      name: file.name,
      content,
      size: file.size,
      uploadedAt: new Date().toISOString(),
      filePath,
    })

    return NextResponse.json({ ok: true, name: file.name, id, count: docStore.count() })
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}

export async function GET() {
  const docs = docStore.getAll().map(d => ({
    id: d.id,
    name: d.name,
    size: d.size,
    uploadedAt: d.uploadedAt,
  }))
  return NextResponse.json({ docs })
}

export async function DELETE(req: NextRequest) {
  const id = new URL(req.url).searchParams.get('id') ?? ''
  docStore.remove(id)
  return NextResponse.json({ ok: true, count: docStore.count() })
}
