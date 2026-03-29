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

export const getReadings = (deviceId, limit = 30) =>
  request(`/readings/${encodeURIComponent(deviceId)}?limit=${limit}`)

export const getLatestReading = (deviceId) =>
  request(`/readings/${encodeURIComponent(deviceId)}/latest`)

export const getAnomalies = (deviceId, limit = 20) =>
  request(`/anomalies/${encodeURIComponent(deviceId)}?limit=${limit}`)

export const getHealth = () => request('/health')
