import { useState } from 'react'

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(res.status === 429
          ? 'Too many login attempts. Try again in 15 minutes.'
          : (data.detail ?? 'Invalid credentials'))
        return
      }
      onLogin()
    } catch {
      setError('Connection error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950">
      <div className="w-full max-w-sm px-4">
        <div className="text-center mb-8">
          <span className="text-5xl">🌿</span>
          <h1 className="text-2xl font-bold mt-3 text-gray-900 dark:text-gray-100">
            Leaf<span className="text-leaf-600 dark:text-leaf-400">Node</span>
          </h1>
          <p className="text-sm text-gray-500 mt-1">Sign in to your dashboard</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white dark:bg-gray-900 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 p-6 space-y-4"
        >
          {error && (
            <div className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-leaf-500 transition-colors"
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:border-leaf-500 transition-colors"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-2 text-sm disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
