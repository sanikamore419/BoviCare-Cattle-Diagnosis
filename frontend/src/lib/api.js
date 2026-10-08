import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
export const api = axios.create({ baseURL, withCredentials: true })

let refreshPromise = null

function signalSessionExpired() {
  localStorage.removeItem('bovicare_token')
  localStorage.removeItem('bovicare_user')
  window.dispatchEvent(new Event('bovicare:auth-expired'))
}

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = axios.post(`${baseURL}/auth/refresh`, {}, { withCredentials: true })
      .then(response => {
        localStorage.setItem('bovicare_token', response.data.access_token)
        localStorage.setItem('bovicare_user', JSON.stringify(response.data.user))
        return response.data.access_token
      })
      .catch(error => {
        signalSessionExpired()
        throw error
      })
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

api.interceptors.request.use(config => {
  const token = localStorage.getItem('bovicare_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(response => response, async error => {
  const config = error.config
  const status = error.response?.status
  const authEndpoint = /\/auth\/(login|register|refresh|logout)(\?|$)/.test(config?.url || '')
  if (status !== 401 || !config || config._retriedAfterRefresh || authEndpoint) {
    return Promise.reject(error)
  }

  config._retriedAfterRefresh = true
  try {
    const accessToken = await refreshAccessToken()
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${accessToken}`
    return api(config)
  } catch {
    return Promise.reject(error)
  }
})
