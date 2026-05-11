import { useState, useEffect } from 'react';
import { Clock, Calendar, TrendingUp } from 'lucide-react';
import apiClient from '../services/api';

const MemberAttendanceHistory = ({ memberId }) => {
  const [attendance, setAttendance] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30'); // days

  useEffect(() => {
    fetchAttendanceHistory();
  }, [memberId, timeRange]);

  const fetchAttendanceHistory = async () => {
    try {
      setLoading(true);
      
      // Calculate date range
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - parseInt(timeRange));
      
      // Fetch attendance records
      const response = await apiClient.get('/attendance/history', {
        params: {
          person_id: memberId,
          person_type: 'member',
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
          per_page: 1000 // Get all records for stats
        }
      });
      
      if (response.data.success) {
        const records = response.data.records || [];
        setAttendance(records);
        
        // Calculate stats
        const totalCheckIns = records.length;
        
        // Count unique days attended
        const uniqueDays = new Set(
          records.map(r => new Date(r.check_in_time).toDateString())
        );
        const daysAttended = uniqueDays.size;
        
        // Calculate attendance rate (days attended / total days in period)
        const totalDays = parseInt(timeRange);
        const attendanceRate = totalDays > 0 ? Math.round((daysAttended / totalDays) * 100) : 0;
        
        // Calculate monthly breakdown for last 12 months
        const monthlyData = {};
        const now = new Date();
        
        // Initialize last 12 months
        for (let i = 11; i >= 0; i--) {
          const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
          const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          const monthName = date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
          monthlyData[key] = { month: monthName, count: 0 };
        }
        
        // Count check-ins per month
        records.forEach(r => {
          const date = new Date(r.check_in_time);
          const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
          if (monthlyData[key]) {
            monthlyData[key].count++;
          }
        });
        
        setStats({
          totalCheckIns,
          daysAttended,
          attendanceRate,
          monthlyBreakdown: Object.values(monthlyData)
        });
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching attendance:', error);
      setLoading(false);
    }
  };

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDuration = (minutes) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-fitnix-lime"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Time Range Selector */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {['7', '30', '90', '365'].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                timeRange === days
                  ? 'bg-fitnix-lime text-fitnix-black'
                  : 'bg-fitnix-black text-fitnix-off-white/60 hover:text-fitnix-off-white'
              }`}
            >
              {days === '7' ? 'Week' : days === '30' ? 'Month' : days === '90' ? '3 Months' : 'Year'}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-fitnix-black/40 rounded-lg p-4 border border-fitnix-lime/20">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-fitnix-lime" />
                <span className="text-xs text-fitnix-off-white/60 font-semibold">Total Check-ins</span>
              </div>
              <p className="text-3xl font-bold text-fitnix-lime">{stats.totalCheckIns}</p>
            </div>
            <div className="bg-fitnix-black/40 rounded-lg p-4 border border-fitnix-lime/20">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-fitnix-lime" />
                <span className="text-xs text-fitnix-off-white/60 font-semibold">Days Attended</span>
              </div>
              <p className="text-3xl font-bold text-fitnix-lime">{stats.daysAttended}</p>
            </div>
            <div className="bg-fitnix-black/40 rounded-lg p-4 border border-fitnix-lime/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-fitnix-lime" />
                <span className="text-xs text-fitnix-off-white/60 font-semibold">Attendance Rate</span>
              </div>
              <p className="text-3xl font-bold text-fitnix-lime">{stats.attendanceRate}%</p>
            </div>
          </div>

          {/* Monthly Breakdown */}
          <div className="bg-fitnix-black/40 rounded-lg p-4 border border-fitnix-lime/20 mb-6">
            <h4 className="text-sm font-bold text-fitnix-off-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-fitnix-lime" />
              Monthly Breakdown (Last 12 Months)
            </h4>
            <div className="grid grid-cols-6 gap-3">
              {stats.monthlyBreakdown.map((month, idx) => (
                <div key={idx} className="text-center">
                  <div className="text-xs text-fitnix-off-white/60 mb-1 font-semibold">{month.month}</div>
                  <div className="text-2xl font-bold text-fitnix-lime">{month.count}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Attendance Records Table */}
      <div className="max-h-96 overflow-y-auto rounded-lg border border-fitnix-off-white/10">
        {attendance.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-fitnix-black/60 sticky top-0">
              <tr>
                <th className="px-4 py-3 text-left text-fitnix-lime font-bold text-xs uppercase">Date</th>
                <th className="px-4 py-3 text-left text-fitnix-lime font-bold text-xs uppercase">Check-In Time</th>
              </tr>
            </thead>
            <tbody>
              {attendance.map((record, idx) => (
                <tr 
                  key={record.id} 
                  className={`border-b border-fitnix-off-white/5 hover:bg-fitnix-black/20 transition-colors ${
                    idx % 2 === 0 ? 'bg-fitnix-black/10' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-fitnix-off-white font-semibold">
                    {formatDate(record.check_in_time)}
                  </td>
                  <td className="px-4 py-3 text-fitnix-lime font-bold">
                    {formatTime(record.check_in_time)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="py-12 text-center">
            <Calendar className="w-12 h-12 text-fitnix-off-white/20 mx-auto mb-3" />
            <p className="text-fitnix-off-white/60 font-semibold">No attendance records found</p>
            <p className="text-fitnix-off-white/40 text-sm mt-1">
              Try selecting a different time range
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MemberAttendanceHistory;
