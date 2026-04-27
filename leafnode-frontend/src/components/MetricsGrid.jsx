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
    unit: ' lux*',
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

function BatteryIcon({ pct }) {
  const fill = pct == null ? 0 : Math.max(0, Math.min(100, pct))
  return (
    <svg viewBox="0 0 24 12" className="w-8 h-4" fill="none">
      <rect x="0.5" y="0.5" width="20" height="11" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <rect x="20.5" y="3.5" width="3" height="5" rx="1" fill="currentColor" opacity="0.6" />
      <rect x="1.5" y="1.5" width={Math.round(fill * 0.18)} height="9" rx="1.5" fill="currentColor" />
    </svg>
  )
}

function batteryColor(pct) {
  if (pct == null) return { text: 'text-gray-400', bg: 'bg-gray-50 dark:bg-gray-500/10', ring: 'ring-1 ring-gray-300/40' }
  if (pct >= 50) return { text: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-500/10', ring: 'ring-1 ring-green-400/40' }
  if (pct >= 20) return { text: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-500/10', ring: 'ring-1 ring-yellow-400/40' }
  return { text: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-500/10', ring: 'ring-2 ring-red-500/80 animate-pulse' }
}

export default function MetricsGrid({ reading, plant }) {
  if (!reading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {METRICS.map((m) => (
          <div key={m.key} className={`card p-5 flex flex-col gap-2 ${m.bg}`}>
            <span className="text-2xl">{m.emoji}</span>
            <p className="text-xs text-gray-400 uppercase tracking-widest">{m.label}</p>
            <p className="text-3xl font-bold text-gray-300 dark:text-gray-600">—</p>
          </div>
        ))}
        <div className="card p-5 flex flex-col gap-2 bg-gray-50 dark:bg-gray-500/10">
          <span className="text-2xl">🔋</span>
          <p className="text-xs text-gray-400 uppercase tracking-widest">Battery</p>
          <p className="text-3xl font-bold text-gray-300 dark:text-gray-600">—</p>
        </div>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {METRICS.map((m) => {
        let value = reading[m.key]
        if (m.key === 'light' && value > 1000) value = 1000

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
          <div 
            key={m.key} 
            className={`card p-5 flex flex-col gap-2 ${m.bg} ${ringClass}`}
            title={m.key === 'light' ? "* Relative light index (0–1000). Not calibrated lux." : undefined}
          >
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
      {/* Battery card */}
      {(() => {
        const pct = reading.battery_pct
        const volt = reading.battery_voltage
        const { text, bg, ring } = batteryColor(pct)
        return (
          <div className={`card p-5 flex flex-col gap-2 ${bg} ${ring}`}>
            <div className="flex items-center justify-between">
              <span className={`${text}`}><BatteryIcon pct={pct} /></span>
              {pct != null && pct < 20 && (
                <span className="badge bg-red-100 text-red-600 border border-red-300 dark:bg-red-900/60 dark:text-red-300 dark:border-red-700">
                  ⚠ Low
                </span>
              )}
              {pct != null && pct >= 20 && pct < 50 && (
                <span className="badge bg-yellow-100 text-yellow-700 border border-yellow-300 dark:bg-yellow-900/60 dark:text-yellow-300 dark:border-yellow-700">
                  ✓ OK
                </span>
              )}
              {pct != null && pct >= 50 && (
                <span className="badge bg-green-100 text-green-700 border border-green-300 dark:bg-green-900/60 dark:text-green-300 dark:border-green-700">
                  ✓ Good
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-widest">Battery</p>
            <p className={`text-3xl font-bold ${text}`}>
              {pct != null ? `${pct}` : '—'}
              {pct != null && <span className="text-base font-normal text-gray-400 ml-1">%*</span>}
            </p>
            {volt != null && (
              <p className="text-xs text-gray-400 dark:text-gray-500">{volt.toFixed(2)} V</p>
            )}
          </div>
        )
      })()}
      <div className="col-span-2 lg:col-span-3 xl:col-span-6 mt-2 px-1">
        <p className="text-[10px] text-gray-400 dark:text-gray-500 italic">
          * Relative light index (0–1000). Not calibrated lux.
        </p>
        <p className="text-[10px] text-gray-400 dark:text-gray-500 italic mt-0.5">
          * Battery percentage is estimated via voltage and may not be 100% accurate.
        </p>
      </div>
    </div>
  )
}
