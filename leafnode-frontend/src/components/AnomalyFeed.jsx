const METRIC_META = {
  temperature: { label: 'Temperature', unit: '°C',   color: 'text-orange-500 dark:text-orange-400' },
  humidity:    { label: 'Humidity',    unit: '%',    color: 'text-blue-500 dark:text-blue-400' },
  pressure:    { label: 'Pressure',   unit: ' hPa', color: 'text-purple-500 dark:text-purple-400' },
  light:       { label: 'Light',      unit: ' lux', color: 'text-yellow-600 dark:text-yellow-400' },
}

function AnomalyCard({ anomaly }) {
  const meta = METRIC_META[anomaly.metric] ?? { label: anomaly.metric, unit: '', color: 'text-gray-600 dark:text-gray-300' }
  const isThreshold = anomaly.rule_type === 'threshold'

  return (
    <div className="card p-5 border-l-2 border-red-400 dark:border-red-500/60">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`badge ${
            isThreshold
              ? 'bg-red-100 text-red-600 border border-red-300 dark:bg-red-900/50 dark:text-red-300 dark:border-red-700'
              : 'bg-amber-100 text-amber-700 border border-amber-300 dark:bg-amber-900/50 dark:text-amber-300 dark:border-amber-700'
          }`}>
            {isThreshold ? '⚠ Threshold' : '📈 Trend'}
          </span>
          <span className={`font-semibold ${meta.color}`}>{meta.label}</span>
          <span className="text-gray-500 dark:text-gray-400 text-sm">
            {anomaly.value?.toFixed(2)}{meta.unit}
            {isThreshold && anomaly.expected_min != null && (
              <span className="text-gray-400 dark:text-gray-600 ml-1">
                (expected {anomaly.expected_min}–{anomaly.expected_max}{meta.unit})
              </span>
            )}
          </span>
        </div>
        <time className="text-xs text-gray-400 whitespace-nowrap">
          {new Date(anomaly.timestamp).toLocaleString()}
        </time>
      </div>

      {anomaly.explanation ? (
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{anomaly.explanation}</p>
      ) : (
        <p className="text-sm text-gray-400 italic">No explanation available</p>
      )}
    </div>
  )
}

export default function AnomalyFeed({ anomalies }) {
  return (
    <div className="card p-6">
      <div className="flex items-center gap-3 mb-5">
        <h3 className="font-semibold text-gray-800 dark:text-gray-200">Anomaly Feed</h3>
        {anomalies.length > 0 && (
          <span className="badge bg-red-100 text-red-600 border border-red-300 dark:bg-red-900/50 dark:text-red-300 dark:border-red-700">
            {anomalies.length}
          </span>
        )}
      </div>

      {anomalies.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-10 text-center">
          <span className="text-4xl">✅</span>
          <p className="text-gray-400 text-sm">No anomalies detected</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
          {anomalies.map((a) => (
            <AnomalyCard key={a.id} anomaly={a} />
          ))}
        </div>
      )}
    </div>
  )
}
