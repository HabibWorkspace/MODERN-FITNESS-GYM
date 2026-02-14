import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://fitcore-backend.onrender.com/api'

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // Add cache control headers to prevent caching
    config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    config.headers['Pragma'] = 'no-cache'
    config.headers['Expires'] = '0'
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Only logout if it's an authentication error, not authorization
      const errorMessage = error.response?.data?.error || ''
      
      // Don't logout for authorization errors (403-like messages in 401)
      if (errorMessage.includes('Only members') || 
          errorMessage.includes('Insufficient permissions') ||
          errorMessage.includes('Unauthorized')) {
        // This is an authorization issue, not authentication - don't logout
        return Promise.reject(error)
      }
      
      // Token expired or invalid - logout
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
