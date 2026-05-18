import { useState, useEffect, useRef } from 'react';
import Pusher from 'pusher-js';
import { toast, Toaster } from 'sonner';
import AdminLayout from '../../components/layouts/AdminLayout';
import { 
  Activity, 
  Users, 
  UserCheck, 
  Clock, 
  Building2, 
  TrendingUp, 
  ClipboardList, 
  CheckCircle2,
  XCircle,
  BarChart3,
  Timer
} from 'lucide-react';

const AdminAttendance = () => {
  const [summary, setSummary] = useState({ today_checkins: 0, members_inside: 0, trainers_inside: 0, avg_stay_today: 0 });
  const [currentlyInside, setCurrentlyInside] = useState({ members: [], trainers: [] });
  const [dailySummary, setDailySummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deviceStatus, setDeviceStatus] = useState({ connected: false, service_running: false });
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const pusherRef = useRef(null);
  const channelRef = useRef(null);

  const convertToPKT = (utcTimeString) => {
    if (!utcTimeString) return 'Unknown time';
    
    try {
      const date = new Date(utcTimeString);
      date.setHours(date.getHours() - 5);
      
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
    } catch (error) {
      console.error('Error converting time:', error);
      return 'Invalid time';
    }
  };

  // Custom toast for check-in with rich member details and profile picture
  const showCheckInToast = (data) => {
    const time = convertToPKT(data.timestamp);
    const personType = data.person_type.charAt(0).toUpperCase() + data.person_type.slice(1);
    
    // Determine status color and text
    let statusColor = '#B6FF00'; // Green
    let statusText = 'Active';
    let statusBg = 'rgba(182, 255, 0, 0.1)';
    
    if (data.person_type === 'member' && data.days_until_expiry !== undefined) {
      const daysLeft = data.days_until_expiry;
      
      if (daysLeft < 0) {
        statusColor = '#ef4444'; // Red
        statusText = `Expired ${Math.abs(daysLeft)} days ago`;
        statusBg = 'rgba(239, 68, 68, 0.1)';
      } else if (daysLeft === 0) {
        statusColor = '#f59e0b'; // Orange
        statusText = 'Expires Today';
        statusBg = 'rgba(245, 158, 11, 0.1)';
      } else if (daysLeft === 1) {
        statusColor = '#f59e0b';
        statusText = 'Expires Tomorrow';
        statusBg = 'rgba(245, 158, 11, 0.1)';
      } else if (daysLeft <= 3) {
        statusColor = '#f59e0b';
        statusText = `${daysLeft} days remaining`;
        statusBg = 'rgba(245, 158, 11, 0.1)';
      } else if (daysLeft <= 7) {
        statusColor = '#f59e0b';
        statusText = `${daysLeft} days remaining`;
        statusBg = 'rgba(245, 158, 11, 0.1)';
      } else {
        statusText = `${daysLeft} days remaining`;
      }
    }
    
    // Format dates
    const formatDate = (dateString) => {
      if (!dateString) return null;
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      });
    };
    
    // Create custom toast content with profile picture and detailed info
    const toastContent = (
      <div className="flex items-start gap-3 p-2">
        {/* Profile Picture */}
        <div className="flex-shrink-0">
          {data.profile_picture ? (
            <img 
              src={data.profile_picture} 
              alt={data.person_name}
              className="w-16 h-16 rounded-full object-cover border-3"
              style={{ borderColor: statusColor }}
            />
          ) : (
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-black border-3"
              style={{ 
                borderColor: statusColor,
                background: statusBg,
                color: statusColor
              }}
            >
              {data.person_name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        {/* Member Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-black text-lg text-white truncate leading-tight">
              {data.person_name}
            </h3>
            <span 
              className="px-3 py-1 rounded-full text-xs font-black whitespace-nowrap"
              style={{ 
                background: statusBg,
                color: statusColor,
                border: `2px solid ${statusColor}`
              }}
            >
              CHECK-IN
            </span>
          </div>
          
          <div className="space-y-1.5 text-xs">
            {/* Type and Time */}
            <div className="flex items-center gap-2 text-gray-400">
              <span className="font-bold">{personType}</span>
              <span>•</span>
              <span className="font-semibold">{time}</span>
            </div>
            
            {data.person_type === 'member' && (
              <>
                {/* Member Number */}
                {data.member_number && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Member ID:</span>
                    <span className="text-white font-bold">#{data.member_number}</span>
                  </div>
                )}
                
                {/* Phone */}
                {data.phone && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Phone:</span>
                    <span className="text-gray-300 font-semibold">{data.phone}</span>
                  </div>
                )}
                
                {/* Divider */}
                {data.package_name && (
                  <div className="border-t border-gray-700 my-2"></div>
                )}
                
                {/* Package Name */}
                {data.package_name && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Package:</span>
                    <span className="text-white font-black">{data.package_name}</span>
                  </div>
                )}
                
                {/* Package Start Date */}
                {data.package_start_date && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Started:</span>
                    <span className="text-gray-300 font-semibold">{formatDate(data.package_start_date)}</span>
                  </div>
                )}
                
                {/* Package Expiry Date */}
                {data.package_expiry_date && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Expires:</span>
                    <span className="text-gray-300 font-semibold">{formatDate(data.package_expiry_date)}</span>
                  </div>
                )}
                
                {/* Package Duration */}
                {data.package_duration_days && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Duration:</span>
                    <span className="text-gray-300 font-semibold">{data.package_duration_days} days</span>
                  </div>
                )}
                
                {/* Status Badge */}
                {data.days_until_expiry !== undefined && (
                  <div 
                    className="flex items-center justify-between px-3 py-2 rounded-lg mt-2"
                    style={{ background: statusBg, border: `1px solid ${statusColor}` }}
                  >
                    <span className="text-gray-400 font-bold text-xs">Package Status:</span>
                    <span className="font-black text-sm" style={{ color: statusColor }}>
                      {statusText}
                    </span>
                  </div>
                )}
                
                {/* Frozen Status */}
                {data.is_frozen && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/30 mt-2">
                    <span className="text-blue-400 font-black text-xs">MEMBERSHIP FROZEN</span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
    
    // Show toast with appropriate styling
    if (data.package_status === 'expired') {
      toast.error(toastContent, {
        duration: 8000,
        style: {
          background: '#1a1a1a',
          border: '3px solid #ef4444',
          color: '#fff',
          padding: '16px',
          minWidth: '450px',
          borderRadius: '16px',
        },
      });
    } else if (data.package_status === 'expiring_soon' || data.package_status === 'expiring_this_week') {
      toast.warning(toastContent, {
        duration: 8000,
        style: {
          background: '#1a1a1a',
          border: '3px solid #f59e0b',
          color: '#fff',
          padding: '16px',
          minWidth: '450px',
          borderRadius: '16px',
        },
      });
    } else {
      toast.success(toastContent, {
        duration: 6000,
        style: {
          background: '#1a1a1a',
          border: '3px solid #B6FF00',
          color: '#fff',
          padding: '16px',
          minWidth: '450px',
          borderRadius: '16px',
        },
      });
    }
  };

  // Custom toast for check-out with duration and profile picture
  const showCheckOutToast = (data) => {
    const personType = data.person_type.charAt(0).toUpperCase() + data.person_type.slice(1);
    
    const hours = Math.floor(data.stay_duration / 60);
    const mins = data.stay_duration % 60;
    const duration = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
    
    // Determine status for members
    let statusText = null;
    let statusColor = '#3b82f6';
    let statusBg = 'rgba(59, 130, 246, 0.1)';
    
    if (data.person_type === 'member' && data.days_until_expiry !== undefined) {
      const daysLeft = data.days_until_expiry;
      
      if (daysLeft < 0) {
        statusText = `Expired ${Math.abs(daysLeft)} days ago`;
        statusColor = '#ef4444';
        statusBg = 'rgba(239, 68, 68, 0.1)';
      } else if (daysLeft <= 3) {
        statusText = `${daysLeft} days remaining`;
        statusColor = '#f59e0b';
        statusBg = 'rgba(245, 158, 11, 0.1)';
      } else if (daysLeft <= 7) {
        statusText = `${daysLeft} days remaining`;
      }
    }
    
    // Format dates
    const formatDate = (dateString) => {
      if (!dateString) return null;
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      });
    };
    
    // Create custom toast content
    const toastContent = (
      <div className="flex items-start gap-3 p-2">
        {/* Profile Picture */}
        <div className="flex-shrink-0">
          {data.profile_picture ? (
            <img 
              src={data.profile_picture} 
              alt={data.person_name}
              className="w-16 h-16 rounded-full object-cover border-3 border-blue-500"
            />
          ) : (
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center text-2xl font-black border-3 border-blue-500"
              style={{ 
                background: 'rgba(59, 130, 246, 0.1)',
                color: '#3b82f6'
              }}
            >
              {data.person_name.charAt(0).toUpperCase()}
            </div>
          )}
        </div>
        
        {/* Member Details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-black text-lg text-white truncate leading-tight">
              {data.person_name}
            </h3>
            <span 
              className="px-3 py-1 rounded-full text-xs font-black whitespace-nowrap"
              style={{ 
                background: 'rgba(59, 130, 246, 0.1)',
                color: '#3b82f6',
                border: '2px solid #3b82f6'
              }}
            >
              CHECK-OUT
            </span>
          </div>
          
          <div className="space-y-1.5 text-xs">
            {/* Type and Duration */}
            <div className="flex items-center gap-2 text-gray-400">
              <span className="font-bold">{personType}</span>
              <span>•</span>
              <span className="font-semibold">Workout: <span className="text-blue-400 font-black">{duration}</span></span>
            </div>
            
            {data.person_type === 'member' && (
              <>
                {/* Member Number */}
                {data.member_number && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Member ID:</span>
                    <span className="text-white font-bold">#{data.member_number}</span>
                  </div>
                )}
                
                {/* Divider */}
                {data.package_name && (
                  <div className="border-t border-gray-700 my-2"></div>
                )}
                
                {/* Package Name */}
                {data.package_name && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Package:</span>
                    <span className="text-white font-black">{data.package_name}</span>
                  </div>
                )}
                
                {/* Package Expiry Date */}
                {data.package_expiry_date && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 font-semibold min-w-[80px]">Expires:</span>
                    <span className="text-gray-300 font-semibold">{formatDate(data.package_expiry_date)}</span>
                  </div>
                )}
                
                {/* Status Badge */}
                {statusText && (
                  <div 
                    className="flex items-center justify-between px-3 py-2 rounded-lg mt-2"
                    style={{ background: statusBg, border: `1px solid ${statusColor}` }}
                  >
                    <span className="text-gray-400 font-bold text-xs">Package Status:</span>
                    <span className="font-black text-sm" style={{ color: statusColor }}>
                      {statusText}
                    </span>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
    
    toast.info(toastContent, {
      duration: 6000,
      style: {
        background: '#1a1a1a',
        border: '3px solid #3b82f6',
        color: '#fff',
        padding: '16px',
        minWidth: '450px',
        borderRadius: '16px',
      },
    });
  };

  useEffect(() => {
    fetchAllData();
    fetchDeviceStatus();
    
    // Initialize Pusher for real-time updates
    const initPusher = () => {
      try {
        // Initialize Pusher client with fallback transports for PythonAnywhere
        pusherRef.current = new Pusher('8f96a097d2f6d11c1a34', {
          cluster: 'mt1',
          encrypted: true,
          forceTLS: true,
          // Enable all transports for maximum compatibility
          enabledTransports: ['ws', 'wss', 'xhr_streaming', 'xhr_polling'],
          disabledTransports: [],
          // Connection timeout and retry settings
          activityTimeout: 120000, // 2 minutes
          pongTimeout: 30000, // 30 seconds
          unavailableTimeout: 10000, // 10 seconds
          // Enable stats for debugging
          enableStats: false,
          // Disable auth endpoint (we're using public channel)
          authEndpoint: null
        });

        // Subscribe to attendance updates channel
        channelRef.current = pusherRef.current.subscribe('attendance-updates');

        // Connection state handlers
        pusherRef.current.connection.bind('connected', () => {
          console.log('✓ Pusher connected successfully');
        });

        pusherRef.current.connection.bind('disconnected', () => {
          console.log('✗ Pusher disconnected - using polling fallback');
        });

        pusherRef.current.connection.bind('unavailable', () => {
          console.warn('⚠ Pusher unavailable - using polling fallback');
        });

        pusherRef.current.connection.bind('failed', () => {
          console.error('✗ Pusher connection failed - using polling fallback');
        });

        pusherRef.current.connection.bind('error', (err) => {
          console.error('Pusher connection error:', err);
        });

        // Channel subscription handlers
        channelRef.current.bind('pusher:subscription_succeeded', () => {
          console.log('✓ Successfully subscribed to attendance-updates channel');
        });

        channelRef.current.bind('pusher:subscription_error', (err) => {
          console.error('✗ Failed to subscribe to attendance-updates channel:', err);
        });

        // Listen for check-in events
        channelRef.current.bind('check-in', (data) => {
          console.log('✓ Check-in event received:', data);
          
          // Show custom rich toast notification
          showCheckInToast(data);

          // Refresh data
          fetchAllData();
          setLastUpdate(new Date());
        });

        // Listen for check-out events
        channelRef.current.bind('check-out', (data) => {
          console.log('✓ Check-out event received:', data);
          
          // Show custom rich toast notification
          showCheckOutToast(data);

          // Refresh data
          fetchAllData();
          setLastUpdate(new Date());
        });

        console.log('✓ Pusher initialized and subscribed to attendance-updates');
      } catch (error) {
        console.error('Failed to initialize Pusher:', error);
      }
    };

    initPusher();
    
    // Aggressive polling every 10 seconds (Pusher fallback)
    const pollingInterval = setInterval(() => {
      fetchAllData();
      fetchDeviceStatus();
      setLastUpdate(new Date());
    }, 10000); // 10 seconds for real-time feel
    
    // Cleanup on unmount
    return () => {
      clearInterval(pollingInterval);
      if (channelRef.current) {
        try {
          channelRef.current.unbind_all();
          pusherRef.current.unsubscribe('attendance-updates');
        } catch (e) {
          console.log('Cleanup error (ignored):', e);
        }
      }
      if (pusherRef.current) {
        try {
          pusherRef.current.disconnect();
        } catch (e) {
          console.log('Disconnect error (ignored):', e);
        }
      }
    };
  }, []);

  const fetchAllData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [summaryRes, liveRes, dailyRes] = await Promise.all([
        fetch('/api/attendance/dashboard/summary', { headers }),
        fetch('/api/attendance/live', { headers }),
        fetch('/api/attendance/daily-summary', { headers })
      ]);
      
      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
        console.log('✓ Summary loaded:', summaryData);
      }
      
      if (liveRes.ok) {
        const liveData = await liveRes.json();
        setCurrentlyInside(liveData);
        console.log('✓ Live data loaded:', liveData);
      }
      
      if (dailyRes.ok) {
        const dailyData = await dailyRes.json();
        // Handle both formats: direct array or wrapped in summaries
        const summaries = Array.isArray(dailyData) ? dailyData : (dailyData.summaries || []);
        setDailySummary(summaries);
        console.log('✓ Daily summary loaded:', summaries);
      }
      
      setLoading(false);
    } catch (err) { 
      console.error('Error fetching data:', err); 
      setLoading(false); 
    }
  };

  const fetchDeviceStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const res = await fetch('/api/attendance/health', { headers });
      if (res.ok) {
        const data = await res.json();
        setDeviceStatus({ 
          connected: data.device_connected || false, 
          service_running: data.service_running || false 
        });
      } else {
        setDeviceStatus({ connected: false, service_running: false });
      }
    } catch (err) { 
      console.error('Device status fetch error:', err); 
      setDeviceStatus({ connected: false, service_running: false });
    }
  };

  if (loading) return (
    <AdminLayout>
      <div className="flex items-center justify-center min-h-screen bg-fitnix-black">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-fitnix-lime mb-4"></div>
          <p className="text-fitnix-lime text-xl font-bold">Loading Dashboard...</p>
        </div>
      </div>
    </AdminLayout>
  );

  return (
    <AdminLayout>
    <Toaster 
      position="top-right" 
      richColors={false}
      expand={true}
      toastOptions={{
        unstyled: true,
        classNames: {
          toast: 'custom-toast-wrapper',
        },
      }}
    />
    <div className="p-6 md:p-8 bg-fitnix-black min-h-screen text-fitnix-off-white">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="text-4xl md:text-5xl font-extrabold text-fitnix-off-white tracking-tight flex items-center gap-3">
              <Activity className="w-10 h-10 text-fitnix-lime" strokeWidth={2.5} />
              Attendance <span className="fitnix-gradient-text">Dashboard</span>
            </h1>
            <p className="text-fitnix-off-white/70 mt-2 text-lg">
              Real-time tracking and analytics
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className={`px-4 py-2 rounded-lg border-2 transition-all duration-300 ${
              deviceStatus.connected 
                ? 'bg-fitnix-lime/10 border-fitnix-lime/30 text-fitnix-lime' 
                : 'bg-red-500/10 border-red-500/30 text-red-400'
            }`}>
              <div className="flex items-center gap-2">
                <span className={`inline-block w-2 h-2 rounded-full ${deviceStatus.connected ? 'bg-fitnix-lime animate-pulse' : 'bg-red-500'}`}></span>
                <span className="text-sm font-bold">Device {deviceStatus.connected ? 'Online' : 'Offline'}</span>
              </div>
            </div>
            <div className="px-4 py-2 rounded-lg border-2 border-fitnix-charcoal bg-fitnix-charcoal/40">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-fitnix-off-white/60" />
                <span className="text-xs font-medium text-fitnix-off-white/60">
                  {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards - Only Today's Check-ins */}
        <div className="grid grid-cols-1 gap-6 mb-8">
          {[
            { label: "Today's Check-ins", value: summary.today_checkins, Icon: BarChart3, gradient: "from-blue-500 to-cyan-500" }
          ].map((stat, idx) => (
            <div key={idx} className="group relative">
              <div className={`absolute -inset-0.5 bg-gradient-to-r ${stat.gradient} rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-300`}></div>
              <div className="relative bg-fitnix-charcoal border-2 border-fitnix-charcoal hover:border-fitnix-lime/30 p-6 rounded-xl transition-all duration-300 transform hover:scale-105">
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-fitnix-off-white/70 text-xs font-bold uppercase tracking-wider">{stat.label}</h3>
                  <stat.Icon className="w-8 h-8 text-fitnix-lime/80" strokeWidth={2} />
                </div>
                <p className="text-5xl font-extrabold fitnix-gradient-text">
                  {stat.value}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Today's Summary Table - Simplified */}
        <div className="fitnix-card-glow mb-8">
          <h2 className="text-2xl font-bold text-fitnix-off-white mb-5 flex items-center gap-2">
            <ClipboardList className="w-7 h-7 text-fitnix-lime" strokeWidth={2.5} />
            Today's Attendance Summary
          </h2>
          <div className="overflow-x-auto rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-fitnix-charcoal/60 border-b-2 border-fitnix-lime/30">
                <tr>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Name</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Type</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Status</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Check-In</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Payment Status</th>
                </tr>
              </thead>
              <tbody>
                {dailySummary && dailySummary.length > 0 ? (
                  dailySummary.map(record => (
                    <tr key={record.id} className="border-b border-fitnix-charcoal hover:bg-fitnix-charcoal/40 transition-colors">
                      <td className="px-4 py-4 text-fitnix-off-white font-bold text-sm">{record.person_name || record.person_id}</td>
                      <td className="px-4 py-4 text-fitnix-off-white/70 capitalize font-medium">{record.person_type}</td>
                      <td className="px-4 py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit border ${
                          record.status === 'Present' 
                            ? 'bg-fitnix-lime/20 text-fitnix-lime border-fitnix-lime/30' 
                            : 'bg-red-500/20 text-red-400 border-red-500/30'
                        }`}>
                          {record.status === 'Present' ? (
                            <CheckCircle2 className="w-3.5 h-3.5" strokeWidth={2.5} />
                          ) : (
                            <XCircle className="w-3.5 h-3.5" strokeWidth={2.5} />
                          )}
                          {record.status}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-fitnix-off-white/70 font-medium">{record.first_check_in ? convertToPKT(record.first_check_in) : '-'}</td>
                      <td className="px-4 py-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1.5 w-fit border ${
                          record.payment_status === 'COMPLETED' || record.payment_status === 'Paid'
                            ? 'bg-green-500/20 text-green-400 border-green-500/30' 
                            : record.payment_status === 'PENDING'
                            ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                            : 'bg-red-500/20 text-red-400 border-red-500/30'
                        }`}>
                          {record.payment_status || 'N/A'}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-4 py-16 text-center">
                      <ClipboardList className="w-16 h-16 text-fitnix-charcoal mx-auto mb-4" strokeWidth={2} />
                      <p className="text-fitnix-off-white/60 text-base font-semibold">No attendance records for today</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    {/* Custom Scrollbar and Toast Styles */}
    <style>{`
      .custom-scrollbar::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }
      .custom-scrollbar::-webkit-scrollbar-track {
        background: #1a1a1a;
        border-radius: 10px;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #B6FF00;
        border-radius: 10px;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #9FE000;
      }
      
      /* Custom Toast Wrapper */
      .custom-toast-wrapper {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
      }
      
      /* Custom Toast Animations */
      .custom-toast-wrapper > div {
        animation: slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        border-radius: 16px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
      }
      
      @keyframes slideInRight {
        from {
          transform: translateX(120%) scale(0.9);
          opacity: 0;
        }
        to {
          transform: translateX(0) scale(1);
          opacity: 1;
        }
      }
      
      /* Responsive toast width */
      @media (max-width: 640px) {
        .custom-toast-wrapper > div {
          min-width: 340px !important;
          max-width: calc(100vw - 24px) !important;
          font-size: 11px !important;
        }
        
        .custom-toast-wrapper img,
        .custom-toast-wrapper > div > div > div:first-child > div {
          width: 48px !important;
          height: 48px !important;
        }
      }
    `}</style>
    </AdminLayout>
  );
};

export default AdminAttendance;
