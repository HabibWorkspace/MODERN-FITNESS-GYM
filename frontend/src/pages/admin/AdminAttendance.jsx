import { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
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

  useEffect(() => {
    fetchAllData();
    fetchDeviceStatus();
    
    const interval = setInterval(() => {
      fetchAllData();
      fetchDeviceStatus();
      setLastUpdate(new Date());
    }, 3000);
    
    return () => clearInterval(interval);
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
    <Toaster position="top-right" richColors />
    <div className="p-6 md:p-8 bg-fitnix-black min-h-screen text-fitnix-off-white">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-10 gap-4">
          <div>
            <h1 className="text-4xl md:text-5xl font-black text-fitnix-off-white tracking-tight flex items-center gap-3">
              <Activity className="w-12 h-12 text-fitnix-lime" strokeWidth={3} />
              Attendance <span className="text-fitnix-lime">Dashboard</span>
            </h1>
            <p className="text-fitnix-gray mt-2 flex items-center gap-2 ml-16">
              <span className="inline-block w-2 h-2 bg-fitnix-lime rounded-full animate-pulse"></span>
              Real-time tracking • Auto-refreshes every 3s
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className={`px-5 py-3 rounded-xl border-2 transition-all duration-300 ${
              deviceStatus.connected 
                ? 'bg-fitnix-lime/10 border-fitnix-lime text-fitnix-lime' 
                : 'bg-red-500/10 border-red-500 text-red-400'
            }`}>
              <div className="flex items-center gap-2">
                <span className={`inline-block w-3 h-3 rounded-full ${deviceStatus.connected ? 'bg-fitnix-lime animate-pulse' : 'bg-red-500'}`}></span>
                <span className="text-sm font-bold">Device {deviceStatus.connected ? 'Online' : 'Offline'}</span>
              </div>
            </div>
            <div className="px-5 py-3 rounded-xl border-2 border-fitnix-dark-gray bg-fitnix-charcoal">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-fitnix-gray" />
                <span className="text-xs font-medium text-fitnix-gray">
                  {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats Cards with Gradient Borders */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          {[
            { label: "Today's Check-ins", value: summary.today_checkins, Icon: BarChart3, color: "from-blue-500 to-cyan-500" },
            { label: "Members Inside", value: summary.members_inside, Icon: Users, color: "from-fitnix-lime to-green-400" },
            { label: "Trainers Inside", value: summary.trainers_inside, Icon: UserCheck, color: "from-purple-500 to-pink-500" },
            { label: "Avg Stay Today", value: summary.avg_stay_formatted || '0h 0m', Icon: Timer, color: "from-orange-500 to-red-500" }
          ].map((stat, idx) => (
            <div key={idx} className="group relative">
              <div className={`absolute -inset-0.5 bg-gradient-to-r ${stat.color} rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300`}></div>
              <div className="relative bg-fitnix-charcoal border-2 border-fitnix-dark-gray p-6 rounded-2xl hover:border-fitnix-lime/50 transition-all duration-300 transform hover:scale-105">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-fitnix-gray text-xs font-black uppercase tracking-wider">{stat.label}</h3>
                  <stat.Icon className="w-10 h-10 text-fitnix-lime" strokeWidth={3} />
                </div>
                <p className="text-6xl font-black bg-gradient-to-r from-fitnix-lime to-green-400 bg-clip-text text-transparent">
                  {stat.value}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Live Feed & Currently Inside - Smaller */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
          {/* Live Activity Feed - Smaller */}
          <div className="relative group h-full">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-fitnix-lime to-green-400 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div className="relative bg-fitnix-charcoal border-3 border-fitnix-dark-gray p-6 rounded-2xl h-full flex flex-col">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-2xl font-black text-fitnix-off-white flex items-center gap-3">
                  <Zap className="w-7 h-7 text-fitnix-lime" strokeWidth={3} />
                  Live Activity
                </h2>
                <span className="px-3 py-1.5 bg-fitnix-lime/20 text-fitnix-lime text-xs font-black rounded-full border-2 border-fitnix-lime/30 flex items-center gap-2">
                  <span className="inline-block w-2 h-2 bg-fitnix-lime rounded-full animate-pulse"></span>
                  LIVE
                </span>
              </div>
              <div className="space-y-2 h-[400px] overflow-y-auto custom-scrollbar">
                {liveEvents.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center">
                    <Activity className="w-16 h-16 text-fitnix-dark-gray mb-3" strokeWidth={2} />
                    <p className="text-fitnix-gray font-bold text-sm">No recent activity</p>
                  </div>
                ) : (
                  liveEvents.map((event, idx) => (
                    <div key={`${event.id}-${idx}`} className="p-2.5 bg-gradient-to-r from-fitnix-dark-gray/80 to-fitnix-dark-gray/40 rounded-lg border-l-3 border-fitnix-lime hover:border-l-4 transition-all duration-200">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-black text-fitnix-off-white text-sm">{event.person_name}</p>
                          <p className="text-xs text-fitnix-lime capitalize font-bold mt-0.5">{event.person_type} • {event.status}</p>
                        </div>
                        {event.status.includes('Check-In') ? (
                          <CheckCircle2 className="w-4 h-4 text-fitnix-lime" strokeWidth={3} />
                        ) : (
                          <XCircle className="w-4 h-4 text-orange-400" strokeWidth={3} />
                        )}
                      </div>
                      <p className="text-xs text-fitnix-gray/70 mt-1 flex items-center gap-1 font-semibold">
                        <Clock className="w-3 h-3" strokeWidth={2.5} />
                        {convertToPKT(event.timestamp)}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Currently Inside */}
          <div className="relative group h-full">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div className="relative bg-fitnix-charcoal border-3 border-fitnix-dark-gray p-6 rounded-2xl h-full flex flex-col">
              <h2 className="text-2xl font-black text-fitnix-off-white mb-5 flex items-center gap-3">
                <Building2 className="w-7 h-7 text-purple-400" strokeWidth={3} />
                Currently Inside
              </h2>
              <div className="space-y-5 flex-1">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-black text-fitnix-lime text-lg flex items-center gap-2">
                      <Users className="w-5 h-5" strokeWidth={3} />
                      Members
                    </h3>
                    <span className="px-3 py-1.5 bg-fitnix-lime/20 text-fitnix-lime text-sm font-black rounded-full border-2 border-fitnix-lime/30">
                      {currentlyInside.members?.length || 0}
                    </span>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                    {currentlyInside.members && currentlyInside.members.length > 0 ? (
                      currentlyInside.members.map(m => (
                        <div key={m.id} className="p-3 bg-fitnix-dark-gray/60 rounded-lg hover:bg-fitnix-dark-gray transition-colors border-2 border-fitnix-dark-gray hover:border-fitnix-lime/30">
                          <div className="flex justify-between items-center">
                            <p className="font-black text-fitnix-off-white text-sm">{m.person_name || m.person_id}</p>
                            <span className="text-xs text-fitnix-lime font-black flex items-center gap-1">
                              <Clock className="w-3 h-3" strokeWidth={2.5} />
                              {m.time_spent_formatted || `${m.time_spent_so_far} min`}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-fitnix-gray text-center py-3 font-bold">No members inside</p>
                    )}
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-black text-purple-400 text-lg flex items-center gap-2">
                      <UserCheck className="w-5 h-5" strokeWidth={3} />
                      Trainers
                    </h3>
                    <span className="px-3 py-1.5 bg-purple-500/20 text-purple-400 text-sm font-black rounded-full border-2 border-purple-500/30">
                      {currentlyInside.trainers?.length || 0}
                    </span>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                    {currentlyInside.trainers && currentlyInside.trainers.length > 0 ? (
                      currentlyInside.trainers.map(t => (
                        <div key={t.id} className="p-3 bg-fitnix-dark-gray/60 rounded-lg hover:bg-fitnix-dark-gray transition-colors border-2 border-fitnix-dark-gray hover:border-purple-500/30">
                          <div className="flex justify-between items-center">
                            <p className="font-black text-fitnix-off-white text-sm">{t.person_name || t.person_id}</p>
                            <span className="text-xs text-purple-400 font-black flex items-center gap-1">
                              <Clock className="w-3 h-3" strokeWidth={2.5} />
                              {t.time_spent_formatted || `${t.time_spent_so_far} min`}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-fitnix-gray text-center py-3 font-bold">No trainers inside</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Today's Summary Table - Moved Above */}
        <div className="relative group mb-10">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-fitnix-lime to-green-400 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-300"></div>
          <div className="relative bg-fitnix-charcoal border-3 border-fitnix-dark-gray p-6 rounded-2xl">
            <h2 className="text-3xl font-black text-fitnix-off-white mb-6 flex items-center gap-3">
              <ClipboardList className="w-9 h-9 text-fitnix-lime" strokeWidth={3} />
              Today's Attendance Summary
            </h2>
            <div className="overflow-x-auto rounded-xl">
              <table className="w-full text-sm">
                <thead className="bg-gradient-to-r from-fitnix-dark-gray to-fitnix-charcoal border-b-3 border-fitnix-lime">
                  <tr>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">Name</th>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">Type</th>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">Status</th>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">First Check-In</th>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">Last Check-Out</th>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">Total Time</th>
                    <th className="px-5 py-5 text-left text-fitnix-lime font-black uppercase tracking-wider text-sm">Visits</th>
                  </tr>
                </thead>
                <tbody>
                  {dailySummary && dailySummary.length > 0 ? (
                    dailySummary.map(record => (
                      <tr key={record.id} className="border-b-2 border-fitnix-dark-gray hover:bg-fitnix-dark-gray/50 transition-colors">
                        <td className="px-5 py-5 text-fitnix-off-white font-black text-base">{record.person_name || record.person_id}</td>
                        <td className="px-5 py-5 text-fitnix-gray capitalize font-bold">{record.person_type}</td>
                        <td className="px-5 py-5">
                          <span className={`px-4 py-2 rounded-full text-xs font-black flex items-center gap-2 w-fit border-2 ${
                            record.status === 'Present' 
                              ? 'bg-fitnix-lime/30 text-fitnix-lime border-fitnix-lime' 
                              : 'bg-red-500/30 text-red-400 border-red-500'
                          }`}>
                            {record.status === 'Present' ? (
                              <CheckCircle2 className="w-4 h-4" strokeWidth={3} />
                            ) : (
                              <XCircle className="w-4 h-4" strokeWidth={3} />
                            )}
                            {record.status}
                          </span>
                        </td>
                        <td className="px-5 py-5 text-fitnix-gray font-bold">{record.first_check_in ? convertToPKT(record.first_check_in) : '-'}</td>
                        <td className="px-5 py-5 text-fitnix-gray font-bold">{record.last_check_out ? convertToPKT(record.last_check_out) : '-'}</td>
                        <td className="px-5 py-5 text-fitnix-gray font-bold">{record.total_time_minutes ? `${Math.floor(record.total_time_minutes / 60)}h ${record.total_time_minutes % 60}m` : '-'}</td>
                        <td className="px-5 py-5 text-fitnix-lime font-black text-xl">{record.visit_count}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7" className="px-5 py-16 text-center">
                        <ClipboardList className="w-20 h-20 text-fitnix-dark-gray mx-auto mb-4" strokeWidth={2} />
                        <p className="text-fitnix-gray text-lg font-bold">No attendance records for today</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Weekly Analytics - Full Width */}
        <div className="grid grid-cols-1 gap-6 mb-10">
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-300"></div>
            <div className="relative bg-fitnix-charcoal border-3 border-fitnix-dark-gray p-8 rounded-2xl">
              <h2 className="text-3xl font-black text-fitnix-off-white mb-8 flex items-center gap-3">
                <TrendingUp className="w-10 h-10 text-blue-400" strokeWidth={3} />
                Weekly Analytics
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-7 gap-6">
                {weeklyData && weeklyData.length > 0 ? (
                  weeklyData.map((day, idx) => (
                    <div key={idx} className="group/bar flex flex-col items-center">
                      <div className="flex flex-col items-center mb-3">
                        <span className="text-lg font-black text-fitnix-gray mb-2">{day.day ? day.day.substring(0, 3) : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][idx]}</span>
                        <span className="text-3xl font-black text-fitnix-lime">{day.count}</span>
                      </div>
                      <div className="bg-fitnix-dark-gray rounded-full h-40 w-16 overflow-hidden border-3 border-fitnix-dark-gray flex flex-col justify-end">
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
                    <BarChart3 className="w-24 h-24 text-fitnix-dark-gray mx-auto mb-4" strokeWidth={2} />
                    <p className="text-fitnix-gray font-bold text-lg">No data available</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Monthly Attendance Records - Collapsible */}
        <div className="relative group">
          <div className="absolute -inset-0.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition duration-300"></div>
          <div className="relative bg-fitnix-charcoal border-3 border-fitnix-dark-gray p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <Calendar className="w-9 h-9 text-purple-400" strokeWidth={3} />
                <div>
                  <h2 className="text-3xl font-black text-fitnix-off-white">Monthly Attendance Records</h2>
                  <p className="text-fitnix-gray text-sm font-bold mt-1">{monthlyRecordsMonth}</p>
                </div>
              </div>
              <button
                onClick={() => setIsMonthlyExpanded(!isMonthlyExpanded)}
                className="flex items-center gap-2 px-5 py-3 bg-purple-500/20 hover:bg-purple-500/30 text-purple-400 rounded-xl border-2 border-purple-500/30 hover:border-purple-500/50 transition-all font-black"
              >
                {isMonthlyExpanded ? (
                  <>
                    <ChevronUp className="w-5 h-5" strokeWidth={3} />
                    Collapse
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-5 h-5" strokeWidth={3} />
                    Expand
                  </>
                )}
              </button>
            </div>

            {isMonthlyExpanded && (
              <>
                {/* Search Bar */}
                <div className="mb-6">
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-fitnix-gray" strokeWidth={2.5} />
                    <input
                      type="text"
                      placeholder="Search by name..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-12 pr-4 py-3 bg-fitnix-dark-gray border-2 border-fitnix-dark-gray focus:border-purple-500 rounded-xl text-fitnix-off-white placeholder-fitnix-gray font-bold focus:outline-none transition-colors"
                    />
                  </div>
                </div>

                {/* Table */}
                <div className="overflow-x-auto rounded-xl max-h-[600px] overflow-y-auto custom-scrollbar">
                  <table className="w-full text-sm">
                    <thead className="bg-gradient-to-r from-fitnix-dark-gray to-fitnix-charcoal border-b-3 border-purple-500 sticky top-0 z-10">
                      <tr>
                        <th className="px-5 py-5 text-left text-purple-400 font-black uppercase tracking-wider text-sm">Name</th>
                        <th className="px-5 py-5 text-left text-purple-400 font-black uppercase tracking-wider text-sm">Type</th>
                        <th className="px-5 py-5 text-left text-purple-400 font-black uppercase tracking-wider text-sm">Total Visits</th>
                        <th className="px-5 py-5 text-left text-purple-400 font-black uppercase tracking-wider text-sm">Days Attended</th>
                        <th className="px-5 py-5 text-left text-purple-400 font-black uppercase tracking-wider text-sm">Total Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {monthlyRecords && monthlyRecords.length > 0 ? (
                        monthlyRecords.map((record, idx) => (
                          <tr key={`${record.person_id}-${idx}`} className="border-b-2 border-fitnix-dark-gray hover:bg-fitnix-dark-gray/50 transition-colors">
                            <td className="px-5 py-5 text-fitnix-off-white font-black text-base">{record.person_name}</td>
                            <td className="px-5 py-5 text-fitnix-gray capitalize font-bold">{record.person_type}</td>
                            <td className="px-5 py-5 text-purple-400 font-black text-xl">{record.total_visits}</td>
                            <td className="px-5 py-5 text-fitnix-lime font-black text-xl">{record.days_attended}</td>
                            <td className="px-5 py-5 text-fitnix-gray font-bold">{record.total_time_formatted}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="px-5 py-16 text-center">
                            <Calendar className="w-20 h-20 text-fitnix-dark-gray mx-auto mb-4" strokeWidth={2} />
                            <p className="text-fitnix-gray text-lg font-bold">
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
    </div>

    {/* Custom Scrollbar Styles */}
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
    `}</style>
    </AdminLayout>
  );
};

export default AdminAttendance;
