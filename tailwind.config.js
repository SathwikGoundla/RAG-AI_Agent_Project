/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        accent: 'var(--accent)',
        border: 'var(--border)',
        sidebar: 'var(--bg-sidebar)',
        surface: 'var(--bg-surface)',
        hover:   'var(--bg-hover)',
        base:    'var(--bg-base)',
        input:   'var(--bg-input)',
        primary: 'var(--text-primary)',
        muted:   'var(--text-muted)',
        subtle:  'var(--text-subtle)',
      },
    },
  },
  plugins: [],
}
