export default function PlantPanel({ plant, onRegister }) {
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
  ]

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

      <div className="grid grid-cols-2 gap-2">
        {thresholds.map((t) => (
          <div key={t.label} className="bg-gray-100 dark:bg-gray-800/60 rounded-xl px-3 py-2">
            <p className={`text-xs font-medium ${t.color} mb-0.5`}>{t.label}</p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {t.min}{t.unit} – {t.max}{t.unit}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
