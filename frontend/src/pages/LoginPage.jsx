import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../services/api'
import logo from '/fitcore-logo.png'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const iconsContainerRef = useRef(null)

  useEffect(() => {
    const container = iconsContainerRef.current
    if (!container) return

    // Simple, recognizable gym equipment icons
    const iconTypes = [
      // Dumbbell 1
      `<svg viewBox="0 0 100 40" fill="currentColor">
        <rect x="5" y="12" width="10" height="16" rx="2"/>
        <rect x="15" y="16" width="70" height="8" rx="2"/>
        <rect x="85" y="12" width="10" height="16" rx="2"/>
      </svg>`,
      
      // Barbell
      `<svg viewBox="0 0 100 40" fill="currentColor">
        <rect x="5" y="10" width="8" height="20" rx="1"/>
        <rect x="13" y="12" width="74" height="16" rx="2"/>
        <rect x="87" y="10" width="8" height="20" rx="1"/>
      </svg>`,
      
      // Kettlebell
      `<svg viewBox="0 0 50 60" fill="currentColor">
        <path d="M 20 15 Q 20 10, 25 10 Q 30 10, 30 15" stroke="currentColor" stroke-width="4" fill="none"/>
        <circle cx="25" cy="35" r="18"/>
      </svg>`,
      
      // Weight plate
      `<svg viewBox="0 0 40 40" fill="currentColor">
        <circle cx="20" cy="20" r="18"/>
        <circle cx="20" cy="20" r="8" fill="#0B0B0B"/>
      </svg>`,
      
      // Water bottle
      `<svg viewBox="0 0 40 80" fill="currentColor">
        <rect x="12" y="5" width="16" height="8" rx="2"/>
        <rect x="10" y="13" width="20" height="60" rx="3"/>
      </svg>`,
      
      // Stopwatch
      `<svg viewBox="0 0 60 70" fill="currentColor">
        <rect x="25" y="5" width="10" height="8" rx="2"/>
        <circle cx="30" cy="40" r="25"/>
        <line x1="30" y1="40" x2="30" y2="20" stroke="#0B0B0B" stroke-width="3"/>
      </svg>`,
      
      // Heart rate
      `<svg viewBox="0 0 60 50" fill="currentColor">
        <path d="M 30 45 L 10 20 Q 10 5, 20 5 Q 30 5, 30 15 Q 30 5, 40 5 Q 50 5, 50 20 Z"/>
      </svg>`,
      
      // Jump rope
      `<svg viewBox="0 0 80 40" fill="currentColor">
        <rect x="5" y="10" width="6" height="20" rx="2"/>
        <path d="M 11 20 Q 25 5, 40 20 Q 55 35, 69 20" stroke="currentColor" stroke-width="4" fill="none"/>
        <rect x="69" y="10" width="6" height="20" rx="2"/>
      </svg>`,
      
      // Medicine ball
      `<svg viewBox="0 0 50 50" fill="currentColor">
        <circle cx="25" cy="25" r="22"/>
        <path d="M 25 5 Q 25 25, 25 45" stroke="#0B0B0B" stroke-width="2" fill="none"/>
        <path d="M 5 25 Q 25 25, 45 25" stroke="#0B0B0B" stroke-width="2" fill="none"/>
      </svg>`,
      
      // Protein shaker
      `<svg viewBox="0 0 40 70" fill="currentColor">
        <rect x="8" y="5" width="24" height="10" rx="2"/>
        <rect x="10" y="15" width="20" height="50" rx="3"/>
        <circle cx="20" cy="40" r="8" fill="#0B0B0B"/>
      </svg>`,
      
      // Yoga mat
      `<svg viewBox="0 0 80 40" fill="currentColor">
        <rect x="10" y="15" width="60" height="10" rx="5"/>
        <circle cx="15" cy="20" r="3"/>
        <circle cx="65" cy="20" r="3"/>
      </svg>`,
      
      // Boxing glove
      `<svg viewBox="0 0 60 70" fill="currentColor">
        <ellipse cx="30" cy="35" rx="25" ry="30"/>
        <rect x="15" y="60" width="30" height="8" rx="2"/>
      </svg>`,
      
      // Resistance band
      `<svg viewBox="0 0 80 50" fill="currentColor">
        <ellipse cx="40" cy="25" rx="35" ry="20" fill="none" stroke="currentColor" stroke-width="6"/>
        <rect x="5" y="20" width="8" height="10" rx="2"/>
        <rect x="67" y="20" width="8" height="10" rx="2"/>
      </svg>`,
      
      // Gym bag
      `<svg viewBox="0 0 80 50" fill="currentColor">
        <rect x="10" y="20" width="60" height="25" rx="4"/>
        <path d="M 25 20 L 25 12 L 55 12 L 55 20" stroke="currentColor" stroke-width="3" fill="none"/>
      </svg>`,
      
      // Towel
      `<svg viewBox="0 0 60 80" fill="currentColor">
        <rect x="10" y="10" width="40" height="60" rx="3"/>
        <line x1="10" y1="20" x2="50" y2="20" stroke="#0B0B0B" stroke-width="2"/>
        <line x1="10" y1="30" x2="50" y2="30" stroke="#0B0B0B" stroke-width="2"/>
      </svg>`,
      
      // Fitness watch
      `<svg viewBox="0 0 50 60" fill="currentColor">
        <rect x="10" y="5" width="30" height="10" rx="3"/>
        <rect x="8" y="15" width="34" height="30" rx="4"/>
        <rect x="10" y="45" width="30" height="10" rx="3"/>
      </svg>`
    ]

    const icons = []
    const positions = [] // Track positions to avoid overlap
    const numIcons = 16 // Increased from 12 to 16 for better coverage
    const minDistance = 80 // Reduced from 100 to allow more icons

    // Shuffle array helper function
    const shuffleArray = (array) => {
      const shuffled = [...array]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      return shuffled
    }

    // Shuffle icon types to ensure uniqueness
    const shuffledIcons = shuffleArray(iconTypes).slice(0, numIcons)

    // Helper function to check if position is valid (not too close to others)
    const isValidPosition = (x, y, size) => {
      for (const pos of positions) {
        const dx = x - pos.x
        const dy = y - pos.y
        const distance = Math.sqrt(dx * dx + dy * dy)
        const requiredDistance = minDistance
        
        if (distance < requiredDistance) {
          return false
        }
      }
      return true
    }

    // Create floating icons with proper spacing - spread across entire screen
    for (let i = 0; i < numIcons; i++) {
      const icon = document.createElement('div')
      icon.className = 'floating-fitness-icon'
      
      const size = 50 + Math.random() * 40 // 50-90px (more consistent sizes)
      
      // Try to find a valid position
      let x, y, attempts = 0
      let validPosition = false
      
      while (!validPosition && attempts < 200) {
        // Distribute more evenly across the entire screen
        if (i < 4) {
          // Left column
          x = 5 + Math.random() * 15
          y = 10 + Math.random() * 80
        } else if (i < 8) {
          // Right column
          x = 80 + Math.random() * 15
          y = 10 + Math.random() * 80
        } else if (i < 10) {
          // Top row (left and right sides only)
          x = Math.random() > 0.5 ? 5 + Math.random() * 20 : 75 + Math.random() * 20
          y = 5 + Math.random() * 15
        } else if (i < 12) {
          // Bottom row (left and right sides only)
          x = Math.random() > 0.5 ? 5 + Math.random() * 20 : 75 + Math.random() * 20
          y = 80 + Math.random() * 15
        } else {
          // Middle areas (sparse, avoiding center)
          x = Math.random() > 0.5 ? 20 + Math.random() * 15 : 65 + Math.random() * 15
          y = 30 + Math.random() * 40
        }
        
        validPosition = isValidPosition(x, y, size)
        attempts++
      }
      
      // If no valid position found after 200 attempts, use a fallback position
      if (!validPosition) {
        // Fallback: place in a grid-like pattern around edges
        const col = i % 4
        const row = Math.floor(i / 4)
        if (col < 2) {
          x = 10 + col * 10
        } else {
          x = 80 + (col - 2) * 10
        }
        y = 15 + row * 25
      }
      
      // Store position
      positions.push({ x, y, size })
      
      const duration = 4 + Math.random() * 3 // 4-7s (smoother timing)
      const delay = Math.random() * 2
      const iconType = shuffledIcons[i] // Use unique icon for each position
      
      // Contained movement - stays in its area with more space
      const moveRange = 30 // Increased from 15 to 30 pixels
      const animationStyle = `float-contained ${duration}s cubic-bezier(0.45, 0.05, 0.55, 0.95) ${delay}s infinite`
      
      // Subtle rotation
      const rotation = -15 + Math.random() * 30
      
      icon.innerHTML = iconType
      icon.style.cssText = `
        position: absolute;
        left: ${x}%;
        top: ${y}%;
        width: ${size}px;
        height: ${size}px;
        color: #B6FF00;
        opacity: ${0.08 + Math.random() * 0.05};
        filter: drop-shadow(0 4px 12px rgba(182, 255, 0, 0.2));
        animation: ${animationStyle};
        transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        pointer-events: auto;
        will-change: transform;
        transform: rotate(${rotation}deg);
        --move-x: ${-moveRange + Math.random() * moveRange * 2}px;
        --move-y: ${-moveRange + Math.random() * moveRange * 2}px;
      `
      
      container.appendChild(icon)
      icons.push({ element: icon, originalX: x, originalY: y, size })
    }

    // Smoother mouse interaction
    let rafId = null
    const handleMouseMove = (e) => {
      if (rafId) return
      
      rafId = requestAnimationFrame(() => {
        const mouseX = e.clientX
        const mouseY = e.clientY
        
        icons.forEach(({ element }) => {
          const rect = element.getBoundingClientRect()
          const iconCenterX = rect.left + rect.width / 2
          const iconCenterY = rect.top + rect.height / 2
          
          const dx = iconCenterX - mouseX
          const dy = iconCenterY - mouseY
          const distance = Math.sqrt(dx * dx + dy * dy)
          
          const interactionRadius = 200
          
          if (distance < interactionRadius) {
            const angle = Math.atan2(dy, dx)
            const force = (interactionRadius - distance) / interactionRadius
            const pushX = Math.cos(angle) * force * 50
            const pushY = Math.sin(angle) * force * 50
            
            element.style.transform = `translate(${pushX}px, ${pushY}px) scale(1.2)`
            element.style.opacity = '0.25'
            element.style.filter = 'drop-shadow(0 6px 16px rgba(182, 255, 0, 0.4))'
          } else {
            element.style.transform = 'translate(0, 0) scale(1)'
            element.style.opacity = '0.1'
            element.style.filter = 'drop-shadow(0 4px 12px rgba(182, 255, 0, 0.2))'
          }
        })
        
        rafId = null
      })
    }

    const handleMouseOver = (e) => {
      if (e.target.classList.contains('floating-fitness-icon')) {
        e.target.style.transform = 'scale(1.4) rotate(15deg)'
        e.target.style.opacity = '0.35'
        e.target.style.filter = 'drop-shadow(0 8px 20px rgba(182, 255, 0, 0.5))'
      }
    }

    const handleMouseOut = (e) => {
      if (e.target.classList.contains('floating-fitness-icon')) {
        e.target.style.transform = 'scale(1)'
        e.target.style.opacity = '0.1'
        e.target.style.filter = 'drop-shadow(0 4px 12px rgba(182, 255, 0, 0.2))'
      }
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    container.addEventListener('mouseover', handleMouseOver)
    container.addEventListener('mouseout', handleMouseOut)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      container.removeEventListener('mouseover', handleMouseOver)
      container.removeEventListener('mouseout', handleMouseOut)
      if (rafId) cancelAnimationFrame(rafId)
      icons.forEach(({ element }) => element.remove())
    }
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password,
      })

      const { access_token, user } = response.data
      
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))

      if (user.role === 'ADMIN' || user.role === 'admin') {
        navigate('/admin')
      } else if (user.role === 'TRAINER' || user.role === 'trainer') {
        navigate('/trainer')
      } else if (user.role === 'MEMBER' || user.role === 'member') {
        navigate('/member')
      } else {
        setError('Unknown user role')
      }
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.message || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-fitnix-black">
      {/* Dark Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-fitnix-black via-fitnix-charcoal to-fitnix-black"></div>

      {/* Floating Fitness Icons Container */}
      <div 
        ref={iconsContainerRef} 
        className="absolute inset-0 z-0"
        style={{ pointerEvents: 'none' }}
      ></div>

      {/* Login Form Container */}
      <div 
        className="relative min-h-screen flex items-center justify-center p-4"
        style={{ zIndex: 10 }}
      >
        <div className="w-full max-w-md animate-fadeInUp">
          {/* Logo with glow */}
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-fitnix-lime/30 blur-2xl rounded-full"></div>
              <img 
                src={logo} 
                alt="FitCore Logo" 
                className="relative w-24 h-24 object-contain animate-pulse-slow" 
              />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-5xl font-bold text-center mb-2">
            <span className="fitnix-gradient-text">FitCore</span>
          </h1>
          <p className="text-center text-fitnix-off-white/60 mb-8 text-sm">
            Your Fitness Partner
          </p>

          {/* Dark Theme Login Card */}
          <div className="backdrop-blur-xl bg-fitnix-charcoal/95 border-2 border-fitnix-lime/30 rounded-2xl shadow-2xl shadow-fitnix-lime/20 p-8 hover:border-fitnix-lime/50 transition-all duration-300">
            <h2 className="text-2xl font-bold text-fitnix-off-white mb-6 text-center">Welcome Back</h2>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg animate-shake">
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-2 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="text-sm text-fitnix-off-white">{error}</span>
                </div>
              </div>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Username Field */}
              <div className="group">
                <label className="block text-fitnix-off-white/80 font-semibold mb-2 text-sm">
                  Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-fitnix-lime/60 group-hover:text-fitnix-lime transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                    className="w-full pl-10 pr-4 py-3 bg-fitnix-black/50 border-2 border-fitnix-off-white/20 rounded-lg text-fitnix-off-white placeholder-fitnix-off-white/40 focus:outline-none focus:border-fitnix-lime focus:ring-2 focus:ring-fitnix-lime/20 transition-all duration-300 hover:border-fitnix-lime/50"
                    placeholder="Enter your username"
                    required
                  />
                </div>
              </div>

              {/* Password Field */}
              <div className="group">
                <label className="block text-fitnix-off-white/80 font-semibold mb-2 text-sm">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="w-5 h-5 text-fitnix-lime/60 group-hover:text-fitnix-lime transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    className="w-full pl-10 pr-12 py-3 bg-fitnix-black/50 border-2 border-fitnix-off-white/20 rounded-lg text-fitnix-off-white placeholder-fitnix-off-white/40 focus:outline-none focus:border-fitnix-lime focus:ring-2 focus:ring-fitnix-lime/20 transition-all duration-300 hover:border-fitnix-lime/50"
                    placeholder="Enter your password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-fitnix-off-white/60 hover:text-fitnix-lime transition-colors"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-fitnix-lime to-fitnix-dark-lime hover:from-fitnix-dark-lime hover:to-fitnix-lime text-fitnix-black font-bold py-3 px-4 rounded-lg transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-105 hover:shadow-lg hover:shadow-fitnix-lime/50 active:scale-95 relative overflow-hidden"
              >
                {loading && (
                  <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></span>
                )}
                {loading ? (
                  <span className="flex items-center justify-center relative z-10">
                    <span className="relative flex h-5 w-5 mr-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fitnix-black opacity-40"></span>
                      <span className="relative inline-flex rounded-full h-5 w-5 border-2 border-fitnix-black border-t-transparent animate-spin"></span>
                    </span>
                    Logging in...
                  </span>
                ) : (
                  'Login'
                )}
              </button>
            </form>
          </div>

          {/* Footer */}
          <p className="text-center text-fitnix-off-white/40 text-sm mt-6">
            © 2026 FitCore. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}
