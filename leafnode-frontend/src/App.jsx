import { useState, useEffect, useCallback } from 'react'
import * as api from './api'
import PlantPanel from './components/PlantPanel'
import PlantSelectorModal from './components/PlantSelectorModal'
import MetricsGrid from './components/MetricsGrid'
import ReadingsChart from './components/ReadingsChart'
import AnomalyFeed from './components/AnomalyFeed'

const REFRESH_MS = 30_000

function useTheme() {
  const [isDark, setIsDark] = useState(() => {
    const stored = localStorage.getItem('leafnode-theme')
    if (stored) return stored === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
      localStorage.setItem('leafnode-theme', 'dark')
    } else {
      root.classList.remove('dark')
      localStorage.setItem('leafnode-theme', 'light')
    }
  }, [isDark])

  return [isDark, () => setIsDark((d) => !d)]
}

export default function App() {
  const [isDark, toggleTheme] = useTheme()
  const [deviceInput, setDeviceInput] = useState('')
  const [activeDevice, setActiveDevice] = useState('')
  const [plant, setPlant] = useState(null)
  const [latestReading, setLatestReading] = useState(null)
  const [readings, setReadings] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const fetchAll = useCallback(async (device) => {
    if (!device) return
    setLoading(true)
    const [p, lr, rs, an] = await Promise.allSettled([
      api.getPlant(device),
      api.getLatestReading(device),
      api.getReadings(device, 50),
      api.getAnomalies(device, 30),
    ])
    setPlant(p.status === 'fulfilled' ? p.value : null)
    setLatestReading(lr.status === 'fulfilled' ? lr.value : null)
    setReadings(rs.status === 'fulfilled' ? rs.value : [])
    setAnomalies(an.status === 'fulfilled' ? an.value : [])
    setLastUpdated(new Date())
    setLoading(false)
  }, [])

  useEffect(() => {
    if (!activeDevice) return
    fetchAll(activeDevice)
    const id = setInterval(() => fetchAll(activeDevice), REFRESH_MS)
    return () => clearInterval(id)
  }, [activeDevice, fetchAll])

  function handleConnect(e) {
    e.preventDefault()
    const d = deviceInput.trim()
    if (!d) return
    setActiveDevice(d)
  }

  async function handleRegisterPlant(plantName) {
    await api.createPlant(plantName, activeDevice)
    setShowModal(false)
    await fetchAll(activeDevice)
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-40 dark:border-gray-800 dark:bg-gray-900/80">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2 shrink-0">
            <span className="text-2xl">🌿</span>
            <span className="text-lg font-bold tracking-tight text-gray-900 dark:text-gray-100">
              Leaf<span className="text-leaf-600 dark:text-leaf-400">Node</span>
            </span>
          </div>

          {/* Device selector */}
          <form onSubmit={handleConnect} className="flex items-center gap-2 flex-1 max-w-sm ml-auto sm:ml-0">
            <input
              type="text"
              placeholder="Device ID (e.g. leafnode-01)"
              value={deviceInput}
              onChange={(e) => setDeviceInput(e.target.value)}
              className="flex-1 bg-gray-100 border border-gray-300 rounded-lg px-3 py-1.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-leaf-500 transition-colors dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
            />
            <button type="submit" className="btn-primary py-1.5 text-sm shrink-0">
              Connect
            </button>
          </form>

          {/* Status + controls */}
          <div className="flex items-center gap-3 ml-auto">
            {activeDevice && (
              <div className="hidden sm:flex items-center gap-3">
                <div className="flex items-center gap-1.5 text-xs">
                  <span className={`w-1.5 h-1.5 rounded-full ${loading ? 'bg-yellow-400 animate-pulse' : 'bg-leaf-500'}`} />
                  <span className="font-mono text-gray-500 dark:text-gray-400">{activeDevice}</span>
                </div>
                {lastUpdated && (
                  <span className="text-xs text-gray-400 dark:text-gray-600">
                    {lastUpdated.toLocaleTimeString()}
                  </span>
                )}
                <button
                  onClick={() => fetchAll(activeDevice)}
                  disabled={loading}
                  className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors disabled:opacity-40"
                  title="Refresh"
                >
                  <RefreshIcon className={loading ? 'animate-spin' : ''} />
                </button>
              </div>
            )}

            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="w-9 h-9 flex items-center justify-center rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-600 transition-colors dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-300"
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {isDark ? <SunIcon /> : <MoonIcon />}
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        {!activeDevice ? (
          <EmptyState />
        ) : (
          <div className="space-y-5">
            <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-5">
              <PlantPanel plant={plant} onRegister={() => setShowModal(true)} />
              <MetricsGrid reading={latestReading} plant={plant} />
            </div>
            <ReadingsChart readings={readings} plant={plant} isDark={isDark} />
            <AnomalyFeed anomalies={anomalies} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-4 text-center text-xs text-gray-400 dark:border-gray-800 dark:text-gray-600">
        LeafNode — plant monitoring · auto-refreshes every {REFRESH_MS / 1000}s
      </footer>

      {showModal && (
        <PlantSelectorModal
          deviceId={activeDevice}
          onClose={() => setShowModal(false)}
          onSuccess={handleRegisterPlant}
        />
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-32 text-center">
      <span className="text-7xl">🌱</span>
      <div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-2">Welcome to LeafNode</h1>
        <p className="text-gray-500 max-w-sm">
          Enter a device ID above to start monitoring your plant's environment in real time.
        </p>
      </div>
    </div>
  )
}

function RefreshIcon({ className = '' }) {
  return (
    <svg className={`w-4 h-4 ${className}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  )
}

function SunIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <circle cx="12" cy="12" r="5" />
      <path strokeLinecap="round" d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" />
    </svg>
  )
}
