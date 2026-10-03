'use client'

import { ThemeProvider } from '@/lib/ThemeContext'
import { ReactNode } from 'react'

export function ClientProvider({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>
}
