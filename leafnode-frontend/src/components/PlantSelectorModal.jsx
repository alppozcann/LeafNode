import { useState } from 'react'

const PRESET_PLANTS = [
  { name: 'Monstera deliciosa', emoji: '🌿', description: 'Tropical, indirect light' },
  { name: 'Pothos',             emoji: '🍃', description: 'Hardy, thrives in low light' },
  { name: 'Snake Plant',        emoji: '🌱', description: 'Drought tolerant, air purifier' },
  { name: 'Peace Lily',         emoji: '🌸', description: 'Shade loving, high humidity' },
  { name: 'Spider Plant',       emoji: '🕸️',  description: 'Adaptable, fast growing' },
  { name: 'Fiddle Leaf Fig',    emoji: '🌲', description: 'Bright indirect light' },
  { name: 'ZZ Plant',           emoji: '💚', description: 'Extremely low maintenance' },
  { name: 'Rubber Plant',       emoji: '🌳', description: 'Bold leaves, moderate light' },
  { name: 'Aloe Vera',          emoji: '🌵', description: 'Succulent, full sun' },
]

export default function PlantSelectorModal({ deviceId, onClose, onSuccess }) {
  const [selected, setSelected] = useState('')
  const [custom, setCustom] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const plantName = custom.trim() || selected

  async function handleSubmit() {
    if (!plantName) return
    setLoading(true)
    setError(null)
    try {
      await onSuccess(plantName)
    } catch (e) {
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-800">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Register Plant</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Device: <span className="text-leaf-600 dark:text-leaf-400 font-mono">{deviceId}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl leading-none transition-colors"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Preset grid */}
          <div>
            <p className="text-sm text-gray-500 mb-3">Choose a common plant</p>
            <div className="grid grid-cols-3 gap-3">
              {PRESET_PLANTS.map((p) => {
                const isActive = selected === p.name && !custom
                return (
                  <button
                    key={p.name}
                    onClick={() => { setSelected(p.name); setCustom('') }}
                    className={`
                      flex flex-col items-center gap-1.5 p-4 rounded-xl border transition-all text-center
                      ${isActive
                        ? 'border-leaf-500 bg-leaf-50 dark:bg-leaf-500/10 shadow-[0_0_0_1px_rgba(34,197,94,0.3)]'
                        : 'border-gray-200 bg-gray-50 hover:border-gray-300 hover:bg-gray-100 dark:border-gray-800 dark:bg-gray-800/50 dark:hover:border-gray-700 dark:hover:bg-gray-800'}
                    `}
                  >
                    <span className="text-3xl">{p.emoji}</span>
                    <span className="text-sm font-medium text-gray-800 dark:text-gray-100 leading-tight">{p.name}</span>
                    <span className="text-xs text-gray-400 leading-tight">{p.description}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-gray-200 dark:bg-gray-800" />
            <span className="text-xs text-gray-400 uppercase tracking-widest">or enter custom name</span>
            <div className="flex-1 h-px bg-gray-200 dark:bg-gray-800" />
          </div>

          {/* Custom input */}
          <input
            type="text"
            placeholder="e.g. Calathea orbifolia, Orchid, Basil…"
            value={custom}
            onChange={(e) => { setCustom(e.target.value); setSelected('') }}
            className="w-full bg-gray-100 border border-gray-300 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-leaf-500 transition-colors dark:bg-gray-800 dark:border-gray-700 dark:text-gray-100 dark:placeholder-gray-500"
          />

          {/* Preview + error */}
          {plantName && (
            <p className="text-sm text-gray-500">
              Will register: <span className="text-leaf-600 dark:text-leaf-400 font-medium">{plantName}</span>
            </p>
          )}
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-2">
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <button onClick={onClose} className="btn-secondary">Cancel</button>
            <button
              onClick={handleSubmit}
              disabled={!plantName || loading}
              className="btn-primary min-w-[120px]"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <SpinnerIcon /> Generating…
                </span>
              ) : (
                'Register Plant'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function SpinnerIcon() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}
