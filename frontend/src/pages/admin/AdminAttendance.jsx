import { useState, useEffect, useRef } from 'react';
import Pusher from 'pusher-js';
import { toast, Toaster } from 'sonner';
import AdminLayout from '../../components/layouts/AdminLayout';
import { 
  Activity, 
  Users, 
  UserCheck, 
  Clock, 
  Zap, 
  Building2, 
  TrendingUp, 
  ClipboardList, 
  CheckCircle2,
  XCircle,
  BarChart3,
  Timer,
  ChevronDown,
  ChevronUp,
  Search,
  Calendar
} from 'lucide-react';

const AdminAttendance = () => {
  const [summary, setSummary] = useState({ today_checkins: 0, members_inside: 0, trainers_inside: 0, avg_stay_today: 0 });
  const [liveEvents, setLiveEvents] = useState([]);
  const [currentlyInside, setCurrentlyInside] = useState({ members: [], trainers: [] });
  const [monthlyRecords, setMonthlyRecords] = useState([]);
  const [monthlyRecordsMonth, setMonthlyRecordsMonth] = useState('');
  const [weeklyData, setWeeklyData] = useState([]);
  const [dailySummary, setDailySummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deviceStatus, setDeviceStatus] = useState({ connected: false, service_running: false });
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [isMonthlyExpanded, setIsMonthlyExpanded] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
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
        // Initialize Pusher client
        pusherRef.current = new Pusher('8f96a097d2f6d11c1a34', {
          cluster: 'mt1',
          encrypted: true
        });

        // Subscribe to attendance updates channel
        channelRef.current = pusherRef.current.subscribe('attendance-updates');

        // Connection state handlers
        pusherRef.current.connection.bind('connected', () => {
          console.log('✓ Pusher connected');
        });

        pusherRef.current.connection.bind('disconnected', () => {
          console.log('✗ Pusher disconnected');
        });

        pusherRef.current.connection.bind('error', (err) => {
          console.error('Pusher connection error:', err);
        });

        // Listen for check-in events
        channelRef.current.bind('check-in', (data) => {
          console.log('Check-in event received:', data);
          
          // Show custom rich toast notification
          showCheckInToast(data);

          // Refresh data
          fetchAllData();
          setLastUpdate(new Date());
        });

        // Listen for check-out events
        channelRef.current.bind('check-out', (data) => {
          console.log('Check-out event received:', data);
          
          // Show custom rich toast notification
          showCheckOutToast(data);

          // Refresh data
          fetchAllData();
          setLastUpdate(new Date());
        });

        console.log('Pusher initialized and subscribed to attendance-updates');
      } catch (error) {
        console.error('Failed to initialize Pusher:', error);
        setPusherConnected(false);
      }
    };

    initPusher();
    
    // Fallback polling every 60 seconds (in case Pusher fails)
    const pollingInterval = setInterval(() => {
      fetchAllData();
      fetchDeviceStatus();
      setLastUpdate(new Date());
    }, 60000); // 60 seconds
    
    // Cleanup on unmount
    return () => {
      clearInterval(pollingInterval);
      if (channelRef.current) {
        channelRef.current.unbind_all();
        pusherRef.current.unsubscribe('attendance-updates');
      }
      if (pusherRef.current) {
        pusherRef.current.disconnect();
      }
    };
  }, []);

  // Refetch monthly records when search query changes
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      if (!loading) {
        const token = localStorage.getItem('token');
        fetch(`/api/attendance/analytics/monthly-records?search=${encodeURIComponent(searchQuery)}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              setMonthlyRecords(data.records || []);
              setMonthlyRecordsMonth(data.month || '');
            }
          })
          .catch(err => console.error(err));
      }
    }, 300);
    
    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  const fetchAllData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      const [summaryRes, monthlyRes, liveRes, weeklyRes, dailyRes] = await Promise.all([
        fetch('/api/attendance/dashboard/summary', { headers }),
        fetch(`/api/attendance/analytics/monthly-records?search=${encodeURIComponent(searchQuery)}`, { headers }),
        fetch('/api/attendance/live', { headers }),
        fetch('/api/attendance/analytics/weekly', { headers }),
        fetch('/api/attendance/daily-summary', { headers })
      ]);
      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (monthlyRes.ok) {
        const data = await monthlyRes.json();
        setMonthlyRecords(data.records || []);
        setMonthlyRecordsMonth(data.month || '');
      }
      if (liveRes.ok) {
        const liveData = await liveRes.json();
        setCurrentlyInside(liveData);
        setLiveEvents(liveData.recent_events || []);
      }
      if (weeklyRes.ok) setWeeklyData((await weeklyRes.json()).data || []);
      if (dailyRes.ok) setDailySummary((await dailyRes.json()).summaries || []);
      setLoading(false);
    } catch (err) { console.error(err); setLoading(false); }
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

        {/* Stats Cards - Simplified */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { label: "Today's Check-ins", value: summary.today_checkins, Icon: BarChart3, gradient: "from-blue-500 to-cyan-500" },
            { label: "Members Inside", value: summary.members_inside, Icon: Users, gradient: "from-fitnix-lime to-green-400" },
            { label: "Trainers Inside", value: summary.trainers_inside, Icon: UserCheck, gradient: "from-purple-500 to-pink-500" },
            { label: "Avg Stay Today", value: summary.avg_stay_formatted || '0h 0m', Icon: Timer, gradient: "from-orange-500 to-red-500" }
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

        {/* Live Feed & Currently Inside - Simplified */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Live Activity Feed */}
          <div className="fitnix-card-glow">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-2xl font-bold text-fitnix-off-white flex items-center gap-2">
                <Zap className="w-6 h-6 text-fitnix-lime" strokeWidth={2.5} />
                Live Activity
              </h2>
              <div className="flex items-center space-x-2 bg-fitnix-black px-3 py-1.5 rounded-full border-2 border-fitnix-lime/20">
                <div className="w-2 h-2 bg-fitnix-lime rounded-full animate-pulse"></div>
                <span className="text-fitnix-lime text-xs font-bold uppercase tracking-wide">Live</span>
              </div>
            </div>
            <div className="space-y-2 h-[400px] overflow-y-auto custom-scrollbar">
              {liveEvents.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center">
                  <Activity className="w-16 h-16 text-fitnix-charcoal mb-3" strokeWidth={2} />
                  <p className="text-fitnix-off-white/60 font-semibold text-sm">No recent activity</p>
                </div>
              ) : (
                liveEvents.map((event, idx) => (
                  <div key={`${event.id}-${idx}`} className="p-3 bg-fitnix-charcoal/40 rounded-lg border border-fitnix-lime/10 hover:border-fitnix-lime/30 transition-all duration-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold text-fitnix-off-white text-sm">{event.person_name}</p>
                        <p className="text-xs text-fitnix-lime capitalize font-semibold mt-0.5">{event.person_type} • {event.status}</p>
                      </div>
                      {event.status.includes('Check-In') ? (
                        <CheckCircle2 className="w-4 h-4 text-fitnix-lime" strokeWidth={2.5} />
                      ) : (
                        <XCircle className="w-4 h-4 text-orange-400" strokeWidth={2.5} />
                      )}
                    </div>
                    <p className="text-xs text-fitnix-off-white/50 mt-1 flex items-center gap-1 font-medium">
                      <Clock className="w-3 h-3" strokeWidth={2} />
                      {convertToPKT(event.timestamp)}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Currently Inside */}
          <div className="fitnix-card-glow">
            <h2 className="text-2xl font-bold text-fitnix-off-white mb-5 flex items-center gap-2">
              <Building2 className="w-6 h-6 text-purple-400" strokeWidth={2.5} />
              Currently Inside
            </h2>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-fitnix-lime text-base flex items-center gap-2">
                    <Users className="w-5 h-5" strokeWidth={2.5} />
                    Members
                  </h3>
                  <span className="px-3 py-1 bg-fitnix-lime/20 text-fitnix-lime text-sm font-bold rounded-full border border-fitnix-lime/30">
                    {currentlyInside.members?.length || 0}
                  </span>
                </div>
                <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                  {currentlyInside.members && currentlyInside.members.length > 0 ? (
                    currentlyInside.members.map(m => (
                      <div key={m.id} className="p-3 bg-fitnix-charcoal/40 rounded-lg hover:bg-fitnix-charcoal/60 transition-colors border border-fitnix-charcoal hover:border-fitnix-lime/20">
                        <div className="flex justify-between items-center">
                          <p className="font-bold text-fitnix-off-white text-sm">{m.person_name || m.person_id}</p>
                          <span className="text-xs text-fitnix-lime font-bold flex items-center gap-1">
                            <Clock className="w-3 h-3" strokeWidth={2} />
                            {m.time_spent_formatted || `${m.time_spent_so_far} min`}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-fitnix-off-white/60 text-center py-3 font-medium">No members inside</p>
                  )}
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-purple-400 text-base flex items-center gap-2">
                    <UserCheck className="w-5 h-5" strokeWidth={2.5} />
                    Trainers
                  </h3>
                  <span className="px-3 py-1 bg-purple-500/20 text-purple-400 text-sm font-bold rounded-full border border-purple-500/30">
                    {currentlyInside.trainers?.length || 0}
                  </span>
                </div>
                <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                  {currentlyInside.trainers && currentlyInside.trainers.length > 0 ? (
                    currentlyInside.trainers.map(t => (
                      <div key={t.id} className="p-3 bg-fitnix-charcoal/40 rounded-lg hover:bg-fitnix-charcoal/60 transition-colors border border-fitnix-charcoal hover:border-purple-500/20">
                        <div className="flex justify-between items-center">
                          <p className="font-bold text-fitnix-off-white text-sm">{t.person_name || t.person_id}</p>
                          <span className="text-xs text-purple-400 font-bold flex items-center gap-1">
                            <Clock className="w-3 h-3" strokeWidth={2} />
                            {t.time_spent_formatted || `${t.time_spent_so_far} min`}
                          </span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-fitnix-off-white/60 text-center py-3 font-medium">No trainers inside</p>
                  )}
                </div>
              </div>
            </div>
          </div>
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
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">First Check-In</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Last Check-Out</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Total Time</th>
                  <th className="px-4 py-4 text-left text-fitnix-lime font-bold uppercase tracking-wide text-xs">Visits</th>
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
                      <td className="px-4 py-4 text-fitnix-off-white/70 font-medium">{record.last_check_out ? convertToPKT(record.last_check_out) : '-'}</td>
                      <td className="px-4 py-4 text-fitnix-off-white/70 font-medium">{record.total_time_minutes ? `${Math.floor(record.total_time_minutes / 60)}h ${record.total_time_minutes % 60}m` : '-'}</td>
                      <td className="px-4 py-4 text-fitnix-lime font-bold text-lg">{record.visit_count}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="px-4 py-16 text-center">
                      <ClipboardList className="w-16 h-16 text-fitnix-charcoal mx-auto mb-4" strokeWidth={2} />
                      <p className="text-fitnix-off-white/60 text-base font-semibold">No attendance records for today</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Weekly Analytics - Simplified */}
        <div className="fitnix-card-glow mb-8">
          <h2 className="text-2xl font-bold text-fitnix-off-white mb-6 flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-blue-400" strokeWidth={2.5} />
            Weekly Analytics
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-7 gap-4">
            {weeklyData && weeklyData.length > 0 ? (
              weeklyData.map((day, idx) => (
                <div key={idx} className="group/bar flex flex-col items-center">
                  <div className="flex flex-col items-center mb-2">
                    <span className="text-base font-bold text-fitnix-off-white/70 mb-1">{day.day ? day.day.substring(0, 3) : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][idx]}</span>
                    <span className="text-2xl font-extrabold fitnix-gradient-text">{day.count}</span>
                  </div>
                  <div className="bg-fitnix-charcoal rounded-full h-32 w-12 overflow-hidden border-2 border-fitnix-charcoal flex flex-col justify-end">
                    <div 
                      className="bg-gradient-to-t from-fitnix-lime to-green-400 rounded-full transition-all duration-1000 ease-out group-hover/bar:shadow-lg group-hover/bar:shadow-fitnix-lime/50 w-full" 
                      style={{ height: `${Math.min(100, (day.count / 50) * 100)}%` }}
                    >
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="col-span-7 text-center py-12">
                <BarChart3 className="w-20 h-20 text-fitnix-charcoal mx-auto mb-4" strokeWidth={2} />
                <p className="text-fitnix-off-white/60 font-semibold text-base">No data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Monthly Attendance Records - Simplified */}
        <div className="fitnix-card-glow">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Calendar className="w-7 h-7 text-purple-400" strokeWidth={2.5} />
              <div>
                <h2 className="text-2xl font-bold text-fitnix-off-white">Monthly Attendance Records</h2>
                <p className="text-fitnix-off-white/60 text-sm font-medium mt-0.5">{monthlyRecordsMonth}</p>
              </div>
            </div>
            <button
              onClick={() => setIsMonthlyExpanded(!isMonthlyExpanded)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-lg border border-purple-500/30 hover:border-purple-500/50 transition-all font-bold"
            >
              {isMonthlyExpanded ? (
                <>
                  <ChevronUp className="w-5 h-5" strokeWidth={2.5} />
                  Collapse
                </>
              ) : (
                <>
                  <ChevronDown className="w-5 h-5" strokeWidth={2.5} />
                  Expand
                </>
              )}
            </button>
          </div>

          {isMonthlyExpanded && (
            <>
              {/* Search Bar */}
              <div className="mb-5">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-fitnix-off-white/50" strokeWidth={2} />
                  <input
                    type="text"
                    placeholder="Search by name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 bg-fitnix-charcoal/60 border-2 border-fitnix-charcoal focus:border-purple-500/50 rounded-lg text-fitnix-off-white placeholder-fitnix-off-white/50 font-medium focus:outline-none transition-colors"
                  />
                </div>
              </div>

              {/* Table */}
              <div className="overflow-x-auto rounded-lg max-h-[600px] overflow-y-auto custom-scrollbar">
                <table className="w-full text-sm">
                  <thead className="bg-fitnix-charcoal/60 border-b-2 border-purple-500/30 sticky top-0 z-10">
                    <tr>
                      <th className="px-4 py-4 text-left text-purple-400 font-bold uppercase tracking-wide text-xs">Name</th>
                      <th className="px-4 py-4 text-left text-purple-400 font-bold uppercase tracking-wide text-xs">Type</th>
                      <th className="px-4 py-4 text-left text-purple-400 font-bold uppercase tracking-wide text-xs">Total Visits</th>
                      <th className="px-4 py-4 text-left text-purple-400 font-bold uppercase tracking-wide text-xs">Days Attended</th>
                      <th className="px-4 py-4 text-left text-purple-400 font-bold uppercase tracking-wide text-xs">Total Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyRecords && monthlyRecords.length > 0 ? (
                      monthlyRecords.map((record, idx) => (
                        <tr key={`${record.person_id}-${idx}`} className="border-b border-fitnix-charcoal hover:bg-fitnix-charcoal/40 transition-colors">
                          <td className="px-4 py-4 text-fitnix-off-white font-bold text-sm">{record.person_name}</td>
                          <td className="px-4 py-4 text-fitnix-off-white/70 capitalize font-medium">{record.person_type}</td>
                          <td className="px-4 py-4 text-purple-400 font-bold text-lg">{record.total_visits}</td>
                          <td className="px-4 py-4 text-fitnix-lime font-bold text-lg">{record.days_attended}</td>
                          <td className="px-4 py-4 text-fitnix-off-white/70 font-medium">{record.total_time_formatted}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" className="px-4 py-16 text-center">
                          <Calendar className="w-16 h-16 text-fitnix-charcoal mx-auto mb-4" strokeWidth={2} />
                          <p className="text-fitnix-off-white/60 text-base font-semibold">
                            {searchQuery ? 'No matching records found' : 'No attendance records for this month'}
                          </p>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
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
