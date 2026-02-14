import { Navigate } from 'react-router-dom'

export default function ProtectedRoute({ children, requiredRole }) {
  const token = localStorage.getItem('token')
  const user = localStorage.getItem('user')

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  try {
    const userData = JSON.parse(user)
    if (requiredRole && userData.role !== requiredRole) {
      return <Navigate to="/login" replace />
    }
  } catch (e) {
    return <Navigate to="/login" replace />
  }

  return children
}
