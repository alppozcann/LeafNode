const BASE = '/api'

async function request(path, options = {}, retries = 3) {
  let delay = 500
  let lastError
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 15_000)
    try {
      const res = await fetch(`${BASE}${path}`, {
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })
      clearTimeout(timer)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        // Don't retry HTTP errors — they're deterministic (4xx/5xx from server)
        throw new Error(err.detail ?? 'Request failed')
      }
      return await res.json()
    } catch (e) {
      clearTimeout(timer)
      // Only retry on network-level failures (timeout = AbortError, no connection = TypeError)
      const isNetworkError = e.name === 'AbortError' || e.name === 'TypeError'
      if (!isNetworkError || attempt === retries) throw e
      lastError = e
      await new Promise(r => setTimeout(r, delay))
      delay = Math.min(delay * 2, 8_000)
    }
  }
  throw lastError
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
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 15_000)
  try {
    const res = await fetch(`/api/anomalies/${id}`, {
      method: 'DELETE',
      signal: controller.signal,
    })
    if (!res.ok) throw new Error('Failed to resolve anomaly')
  } finally {
    clearTimeout(timer)
  }
}

export const sendCommand = (deviceId, cmd, params = null) =>
  request(`/devices/${encodeURIComponent(deviceId)}/command`, {
    method: 'POST',
    body: JSON.stringify({ cmd, params }),
  })
