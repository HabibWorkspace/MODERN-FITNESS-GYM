import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import apiClient from '../services/api'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const navigate = useNavigate()
  
  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing reset token')
    }
  }, [token])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    
    setLoading(true)
    
    try {
      await apiClient.post('/auth/reset-password', {
        token,
        new_password: password
      })
      
      setSuccess(true)
      setTimeout(() => {
        navigate('/login')
      }, 3000)
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to reset password')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-charcoal-dark flex items-center justify-center p-4">
        <div className="bg-fitnix-charcoal rounded-2xl p-8 w-full max-w-md border border-fitnix-primary">
          <div className="text-center">
            <svg className="w-16 h-16 mx-auto text-fitnix-primary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-2xl font-bold text-fitnix-primary mb-2">Password Reset Successful!</h2>
            <p className="text-fitnix-off-white mb-4">
              Your password has been reset successfully.
            </p>
            <p className="text-fitnix-off-white/60">
              Redirecting to login page...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-charcoal-dark flex items-center justify-center p-4">
      <div className="bg-fitnix-charcoal rounded-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <img 
            src="/fitcore-logo.png" 
            alt="FitCore Logo" 
            className="h-16 mx-auto mb-4"
          />
          <h1 className="text-3xl font-bold text-fitnix-primary mb-2">Reset Password</h1>
          <p className="text-fitnix-off-white/60">Enter your new password</p>
        </div>

        {error && (
          <div className="bg-charcoal-dark border border-red-500 text-fitnix-off-white px-4 py-3 rounded-xl mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {error}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-fitnix-off-white mb-2 font-semibold">New Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-charcoal-dark text-fitnix-off-white px-4 py-3 pr-12 rounded-lg border border-neutral-border focus:border-fitnix-primary focus:outline-none"
                placeholder="Enter new password"
                required
                disabled={!token || loading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-fitnix-off-white/60 hover:text-fitnix-primary transition-colors"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M3.98 8.223A10.477 10.477 0 001.934 12c2.292 5.118 7.169 8 11.982 8.018A11.556 11.556 0 008.126 9.86m12.868-5.432a9.879 9.879 0 018.9 10.158" />
                    <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path fillRule="evenodd" d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 010-1.113zM17.25 12a5.25 5.25 0 11-10.5 0 5.25 5.25 0 0110.5 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-fitnix-off-white mb-2 font-semibold">Confirm Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-charcoal-dark text-fitnix-off-white px-4 py-3 rounded-lg border border-neutral-border focus:border-fitnix-primary focus:outline-none"
              placeholder="Confirm new password"
              required
              disabled={!token || loading}
            />
          </div>

          <button
            type="submit"
            disabled={!token || loading}
            className="w-full bg-fitnix-primary hover:bg-fitnix-primary-dark text-fitnix-off-white-dark font-bold py-3 px-4 rounded-lg transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-fitnix-primary hover:text-fitnix-primary-dark transition-colors"
            >
              Back to Login
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
