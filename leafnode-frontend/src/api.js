const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  return res.json()
}

export const getPlant = (deviceId) =>
  request(`/plants/${encodeURIComponent(deviceId)}`)

export const createPlant = (plantName, deviceId) =>
  request('/plants', {
    method: 'POST',
    body: JSON.stringify({ plant_name: plantName, device_id: deviceId }),
  })

export const getReadings = (deviceId, range = '3h') =>
  request(`/readings/${encodeURIComponent(deviceId)}?range=${range}`)

export const getLatestReading = (deviceId) =>
  request(`/readings/${encodeURIComponent(deviceId)}/latest`)

export const getCommands = (deviceId, limit = 10) =>
  request(`/devices/${encodeURIComponent(deviceId)}/commands?limit=${limit}`)

export const getAnomalies = (deviceId, limit = 20) =>
  request(`/anomalies/${encodeURIComponent(deviceId)}?limit=${limit}`)

export const getHealth = () => request('/health')

export async function resolveAnomaly(id) {
  const res = await fetch(`/api/anomalies/${id}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to resolve anomaly')
}

export const sendCommand = (deviceId, cmd, params = null) =>
  request(`/devices/${encodeURIComponent(deviceId)}/command`, {
    method: 'POST',
    body: JSON.stringify({ cmd, params }),
  })
