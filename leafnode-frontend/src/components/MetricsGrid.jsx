const METRICS = [
  {
    key: 'temperature',
    label: 'Temperature',
    unit: '°C',
    emoji: '🌡️',
    profileMin: 'temperature_min',
    profileMax: 'temperature_max',
    healthStatus: 'bme_ok',
    ring: 'ring-orange-400/40',
    text: 'text-orange-500 dark:text-orange-400',
    bg: 'bg-orange-50 dark:bg-orange-500/10',
  },
  {
    key: 'humidity',
    label: 'Humidity',
    unit: '%',
    emoji: '💧',
    profileMin: 'humidity_min',
    profileMax: 'humidity_max',
    healthStatus: 'bme_ok',
    ring: 'ring-blue-400/40',
    text: 'text-blue-500 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-500/10',
  },
  {
    key: 'pressure',
    label: 'Pressure',
    unit: ' hPa',
    emoji: '🌬️',
    profileMin: 'pressure_min',
    profileMax: 'pressure_max',
    healthStatus: 'bme_ok',
    ring: 'ring-purple-400/40',
    text: 'text-purple-500 dark:text-purple-400',
    bg: 'bg-purple-50 dark:bg-purple-500/10',
  },
  {
    key: 'light',
    label: 'Light',
    unit: ' lux',
    emoji: '☀️',
    profileMin: 'light_min',
    profileMax: 'light_max',
    healthStatus: 'ldr_ok',
    ring: 'ring-yellow-400/40',
    text: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-500/10',
  },
  {
    key: 'soil_moisture',
    label: 'Soil Moisture',
    unit: '%',
    emoji: '🌱',
    profileMin: 'soil_moisture_min',
    profileMax: 'soil_moisture_max',
    healthStatus: 'soil_ok',
    ring: 'ring-emerald-400/40',
    text: 'text-emerald-500 dark:text-emerald-400',
    bg: 'bg-emerald-50 dark:bg-emerald-500/10',
  },
]

function statusFor(value, min, max) {
  if (min == null || max == null) return 'unknown'
  if (value < min || value > max) return 'anomaly'
  return 'ok'
}

export default function MetricsGrid({ reading, plant }) {
  if (!reading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {METRICS.map((m) => (
          <div key={m.key} className={`card p-5 flex flex-col gap-2 ${m.bg}`}>
            <span className="text-2xl">{m.emoji}</span>
            <p className="text-xs text-gray-400 uppercase tracking-widest">{m.label}</p>
            <p className="text-3xl font-bold text-gray-300 dark:text-gray-600">—</p>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
      {METRICS.map((m) => {
        const value = reading[m.key]
        const min = plant?.[m.profileMin]
        const max = plant?.[m.profileMax]
        
        let status = 'ok'
        if (m.healthStatus && reading[m.healthStatus] === false) {
          status = 'fault'
        } else if (min != null && max != null && (value < min || value > max)) {
          status = 'anomaly'
        }

        const ringClass =
          status === 'fault'
            ? 'ring-2 ring-red-500/80 animate-pulse'
            : status === 'anomaly'
            ? 'ring-2 ring-orange-400/50'
            : `ring-1 ${m.ring}`

        return (
          <div key={m.key} className={`card p-5 flex flex-col gap-2 ${m.bg} ${ringClass}`}>
            <div className="flex items-center justify-between">
              <span className="text-2xl">{m.emoji}</span>
              {status === 'fault' && (
                <span className="badge bg-red-100 text-red-600 border border-red-300 dark:bg-red-900/60 dark:text-red-300 dark:border-red-700">
                  ✗ FAULT
                </span>
              )}
              {status === 'anomaly' && (
                <span className="badge bg-orange-100 text-orange-600 border border-orange-300 dark:bg-orange-900/60 dark:text-orange-300 dark:border-orange-700">
                  ⚠ Alert
                </span>
              )}
              {status === 'ok' && (
                <span className="badge bg-leaf-100 text-leaf-700 border border-leaf-300 dark:bg-leaf-900/60 dark:text-leaf-300 dark:border-leaf-700">
                  ✓ OK
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-widest">{m.label}</p>
            <p className={`text-3xl font-bold ${m.text}`}>
              {status === 'fault' ? 'ERR' : typeof value === 'number' ? value.toFixed(1) : '—'}
              {status !== 'fault' && <span className="text-base font-normal text-gray-400 ml-1">{m.unit}</span>}
            </p>
            {min != null && max != null && (
              <p className="text-xs text-gray-400 dark:text-gray-500">
                Range: {min}{m.unit} – {max}{m.unit}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
