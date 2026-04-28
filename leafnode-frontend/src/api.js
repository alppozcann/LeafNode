const BASE = '/api'

async function tryRefresh() {
  try {
    const res = await fetch(`${BASE}/auth/refresh`, { method: 'POST', credentials: 'include' })
    return res.ok
  } catch {
    return false
  }
}

async function request(path, options = {}, retries = 3) {
  let delay = 500
  let lastError
  let authRetried = false

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 15_000)
    try {
      const res = await fetch(`${BASE}${path}`, {
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        ...options,
      })
      clearTimeout(timer)

      if (res.status === 401 && !authRetried) {
        authRetried = true
        const refreshed = await tryRefresh()
        if (refreshed) {
          attempt--
          continue
        }
        throw Object.assign(new Error('Session expired'), { status: 401 })
      }

      if (res.status === 204) return null

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail ?? 'Request failed')
      }
      return await res.json()
    } catch (e) {
      clearTimeout(timer)
      if (e.status === 401) throw e
      const isNetworkError = e.name === 'AbortError' || e.name === 'TypeError'
      if (!isNetworkError || attempt === retries) throw e
      lastError = e
      await new Promise(r => setTimeout(r, delay))
      delay = Math.min(delay * 2, 8_000)
    }
  }
  throw lastError
}

export const getMe = () => request('/auth/me')

export const logout = () =>
  fetch(`${BASE}/auth/logout`, { method: 'POST', credentials: 'include' })

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

export const resolveAnomaly = (id) =>
  request(`/anomalies/${id}`, { method: 'DELETE' })

export const sendCommand = (deviceId, cmd, params = null) =>
  request(`/devices/${encodeURIComponent(deviceId)}/command`, {
    method: 'POST',
    body: JSON.stringify({ cmd, params }),
  })
