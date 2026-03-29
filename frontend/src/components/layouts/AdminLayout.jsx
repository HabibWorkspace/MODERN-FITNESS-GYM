import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import logo from '/fitcore-logo.png'

export default function AdminLayout({ children, onLogout }) {
  const location = useLocation()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const navItems = [
    { 
      path: '/admin', 
      label: 'Dashboard', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    },
    { 
      path: '/admin/members', 
      label: 'Members', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
    { 
      path: '/admin/trainers', 
      label: 'Trainers', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    { 
      path: '/admin/packages', 
      label: 'Packages', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      )
    },
    { 
      path: '/admin/finance', 
      label: 'Finance', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    { 
      path: '/admin/analytics', 
      label: 'Analytics', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      )
    },
    { 
      path: '/admin/attendance', 
      label: 'Attendance', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
      )
    },
    { 
      path: '/admin/device-mappings', 
      label: 'Device Mappings', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4" />
        </svg>
      )
    },
    { 
      path: '/admin/settings', 
      label: 'Settings', 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-fitnix-black via-fitnix-charcoal to-fitnix-black">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-fitnix-charcoal/95 backdrop-blur-xl border-b border-fitnix-lime/10 z-50 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src={logo} alt="FitCore Logo" className="w-8 h-8 object-contain" />
            <div className="text-lg font-extrabold fitnix-gradient-text">FitCore</div>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="text-fitnix-off-white p-2 hover:bg-fitnix-lime/10 rounded-lg transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-fitnix-charcoal/95 backdrop-blur-xl border-r border-fitnix-lime/10 transition-all duration-300 z-50 
        ${isCollapsed ? 'w-20' : 'w-64'}
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="hidden lg:flex items-center justify-center p-4 border-b border-fitnix-lime/10">
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="absolute inset-0 bg-fitnix-lime/20 blur-lg rounded-full"></div>
                <img 
                  src={logo} 
                  alt="FitCore Logo" 
                  className="relative w-10 h-10 object-contain" 
                />
              </div>
              <div className="text-xl font-extrabold fitnix-gradient-text">
                FitCore
              </div>
            </div>
          )}
          {isCollapsed && (
            <div className="relative flex-shrink-0">
              <div className="absolute inset-0 bg-fitnix-lime/20 blur-lg rounded-full"></div>
              <img 
                src={logo} 
                alt="FitCore Logo" 
                className="relative w-12 h-12 object-contain" 
              />
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1 flex-1 overflow-y-auto mt-16 lg:mt-0">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                  isActive
                    ? 'bg-gradient-to-r from-fitnix-lime/20 to-fitnix-dark-lime/20 text-fitnix-lime border border-fitnix-lime/30'
                    : 'text-fitnix-off-white/70 hover:bg-fitnix-black/30 hover:text-fitnix-off-white border border-transparent hover:border-fitnix-lime/20'
                }`}
                title={isCollapsed ? item.label : ''}
              >
                <span className={isActive ? 'text-fitnix-lime' : 'text-fitnix-off-white/70 group-hover:text-fitnix-off-white transition-colors duration-200'}>
                  {item.icon}
                </span>
                {!isCollapsed && (
                  <span className="font-semibold">{item.label}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="p-3 border-t border-fitnix-lime/10 space-y-2">
          {/* Collapse Button - Desktop Only */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={`hidden lg:flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 w-full text-fitnix-off-white hover:bg-fitnix-lime/10 hover:text-fitnix-lime border border-transparent hover:border-fitnix-lime/20 group ${isCollapsed ? 'justify-center' : ''}`}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isCollapsed ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
              )}
            </svg>
            {!isCollapsed && (
              <span className="font-semibold">{isCollapsed ? 'Expand' : 'Collapse'}</span>
            )}
          </button>

          {/* Logout Button */}
          <button
            onClick={onLogout}
            className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 w-full text-red-400 hover:bg-red-500/5 hover:text-red-300 border border-transparent hover:border-red-500/20 group ${isCollapsed ? 'justify-center' : ''}`}
            title={isCollapsed ? 'Logout' : ''}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            {!isCollapsed && (
              <span className="font-semibold">Logout</span>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`transition-all duration-300 pt-16 lg:pt-0 ${isCollapsed ? 'lg:ml-20' : 'lg:ml-64'}`}>
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
