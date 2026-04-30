import { useState } from 'react'
import { resolveAnomaly } from '../api'

const METRIC_META = {
  temperature: { label: 'Temperature', unit: '°C', color: 'text-orange-500 dark:text-orange-400' },
  humidity: { label: 'Humidity', unit: '%', color: 'text-blue-500 dark:text-blue-400' },
  pressure: { label: 'Pressure', unit: ' hPa', color: 'text-purple-500 dark:text-purple-400' },
  light: { label: 'Light', unit: ' lux', color: 'text-yellow-600 dark:text-yellow-400' },
}

function AnomalyCard({ anomaly, onResolved }) {
  const meta = METRIC_META[anomaly.metric] ?? { label: anomaly.metric, unit: '', color: 'text-gray-600 dark:text-gray-300' }
  const isThreshold = anomaly.rule_type === 'threshold'
  const [resolving, setResolving] = useState(false)

  async function handleResolve() {
    setResolving(true)
    try {
      await resolveAnomaly(anomaly.id)
      onResolved(anomaly.id)
    } catch (e) {
      console.error(e)
      setResolving(false)
    }
  }

  return (
    <div className={`relative p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl shadow-sm border-l-4 ${
      isThreshold ? 'border-l-red-500 dark:border-l-red-500' : 'border-l-amber-500 dark:border-l-amber-500'
    } transition-all hover:shadow-md`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`badge ${isThreshold
              ? 'bg-red-50 text-red-600 border border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800/50'
              : 'bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50'
              }`}>
              {isThreshold ? '⚠ Threshold' : '📈 Trend'}
            </span>
            <span className={`font-medium ${meta.color}`}>{meta.label}</span>
          </div>
          <div className="text-gray-600 dark:text-gray-300 text-sm flex items-center gap-2">
            <span className="font-semibold text-gray-900 dark:text-white">
              {anomaly.value?.toFixed(2)}{meta.unit}
            </span>
            {isThreshold && anomaly.expected_min != null && (
              <span className="text-gray-400 dark:text-gray-500 text-xs">
                (expected {anomaly.expected_min}–{anomaly.expected_max}{meta.unit})
              </span>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <time className="text-xs text-gray-400 whitespace-nowrap">
            {new Date(anomaly.timestamp).toLocaleString(undefined, {
              month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            })}
          </time>
          <button
            onClick={handleResolve}
            disabled={resolving}
            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 shadow-sm transition-colors dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-200 dark:border-gray-700 disabled:opacity-50 whitespace-nowrap"
          >
            {resolving ? 'Resolving…' : 'Resolve'}
          </button>
        </div>
      </div>

      {anomaly.explanation && (
        <div className="mt-3 text-sm text-gray-600 dark:text-gray-300 leading-relaxed bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg border border-gray-100 dark:border-gray-800/50">
          <span className="font-medium text-gray-700 dark:text-gray-200 mb-1 block text-xs uppercase tracking-wider">AI Analysis</span>
          {anomaly.explanation}
        </div>
      )}
    </div>
  )
}

export default function AnomalyFeed({ anomalies: initialAnomalies }) {
  // Use local state to track resolved anomalies
  const [resolvedIds, setResolvedIds] = useState([])

  // Derived state: filter out resolved ones
  const activeAnomalies = initialAnomalies.filter(a => !resolvedIds.includes(a.id))

  function handleResolved(id) {
    setResolvedIds((prev) => [...prev, id])
  }

  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-5">
        <h3 className="font-semibold text-gray-800 dark:text-gray-200">Anomaly Feed</h3>
        {activeAnomalies.length > 0 && (
          <span className="badge bg-red-100 text-red-600 border border-red-300 dark:bg-red-900/50 dark:text-red-300 dark:border-red-700">
            {activeAnomalies.length}
          </span>
        )}
      </div>

      {activeAnomalies.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-10 text-center">
          <span className="text-4xl">✅</span>
          <p className="text-gray-400 text-sm">No anomalies detected</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {activeAnomalies.map((a) => (
            <AnomalyCard key={a.id} anomaly={a} onResolved={handleResolved} />
          ))}
        </div>
      )}
    </div>
  )
}
