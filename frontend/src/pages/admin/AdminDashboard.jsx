import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../../services/api'
import AdminLayout from '../../components/layouts/AdminLayout'
import logo from '/fitcore-logo.png'

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null)
  const [recentActivities, setRecentActivities] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchMetrics()
    fetchRecentActivities()
    
    // Auto-refresh metrics every 10 seconds to update overdue payments
    const metricsInterval = setInterval(() => {
      fetchMetrics()
    }, 10000)
    
    // Auto-refresh recent activities every 30 seconds
    const activitiesInterval = setInterval(() => {
      fetchRecentActivities()
    }, 30000)
    
    return () => {
      clearInterval(metricsInterval)
      clearInterval(activitiesInterval)
    }
  }, [])

  const fetchMetrics = async () => {
    try {
      const response = await apiClient.get(`/admin/dashboard/metrics?_t=${Date.now()}`)
      setMetrics(response.data)
    } catch (err) {
      setError('Failed to load dashboard metrics')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchRecentActivities = async () => {
    try {
      // Fetch recent members and transactions
      const [membersRes, transactionsRes] = await Promise.all([
        apiClient.get('/admin/members?per_page=5'),
        apiClient.get('/finance/transactions?per_page=5')
      ])

      const members = membersRes.data.members || []
      const transactions = transactionsRes.data.transactions || []

      // Combine and sort by timestamp
      const activities = []

      // Add member registrations
      members.forEach(member => {
        activities.push({
          type: 'member',
          icon: 'user',
          title: 'New member registered',
          description: `${member.username} joined the gym`,
          timestamp: member.created_at,
          color: 'fitnix-lime'
        })
      })

      // Add payment activities
      transactions.forEach(transaction => {
        if (transaction.status === 'COMPLETED' && transaction.paid_date) {
          activities.push({
            type: 'payment',
            icon: 'payment',
            title: 'Payment received',
            description: `Rs. ${transaction.amount} - Monthly membership`,
            timestamp: transaction.paid_date,
            color: 'fitnix-dark-lime'
          })
        }
      })

      // Sort by timestamp (newest first)
      activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

      setRecentActivities(activities.slice(0, 5))
    } catch (err) {
      console.error('Failed to fetch recent activities:', err)
    }
  }

  const getTimeAgo = (timestamp) => {
    const now = new Date()
    const past = new Date(timestamp)
    const diffMs = now - past
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const metricCards = [
    {
      title: 'Total Members',
      value: metrics?.total_members || 0,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      iconBg: 'bg-fitnix-lime',
      iconColor: 'text-fitnix-black',
      accentColor: 'text-fitnix-lime',
      borderColor: 'border-fitnix-lime/30',
      glowColor: 'hover:shadow-neon-lime'
    },
    {
      title: 'Overdue Payments',
      value: metrics?.overdue_payments_count || 0,
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      iconBg: 'bg-red-600',
      iconColor: 'text-white',
      accentColor: 'text-red-400',
      borderColor: 'border-red-500/30',
      glowColor: 'hover:shadow-neon-red'
    }
  ]

  const quickActions = [
    {
      title: 'Manage Members',
      description: 'Add, edit, and manage member accounts',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      path: '/admin/members',
      color: 'from-fitnix-lime to-fitnix-dark-lime'
    },
    {
      title: 'Manage Trainers',
      description: 'Handle trainer profiles and schedules',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      path: '/admin/trainers',
      color: 'from-fitnix-dark-lime to-fitnix-lime'
    },
    {
      title: 'Finance Overview',
      description: 'Track payments and financial reports',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      path: '/admin/finance',
      color: 'from-fitnix-lime to-fitnix-dark-lime'
    },
    {
      title: 'Analytics',
      description: 'View detailed reports and insights',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      path: '/admin/analytics',
      color: 'from-fitnix-dark-lime to-fitnix-lime'
    }
  ]

  if (loading) {
    return (
      <div className="fixed inset-0 bg-fitnix-black flex items-center justify-center z-50">
        <div className="relative flex flex-col items-center">
          {/* Outer rotating ring */}
          <div className="relative w-24 h-24">
            <div className="absolute inset-0 rounded-full border-4 border-fitnix-charcoal/30"></div>
            <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-fitnix-lime border-r-fitnix-lime animate-spin"></div>
            <div className="absolute inset-2 rounded-full border-4 border-transparent border-b-fitnix-dark-lime border-l-fitnix-dark-lime animate-spin-reverse"></div>
            {/* Logo in center */}
            <div className="absolute inset-0 flex items-center justify-center">
              <img 
                src={logo} 
                alt="FitNix Logo" 
                className="w-14 h-14 object-contain animate-pulse" 
                style={{ 
                  filter: 'drop-shadow(0 0 8px rgba(182, 255, 0, 0.3))',
                  mixBlendMode: 'screen'
                }} 
              />
            </div>
          </div>
          {/* Loading text */}
          <p className="mt-4 text-fitnix-lime font-semibold animate-pulse">Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <AdminLayout onLogout={handleLogout}>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold text-fitnix-off-white">
              Admin <span className="fitnix-gradient-text">Dashboard</span>
            </h1>
            <p className="text-fitnix-off-white/70 mt-2 text-lg">
              Welcome back! Here's what's happening at your gym today.
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <div className="text-sm text-fitnix-off-white/60">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-fitnix-charcoal border border-fitnix-lime text-fitnix-off-white px-6 py-4 rounded-xl">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {error}
            </div>
          </div>
        )}

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {metricCards.map((metric, index) => {
            const isOverdue = index === 1
            return (
            <div 
              key={index} 
              className={`fitnix-card-glow border-2 ${metric.borderColor} transform hover:scale-105 transition-all duration-300 relative rounded-2xl`}
              onMouseEnter={(e) => {
                if (isOverdue) {
                  e.currentTarget.style.boxShadow = '0 0 12px rgba(255, 59, 48, 0.3), 0 0 24px rgba(255, 59, 48, 0.15)'
                } else {
                  e.currentTarget.style.boxShadow = '0 0 12px rgba(182, 255, 0, 0.3), 0 0 24px rgba(182, 255, 0, 0.15)'
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              {/* Gradient mesh overlay */}
              <div className="absolute inset-0 bg-gradient-mesh opacity-30 pointer-events-none rounded-2xl"></div>
              
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-6">
                  <div className={`w-16 h-16 ${metric.iconBg} rounded-xl flex items-center justify-center ${metric.iconColor} shadow-lg`}>
                    {metric.icon}
                  </div>
                </div>
                
                <div className="space-y-2">
                  <p className={`text-3xl sm:text-4xl md:text-5xl font-extrabold ${metric.accentColor}`}>{metric.value}</p>
                  <p className="text-fitnix-off-white/80 text-sm sm:text-base font-semibold">{metric.title}</p>
                </div>
              </div>
            </div>
            )
          })}
        </div>

        {/* Recent Activity */}
        <div className="fitnix-card-glow">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-fitnix-off-white">Recent Activity</h2>
            <div className="flex items-center space-x-2 bg-fitnix-black px-4 py-2 rounded-full border-2 border-fitnix-lime/20">
              <div className="w-2 h-2 bg-fitnix-lime rounded-full animate-pulse"></div>
              <span className="text-fitnix-lime text-sm font-bold uppercase tracking-wide">Live</span>
            </div>
          </div>
          
          <div className="space-y-3">
            {recentActivities.length === 0 ? (
              <div className="text-center py-16">
                <div className="flex flex-col items-center justify-center space-y-4">
                  <div className="w-24 h-24 bg-gradient-to-br from-fitnix-charcoal to-fitnix-black rounded-full flex items-center justify-center border-2 border-fitnix-lime/20">
                    <svg className="w-12 h-12 text-fitnix-lime/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-fitnix-off-white/60 text-xl font-semibold">No recent activity</p>
                  <p className="text-fitnix-off-white/40 text-sm">Activity will appear here as it happens</p>
                </div>
              </div>
            ) : (
              recentActivities.map((activity, index) => (
                <div 
                  key={index} 
                  className="group flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-4 sm:p-5 bg-fitnix-charcoal/40 backdrop-blur-lg rounded-xl hover:bg-fitnix-charcoal/60 transition-all duration-300 border border-fitnix-lime/10 hover:border-fitnix-lime/30 hover:shadow-lg transform hover:scale-[1.02]"
                >
                  {/* Icon with gradient background */}
                  <div className={`relative w-12 h-12 sm:w-14 sm:h-14 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    activity.icon === 'user' 
                      ? 'bg-gradient-to-br from-fitnix-lime to-fitnix-dark-lime' 
                      : 'bg-gradient-to-br from-cyan-500 to-cyan-700'
                  } shadow-lg`}>
                    {activity.icon === 'user' ? (
                      <svg className="w-7 h-7 text-fitnix-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    ) : (
                      <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                    )}
                    {/* Subtle glow effect */}
                    <div className={`absolute inset-0 rounded-xl ${
                      activity.icon === 'user' 
                        ? 'bg-fitnix-lime' 
                        : 'bg-cyan-500'
                    } opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-200`}></div>
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-fitnix-off-white font-semibold text-sm sm:text-base truncate group-hover:text-fitnix-lime transition-colors">
                      {activity.title}
                    </p>
                    <p className="text-fitnix-off-white/60 text-xs sm:text-sm truncate mt-0.5">
                      {activity.description}
                    </p>
                  </div>
                  
                  {/* Timestamp */}
                  <div className="flex items-center space-x-2 flex-shrink-0 sm:ml-auto">
                    <div className="text-fitnix-off-white/40 text-xs sm:text-sm font-medium whitespace-nowrap bg-fitnix-black px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg">
                      {getTimeAgo(activity.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}
