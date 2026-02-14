import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Line, Bar, Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import apiClient from '../../services/api'
import AdminLayout from '../../components/layouts/AdminLayout'
import logo from '/fitcore-logo.png'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

export default function AdminAnalytics() {
  const [revenue, setRevenue] = useState(null)
  const [revenueTrend, setRevenueTrend] = useState(null)
  const [memberGrowth, setMemberGrowth] = useState(null)
  const [members, setMembers] = useState([])
  const [packages, setPackages] = useState([])
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      const results = await Promise.allSettled([
        apiClient.get('/admin/dashboard/revenue-projection'),
        apiClient.get('/admin/dashboard/revenue-trend'),
        apiClient.get('/admin/dashboard/member-growth'),
        apiClient.get('/admin/members'),
        apiClient.get('/packages'),
        apiClient.get('/admin/finance/member-payments-fixed')
      ])

      if (results[0].status === 'fulfilled') setRevenue(results[0].value.data)
      if (results[1].status === 'fulfilled') setRevenueTrend(results[1].value.data)
      if (results[2].status === 'fulfilled') setMemberGrowth(results[2].value.data)
      if (results[3].status === 'fulfilled') setMembers(results[3].value.data.members || [])
      if (results[4].status === 'fulfilled') setPackages(results[4].value.data.packages || [])
      if (results[5].status === 'fulfilled') setTransactions(results[5].value.data.payments || [])

      if (results[0].status === 'rejected') {
        setError('Failed to load some analytics data')
      }
    } catch (err) {
      setError('Failed to load analytics')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const calculateMRRGrowth = () => {
    if (!revenueTrend || revenueTrend.revenue.length < 2) return 0
    const currentMonth = revenueTrend.revenue[revenueTrend.revenue.length - 1]
    const previousMonth = revenueTrend.revenue[revenueTrend.revenue.length - 2]
    if (previousMonth === 0) return 0
    const growth = ((currentMonth - previousMonth) / previousMonth) * 100
    return growth.toFixed(1)
  }

  const calculateARPM = () => {
    if (!revenue || !revenue.active_packages_count || revenue.active_packages_count === 0) return 0
    return (revenue.projected_monthly_revenue / revenue.active_packages_count).toFixed(0)
  }

  const calculateRetentionRate = () => {
    if (!memberGrowth || !memberGrowth.counts || memberGrowth.counts.length === 0) return 0
    const currentActive = memberGrowth.counts[memberGrowth.counts.length - 1]
    const previousActive = memberGrowth.counts[memberGrowth.counts.length - 2] || currentActive
    if (previousActive === 0) return 100
    const retention = (currentActive / previousActive) * 100
    return Math.min(retention, 100).toFixed(1)
  }

  const getTotalActiveMembers = () => {
    if (!members || members.length === 0) return 0
    return members.filter(m => !m.is_frozen).length
  }

  const getCompletedPaymentsThisMonth = () => {
    if (!transactions || transactions.length === 0) return 0
    const now = new Date()
    const currentMonth = now.getMonth()
    const currentYear = now.getFullYear()
    
    return transactions.filter(t => {
      if (t.status !== 'COMPLETED' || !t.paid_date) return false
      const paidDate = new Date(t.paid_date)
      return paidDate.getMonth() === currentMonth && paidDate.getFullYear() === currentYear
    }).length
  }

  const getTotalCompletedPaymentsAmount = () => {
    if (!transactions || transactions.length === 0) return 0
    const now = new Date()
    const currentMonth = now.getMonth()
    const currentYear = now.getFullYear()
    
    return transactions
      .filter(t => {
        if (t.status !== 'COMPLETED' || !t.paid_date) return false
        const paidDate = new Date(t.paid_date)
        return paidDate.getMonth() === currentMonth && paidDate.getFullYear() === currentYear
      })
      .reduce((sum, t) => sum + (t.amount || 0), 0)
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: '#F5F5F5',
          font: { size: 12 }
        }
      },
      tooltip: {
        backgroundColor: '#1A1A1A',
        titleColor: '#B6FF00',
        bodyColor: '#F5F5F5',
        borderColor: '#B6FF00',
        borderWidth: 1
      }
    },
    scales: {
      x: {
        ticks: { color: '#F5F5F5' },
        grid: { color: '#2A2A2A' }
      },
      y: {
        ticks: { color: '#F5F5F5' },
        grid: { color: '#2A2A2A' }
      }
    }
  }

  const getRevenueChartData = () => {
    if (!revenueTrend) {
      return {
        labels: [],
        datasets: [{
          label: 'Revenue (Rs.)',
          data: [],
          borderColor: '#B6FF00',
          backgroundColor: 'rgba(182, 255, 0, 0.1)',
          fill: true,
          tension: 0.4
        }]
      }
    }
    return {
      labels: revenueTrend.months,
      datasets: [{
        label: 'Revenue (Rs.)',
        data: revenueTrend.revenue,
        borderColor: '#B6FF00',
        backgroundColor: 'rgba(182, 255, 0, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#B6FF00',
        pointBorderColor: '#0B0B0B',
        pointBorderWidth: 2,
        pointRadius: 5,
        pointHoverRadius: 7
      }]
    }
  }

  const getPackageDistributionData = () => {
    if (!members || members.length === 0) {
      return {
        labels: ['No Members'],
        datasets: [{
          data: [1],
          backgroundColor: ['#2A2A2A'],
          borderColor: ['#3A3A3A'],
          borderWidth: 1
        }]
      }
    }

    // If no packages, show empty state
    if (!packages || packages.length === 0) {
      return {
        labels: ['No Packages'],
        datasets: [{
          data: [1],
          backgroundColor: ['#2A2A2A'],
          borderColor: ['#3A3A3A'],
          borderWidth: 1
        }]
      }
    }

    // Create a map of package IDs to package names
    const packageMap = {}
    packages.forEach(pkg => {
      packageMap[pkg.id] = pkg.name
    })

    // Count members by package
    const packageCounts = {}
    members.forEach(member => {
      if (member.current_package_id && packageMap[member.current_package_id]) {
        const packageName = packageMap[member.current_package_id]
        packageCounts[packageName] = (packageCounts[packageName] || 0) + 1
      }
    })

    // If no members have packages assigned, show empty state
    const labels = Object.keys(packageCounts)
    if (labels.length === 0) {
      return {
        labels: ['No Assignments'],
        datasets: [{
          data: [1],
          backgroundColor: ['#2A2A2A'],
          borderColor: ['#3A3A3A'],
          borderWidth: 1
        }]
      }
    }

    const data = Object.values(packageCounts)

    // Generate distinct colors dynamically
    const generateColors = (count) => {
      const colors = []
      const saturation = 70
      const lightness = 55
      
      for (let i = 0; i < count; i++) {
        const hue = (i * 360 / count) % 360
        colors.push(`hsl(${hue}, ${saturation}%, ${lightness}%)`)
      }
      
      return colors
    }

    return {
      labels,
      datasets: [{
        data,
        backgroundColor: generateColors(labels.length),
        borderColor: '#0B0B0B',
        borderWidth: 2
      }]
    }
  }

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

  const mrrGrowth = calculateMRRGrowth()
  const arpm = calculateARPM()
  const retentionRate = calculateRetentionRate()

  return (
    <AdminLayout onLogout={handleLogout}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-fitnix-off-white">
            Analytics <span className="fitnix-gradient-text">Dashboard</span>
          </h1>
          <p className="text-fitnix-off-white/60 mt-2">
            Real-time insights and performance metrics
          </p>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500 text-fitnix-off-white px-4 py-3 rounded-xl">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {error}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {revenue && (
            <div className="fitnix-card-glow border-2 border-fitnix-lime/20 hover:border-fitnix-lime/40 hover:shadow-[0_0_20px_rgba(182,255,0,0.3)] transform hover:scale-105 transition-all duration-300">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-fitnix-off-white/60 text-sm font-semibold mb-2 uppercase tracking-wide">
                    Monthly Recurring Revenue
                  </h3>
                  <p className="text-2xl sm:text-3xl font-bold text-fitnix-lime">
                    Rs. {revenue.projected_monthly_revenue?.toLocaleString() || 0}
                  </p>
                  <p className="text-fitnix-off-white/60 text-xs mt-2">
                    {revenue.active_packages_count || 0} active members
                  </p>
                </div>
                <div className="p-3 bg-fitnix-lime/10 rounded-lg">
                  <svg className="w-6 h-6 text-fitnix-lime" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>
          )}

          <div className="fitnix-card-glow border-2 border-cyan-500/20 hover:border-cyan-600/40 hover:shadow-neon-cyan transform hover:scale-105 transition-all duration-300">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-fitnix-off-white/60 text-sm font-semibold mb-2 uppercase tracking-wide">
                  Total Active Members
                </h3>
                <p className="text-2xl sm:text-3xl font-bold text-cyan-400">
                  {getTotalActiveMembers()}
                </p>
                <p className="text-fitnix-off-white/60 text-xs mt-2">
                  active members
                </p>
              </div>
              <div className="p-3 bg-cyan-500/10 rounded-lg">
                <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="fitnix-card-glow border-2 border-green-500/20 hover:border-green-600/40 hover:shadow-[0_0_20px_rgba(34,197,94,0.3)] transform hover:scale-105 transition-all duration-300">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-fitnix-off-white/60 text-sm font-semibold mb-2 uppercase tracking-wide">
                  Completed Payments (This Month)
                </h3>
                <p className="text-2xl sm:text-3xl font-bold text-green-400">
                  Rs. {getTotalCompletedPaymentsAmount().toLocaleString()}
                </p>
                <p className="text-fitnix-off-white/60 text-xs mt-2">
                  {getCompletedPaymentsThisMonth()} payments
                </p>
              </div>
              <div className="p-3 bg-green-500/10 rounded-lg">
                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="fitnix-card-glow backdrop-blur-xl">
            <h2 className="text-lg sm:text-xl font-semibold text-fitnix-off-white mb-4">Revenue Trend</h2>
            <div className="h-48 sm:h-64">
              <Line data={getRevenueChartData()} options={chartOptions} />
            </div>
          </div>

          <div className="fitnix-card-glow backdrop-blur-xl">
            <h2 className="text-lg sm:text-xl font-semibold text-fitnix-off-white mb-4">Package Distribution</h2>
            <p className="text-fitnix-off-white/60 text-xs sm:text-sm mb-4">
              Member distribution across packages
            </p>
            <div className="h-48 sm:h-64 flex items-center justify-center">
              <div className="w-48 h-48 sm:w-64 sm:h-64">
                <Doughnut 
                  data={getPackageDistributionData()} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: {
                          color: '#F5F5F5',
                          font: { size: 12 },
                          padding: 15
                        }
                      },
                      tooltip: {
                        backgroundColor: '#1A1A1A',
                        titleColor: '#B6FF00',
                        bodyColor: '#F5F5F5',
                        borderColor: '#B6FF00',
                        borderWidth: 1
                      }
                    }
                  }} 
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  )
}
