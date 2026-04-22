import { useState } from 'react'
import * as api from '../api'

export default function PlantPanel({ plant, onRegister, deviceId }) {
  if (!plant) {
    return (
      <div className="card p-6 flex flex-col items-center justify-center gap-4 text-center min-h-[180px]">
        <span className="text-5xl">🪴</span>
        <div>
          <p className="font-semibold text-gray-700 dark:text-gray-300">No plant registered</p>
          <p className="text-sm text-gray-400 mt-1">Register a plant to enable anomaly detection</p>
        </div>
        <button onClick={onRegister} className="btn-primary">Register Plant</button>
      </div>
    )
  }

  const thresholds = [
    { label: 'Temperature', min: plant.temperature_min, max: plant.temperature_max, unit: '°C',   color: 'text-orange-500 dark:text-orange-400' },
    { label: 'Humidity',    min: plant.humidity_min,    max: plant.humidity_max,    unit: '%',    color: 'text-blue-500 dark:text-blue-400' },
    { label: 'Pressure',    min: plant.pressure_min,    max: plant.pressure_max,    unit: ' hPa', color: 'text-purple-500 dark:text-purple-400' },
    { label: 'Light',       min: plant.light_min,       max: plant.light_max,       unit: ' lux', color: 'text-yellow-500 dark:text-yellow-400' },
    { label: 'Soil Moist',  min: plant.soil_moisture_min, max: plant.soil_moisture_max, unit: '%', color: 'text-emerald-500 dark:text-emerald-400' },
  ]

  const [cmdSending, setCmdSending] = useState(false)
  const [cmdResult, setCmdResult] = useState(null)

  async function handleCmd(cmd, times) {
    if (!deviceId) return
    setCmdSending(true)
    setCmdResult(null)
    try {
      await api.sendCommand(deviceId, cmd, times)
      setCmdResult({ type: 'success', text: `Command '${cmd}' queued!` })
    } catch (e) {
      setCmdResult({ type: 'error', text: e.message })
    }
    setCmdSending(false)
    setTimeout(() => setCmdResult(null), 5000)
  }

  return (
    <div className="card p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-1">Active Plant</p>
          <h2 className="text-xl font-bold text-leaf-600 dark:text-leaf-400">{plant.plant_name}</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Registered {new Date(plant.created_at).toLocaleDateString()}
          </p>
        </div>
        <button onClick={onRegister} className="btn-secondary text-sm">
          Change
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        {thresholds.map((t) => (
          <div key={t.label} className="bg-gray-100 dark:bg-gray-800/60 rounded-xl px-3 py-2">
            <p className={`text-xs font-medium ${t.color} mb-0.5`}>{t.label}</p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {t.min}{t.unit} – {t.max}{t.unit}
            </p>
          </div>
        ))}
      </div>

      <div className="pt-4 border-t border-gray-100 dark:border-gray-800/60">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Device Commands</p>
          <span className="text-[10px] text-orange-600 bg-orange-100 border border-orange-200 dark:bg-orange-900/40 dark:text-orange-400 dark:border-orange-800/60 px-2 py-0.5 rounded-full flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></span>
            Executes on next wake (35s)
          </span>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => handleCmd('led_on')} disabled={cmdSending} className="btn-secondary text-xs px-3 py-1.5 font-medium disabled:opacity-50">LED On</button>
          <button onClick={() => handleCmd('led_off')} disabled={cmdSending} className="btn-secondary text-xs px-3 py-1.5 font-medium disabled:opacity-50">LED Off</button>
          <button onClick={() => handleCmd('ping')} disabled={cmdSending} className="btn-secondary text-xs px-3 py-1.5 font-medium disabled:opacity-50">Ping</button>
          <button onClick={() => handleCmd('blink', { times: 3 })} disabled={cmdSending} className="btn-secondary text-xs px-3 py-1.5 font-medium disabled:opacity-50">Blink</button>
        </div>
        {cmdResult && (
          <p className={`mt-2 text-xs font-medium text-center ${cmdResult.type === 'success' ? 'text-leaf-600 dark:text-leaf-400' : 'text-red-500'}`}>
            {cmdResult.text}
          </p>
        )}
      </div>
    </div>
  )
}
