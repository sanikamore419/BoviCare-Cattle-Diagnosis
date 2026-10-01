import axios from 'axios'

export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('bovicare_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem('bovicare_token')
    localStorage.removeItem('bovicare_user')
    window.dispatchEvent(new Event('bovicare:auth-expired'))
  }
  return Promise.reject(error)
})
