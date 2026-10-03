'use client'
import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import ChatPanel from '@/components/ChatPanel'
import QuizPanel from '@/components/QuizPanel'
import StudyPlanPanel from '@/components/StudyPlanPanel'

interface Doc { id: string; name: string; size: number }

export default function Home() {
  const [tab, setTab] = useState('chat')
  const [docs, setDocs] = useState<Doc[]>([])

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar tab={tab} setTab={setTab} onDocsChange={setDocs} />
      <main className="flex-1 overflow-hidden bg-base">
        {tab === 'chat'  && <ChatPanel  docCount={docs.length} />}
        {tab === 'quiz'  && <QuizPanel  docCount={docs.length} />}
        {tab === 'study' && <StudyPlanPanel docCount={docs.length} />}
      </main>
    </div>
  )
}
