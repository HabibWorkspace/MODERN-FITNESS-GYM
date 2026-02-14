import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminMembers from './pages/admin/AdminMembers'
import AdminTrainers from './pages/admin/AdminTrainers'
import AdminFinance from './pages/admin/AdminFinance'
import AdminSettings from './pages/admin/AdminSettings'
import AdminAnalytics from './pages/admin/AdminAnalytics'
import AdminPackages from './pages/admin/AdminPackages'
import OfflineIndicator from './components/OfflineIndicator'

function App() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return (
    <Router basename="/MODERN-FITNESS-GYM" future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      {!isOnline && <OfflineIndicator />}
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        
        {/* Admin Routes Only */}
        <Route path="/admin" element={<ProtectedRoute requiredRole="admin"><AdminDashboard /></ProtectedRoute>} />
        <Route path="/admin/members" element={<ProtectedRoute requiredRole="admin"><AdminMembers /></ProtectedRoute>} />
        <Route path="/admin/trainers" element={<ProtectedRoute requiredRole="admin"><AdminTrainers /></ProtectedRoute>} />
        <Route path="/admin/packages" element={<ProtectedRoute requiredRole="admin"><AdminPackages /></ProtectedRoute>} />
        <Route path="/admin/finance" element={<ProtectedRoute requiredRole="admin"><AdminFinance /></ProtectedRoute>} />
        <Route path="/admin/analytics" element={<ProtectedRoute requiredRole="admin"><AdminAnalytics /></ProtectedRoute>} />
        <Route path="/admin/settings" element={<ProtectedRoute requiredRole="admin"><AdminSettings /></ProtectedRoute>} />
        
        {/* Default redirect - Only admin login available */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Catch-all for removed routes */}
        <Route path="/member/*" element={<Navigate to="/login" replace />} />
        <Route path="/trainer/*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  )
}

export default App
