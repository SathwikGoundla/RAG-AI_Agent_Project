'use client'
import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

export default function ThemeToggle() {
  const [mounted, setMounted] = useState(false)
  const [theme, setThemeState] = useState<'light' | 'dark'>('dark')

  useEffect(() => {
    // Set mounted to true and initialize theme from DOM
    setMounted(true)
    const currentTheme = (document.documentElement.getAttribute('data-theme') as 'light' | 'dark') || 'dark'
    setThemeState(currentTheme)
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setThemeState(newTheme)
    
    // Update DOM and localStorage directly
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  if (!mounted) {
    return (
      <button
        disabled
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium opacity-50 cursor-not-allowed"
      >
        <Sun size={16} />
        <span>Loading...</span>
      </button>
    )
  }

  return (
    <button
      onClick={toggleTheme}
      className="w-full flex items-center gap-2 px-3 py-2 rounded-lg transition-colors
                 bg-hover hover:bg-surface border border-border text-primary text-sm font-medium"
      title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
    >
      {theme === 'dark' ? (
        <>
          <Sun size={16} />
          <span>Light Mode</span>
        </>
      ) : (
        <>
          <Moon size={16} />
          <span>Dark Mode</span>
        </>
      )}
    </button>
  )
}
