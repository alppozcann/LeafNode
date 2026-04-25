import { useState, useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'

const METRICS = [
  { key: 'temperature',   label: 'Temperature',   unit: '°C',   color: '#f97316', profileMin: 'temperature_min', profileMax: 'temperature_max' },
  { key: 'humidity',      label: 'Humidity',      unit: '%',    color: '#3b82f6', profileMin: 'humidity_min',    profileMax: 'humidity_max' },
  { key: 'pressure',      label: 'Pressure',      unit: ' hPa', color: '#a855f7', profileMin: 'pressure_min',    profileMax: 'pressure_max' },
  { key: 'light',         label: 'Light',         unit: ' lux*', color: '#eab308', profileMin: 'light_min',       profileMax: 'light_max' },
  { key: 'soil_moisture', label: 'Soil Moisture', unit: '%',    color: '#10b981', profileMin: 'soil_moisture_min', profileMax: 'soil_moisture_max' },
]

function formatTime(ts, range) {
  const date = new Date(ts)
  const isLongRange = ['1d', '5d', '10d', '15d', '30d'].includes(range)
  
  if (isLongRange) {
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false
    })
  }
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false
  })
}

function CustomTooltip({ active, payload, label, unit, isDark, range }) {
  if (!active || !payload?.length) return null
  const formattedLabel = formatTime(label, range)
  return (
    <div className={`border rounded-lg px-3 py-2 text-xs shadow-xl ${
      isDark
        ? 'bg-gray-800 border-gray-700 text-white'
        : 'bg-white border-gray-200 text-gray-900'
    }`}>
      <p className={`mb-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{formattedLabel}</p>
      <p className="font-semibold">{payload[0].value?.toFixed(2)}{unit}</p>
    </div>
  )
}

export default function ReadingsChart({ readings, plant, isDark, timeRange, onRangeChange }) {
  const [activeMetric, setActiveMetric] = useState('temperature')
  const [showDots, setShowDots] = useState(false)

  const metric = METRICS.find((m) => m.key === activeMetric)

  const data = useMemo(
    () => [...readings].reverse().map((r) => ({ 
      ...r, 
      timestamp_num: new Date(r.timestamp).getTime() 
    })),
    [readings]
  )

  const minRef = plant?.[metric.profileMin]
  const maxRef = plant?.[metric.profileMax]

  const gridColor  = isDark ? '#1f2937' : '#f3f4f6'
  const axisColor  = isDark ? '#6b7280' : '#9ca3af'

  return (
    <div className="card p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold text-gray-800 dark:text-gray-200">Reading History</h3>
          <div className="flex items-center gap-2">
            <select 
              value={timeRange} 
              onChange={(e) => onRangeChange?.(e.target.value)}
              className={`px-3 py-1.5 rounded-lg border text-xs focus:outline-none cursor-pointer ${isDark ? 'bg-gray-800 border-gray-700 text-gray-200' : 'bg-white border-gray-200 text-gray-700'}`}
            >
              <option value="30m">Last 30m</option>
              <option value="1h">Last 1h</option>
              <option value="3h">Last 3h</option>
              <option value="6h">Last 6h</option>
              <option value="12h">Last 12h</option>
              <option value="1d">Last 1d</option>
              <option value="5d">Last 5d</option>
              <option value="10d">Last 10d</option>
              <option value="15d">Last 15d</option>
              <option value="30d">Last 30d</option>
            </select>
            <button
              onClick={() => setShowDots(!showDots)}
              title={showDots ? 'Hide measurement points' : 'Show measurement points'}
              className={`p-1.5 rounded-lg border transition-all ${
                showDots 
                  ? 'bg-leaf-50 border-leaf-200 text-leaf-600 dark:bg-leaf-900/20 dark:border-leaf-800 dark:text-leaf-400' 
                  : 'bg-white border-gray-200 text-gray-500 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-400'
              }`}
            >
              <DotIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
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
              dataKey="timestamp_num"
              type="number"
              domain={['dataMin', 'dataMax']}
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: gridColor }}
              tickFormatter={(ts) => formatTime(ts, timeRange)}
              scale="time"
            />
            <YAxis
              tick={{ fill: axisColor, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
              domain={['auto', 'auto']}
            />
            <Tooltip 
              content={<CustomTooltip unit={metric.unit} isDark={isDark} range={timeRange} />} 
              labelFormatter={(ts) => formatTime(ts, timeRange)}
              cursor={{ stroke: isDark ? '#374151' : '#e5e7eb' }} 
            />
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
              dot={showDots ? { r: 3, fill: metric.color, strokeWidth: 0 } : false}
              activeDot={{ r: 5, fill: metric.color, stroke: isDark ? '#111827' : '#fff', strokeWidth: 2 }}
              animationDuration={500}
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

function DotIcon({ className }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="3" />
      <circle cx="6" cy="12" r="3" opacity="0.4" />
      <circle cx="18" cy="12" r="3" opacity="0.4" />
    </svg>
  )
}
