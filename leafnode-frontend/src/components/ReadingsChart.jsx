import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'

const METRICS = [
  { key: 'temperature', label: 'Temperature', unit: '°C',   color: '#f97316', profileMin: 'temperature_min', profileMax: 'temperature_max' },
  { key: 'humidity',    label: 'Humidity',    unit: '%',    color: '#3b82f6', profileMin: 'humidity_min',    profileMax: 'humidity_max' },
  { key: 'pressure',    label: 'Pressure',    unit: ' hPa', color: '#a855f7', profileMin: 'pressure_min',    profileMax: 'pressure_max' },
  { key: 'light',       label: 'Light',       unit: ' lux', color: '#eab308', profileMin: 'light_min',       profileMax: 'light_max' },
]

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function CustomTooltip({ active, payload, label, unit, isDark }) {
  if (!active || !payload?.length) return null
  return (
    <div className={`border rounded-lg px-3 py-2 text-xs shadow-xl ${
      isDark
        ? 'bg-gray-800 border-gray-700 text-white'
        : 'bg-white border-gray-200 text-gray-900'
    }`}>
      <p className={`mb-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{label}</p>
      <p className="font-semibold">{payload[0].value?.toFixed(2)}{unit}</p>
    </div>
  )
}

export default function ReadingsChart({ readings, plant, isDark }) {
  const [activeMetric, setActiveMetric] = useState('temperature')

  const metric = METRICS.find((m) => m.key === activeMetric)

  const data = useMemo(
    () => [...readings].reverse().map((r) => ({ ...r, time: formatTime(r.timestamp) })),
    [readings]
  )

  const minRef = plant?.[metric.profileMin]
  const maxRef = plant?.[metric.profileMax]

  const gridColor  = isDark ? '#1f2937' : '#f3f4f6'
  const axisColor  = isDark ? '#6b7280' : '#9ca3af'

  return (
    <div className="card p-6">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
        <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex-1">Reading History</h3>
        <div className="flex gap-2 flex-wrap">
          {METRICS.map((m) => (
            <button
              key={m.key}
              onClick={() => setActiveMetric(m.key)}
              style={activeMetric === m.key ? { borderColor: m.color, color: m.color, backgroundColor: `${m.color}18` } : {}}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                activeMetric === m.key
                  ? ''
                  : 'border-gray-200 text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:border-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {data.length === 0 ? (
        <div className="h-56 flex items-center justify-center text-gray-400 text-sm">
          No readings yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey="time"
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: gridColor }}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip unit={metric.unit} isDark={isDark} />} cursor={{ stroke: isDark ? '#374151' : '#e5e7eb' }} />
            {minRef != null && (
              <ReferenceLine y={minRef} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.6} />
            )}
            {maxRef != null && (
              <ReferenceLine y={maxRef} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.6} />
            )}
            <Line
              type="monotone"
              dataKey={metric.key}
              stroke={metric.color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: metric.color }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {(minRef != null || maxRef != null) && (
        <p className="text-xs text-gray-400 mt-2 text-right">— — threshold boundaries</p>
      )}
    </div>
  )
}
