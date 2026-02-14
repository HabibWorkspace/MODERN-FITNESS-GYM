import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../../services/api'
import AdminLayout from '../../components/layouts/AdminLayout'
import logo from '/fitcore-logo.png'

export default function AdminTrainers() {
  const [trainers, setTrainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingTrainer, setEditingTrainer] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  const [deletingTrainer, setDeletingTrainer] = useState(null)
  const [formData, setFormData] = useState({
    full_name: '',
    gender: '',
    date_of_birth: '',
    phone: '',
    cnic: '',
    email: '',
    specialization: '',
    salary_rate: '',
    availability: '',
  })
  const navigate = useNavigate()

  useEffect(() => {
    fetchTrainers()
  }, [])

  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError('')
        setSuccess('')
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [error, success])

  const fetchTrainers = async () => {
    try {
      const response = await apiClient.get('/admin/trainers-fixed')
      setTrainers(response.data.trainers || [])
    } catch (err) {
      setError('Failed to load trainers')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    
    try {
      if (editingTrainer) {
        // Update existing trainer
        const updateData = {
          full_name: formData.full_name,
          gender: formData.gender,
          date_of_birth: formData.date_of_birth,
          phone: formData.phone,
          cnic: formData.cnic,
          email: formData.email,
          specialization: formData.specialization,
          salary_rate: formData.salary_rate,
          availability: formData.availability,
        }
        await apiClient.put(`/admin/trainers/${editingTrainer.id}/update-fixed`, updateData)
        setSuccess('Trainer updated successfully')
        setEditingTrainer(null)
      } else {
        // Create new trainer without username/password
        const createData = {
          full_name: formData.full_name,
          gender: formData.gender,
          date_of_birth: formData.date_of_birth,
          phone: formData.phone,
          cnic: formData.cnic,
          email: formData.email,
          specialization: formData.specialization,
          salary_rate: formData.salary_rate,
          availability: formData.availability,
        }
        await apiClient.post('/admin/trainers', createData)
        setSuccess('Trainer created successfully')
      }
      
      setFormData({ username: '', password: '', full_name: '', gender: '', date_of_birth: '', phone: '', cnic: '', email: '', specialization: '', salary_rate: '', availability: '' })
      setShowForm(false)
      fetchTrainers()
    } catch (err) {
      setError(err.response?.data?.error || `Failed to ${editingTrainer ? 'update' : 'create'} trainer`)
    }
  }

  const handleEdit = (trainer) => {
    setEditingTrainer(trainer)
    
    // Format date_of_birth for input field (needs YYYY-MM-DD format)
    let dobFormatted = '';
    if (trainer.date_of_birth) {
      try {
        const date = new Date(trainer.date_of_birth);
        dobFormatted = date.toISOString().split('T')[0];
      } catch (e) {
        console.error('Error formatting date:', e);
      }
    }
    
    const formDataToSet = {
      full_name: trainer.full_name || '',
      gender: trainer.gender || '',
      date_of_birth: dobFormatted,
      phone: trainer.phone || '',
      cnic: trainer.cnic || '',
      email: trainer.email || '',
      specialization: trainer.specialization || '',
      salary_rate: trainer.salary_rate || '',
      availability: trainer.availability || '',
    };
    
    setFormData(formDataToSet);
    
    setShowForm(true)
    setShowPassword(false)
    setError('')
    setSuccess('')
    
    // Scroll to top to show the form
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelEdit = () => {
    setEditingTrainer(null)
    setFormData({ full_name: '', gender: '', date_of_birth: '', phone: '', cnic: '', email: '', specialization: '', salary_rate: '', availability: '' })
    setShowForm(false)
    setShowPassword(false)
    setError('')
    setSuccess('')
  }

  const handleDelete = async (trainer) => {
    setDeletingTrainer(trainer)
  }

  const confirmDelete = async () => {
    if (!deletingTrainer) return
    
    setError('')
    setSuccess('')
    
    try {
      await apiClient.delete(`/admin/trainers/${deletingTrainer.id}`)
      setSuccess('Trainer deleted successfully')
      setDeletingTrainer(null)
      fetchTrainers()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete trainer')
      setDeletingTrainer(null)
    }
  }

  const cancelDelete = () => {
    setDeletingTrainer(null)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
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

  return (
    <AdminLayout onLogout={handleLogout}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-fitnix-off-white">
              Trainer <span className="fitnix-gradient-text">Management</span>
            </h1>
            <p className="text-fitnix-off-white/60 mt-2">
              Manage gym trainers, profiles, and access
            </p>
          </div>
          <button
            onClick={() => {
              if (showForm && !editingTrainer) {
                setShowForm(false)
                setFormData({ full_name: '', gender: '', date_of_birth: '', phone: '', cnic: '', email: '', specialization: '', salary_rate: '', availability: '' })
              } else if (editingTrainer) {
                handleCancelEdit()
              } else {
                setShowForm(true)
              }
            }}
            className="fitnix-button-primary flex items-center justify-center space-x-2 w-full sm:w-auto"
          >
            {showForm ? (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                <span>Cancel</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                <span>Add Trainer</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-500 text-fitnix-off-white px-4 py-3 rounded-xl">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {error}
            </div>
          </div>
        )}

        {success && (
          <div className="bg-fitnix-charcoal border border-fitnix-lime text-fitnix-off-white px-4 py-3 rounded-xl">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2 text-fitnix-lime" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {success}
            </div>
          </div>
        )}

        {showForm && (
          <form onSubmit={handleSubmit} className="fitnix-card-glow">
            <h2 className="text-xl font-semibold text-fitnix-off-white mb-4">
              {editingTrainer ? 'Edit Trainer' : 'Add New Trainer'}
            </h2>
            
            {/* Personal Information */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-fitnix-lime mb-3">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Full Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Enter full name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="fitnix-input"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="fitnix-input"
                  >
                    <option value="">Select gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Date of Birth
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <select
                      value={formData.date_of_birth ? new Date(formData.date_of_birth).getDate() : ''}
                      onChange={(e) => {
                        const day = e.target.value
                        if (day && formData.date_of_birth) {
                          const date = new Date(formData.date_of_birth)
                          date.setDate(parseInt(day))
                          setFormData({ ...formData, date_of_birth: date.toISOString().split('T')[0] })
                        } else if (day) {
                          const date = new Date()
                          date.setDate(parseInt(day))
                          setFormData({ ...formData, date_of_birth: date.toISOString().split('T')[0] })
                        }
                      }}
                      className="fitnix-input"
                    >
                      <option value="">Day</option>
                      {Array.from({ length: 31 }, (_, i) => i + 1).map(day => (
                        <option key={day} value={day}>{day}</option>
                      ))}
                    </select>
                    <select
                      value={formData.date_of_birth ? new Date(formData.date_of_birth).getMonth() + 1 : ''}
                      onChange={(e) => {
                        const month = e.target.value
                        if (month && formData.date_of_birth) {
                          const date = new Date(formData.date_of_birth)
                          date.setMonth(parseInt(month) - 1)
                          setFormData({ ...formData, date_of_birth: date.toISOString().split('T')[0] })
                        } else if (month) {
                          const date = new Date()
                          date.setMonth(parseInt(month) - 1)
                          setFormData({ ...formData, date_of_birth: date.toISOString().split('T')[0] })
                        }
                      }}
                      className="fitnix-input"
                    >
                      <option value="">Month</option>
                      {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month, i) => (
                        <option key={i + 1} value={i + 1}>{month}</option>
                      ))}
                    </select>
                    <select
                      value={formData.date_of_birth ? new Date(formData.date_of_birth).getFullYear() : ''}
                      onChange={(e) => {
                        const year = e.target.value
                        if (year && formData.date_of_birth) {
                          const date = new Date(formData.date_of_birth)
                          date.setFullYear(parseInt(year))
                          setFormData({ ...formData, date_of_birth: date.toISOString().split('T')[0] })
                        } else if (year) {
                          const date = new Date()
                          date.setFullYear(parseInt(year))
                          setFormData({ ...formData, date_of_birth: date.toISOString().split('T')[0] })
                        }
                      }}
                      className="fitnix-input"
                    >
                      <option value="">Year</option>
                      {Array.from({ length: 100 }, (_, i) => new Date().getFullYear() - i).map(year => (
                        <option key={year} value={year}>{year}</option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Email <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="email"
                    placeholder="Enter email address"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="fitnix-input"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Phone <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    placeholder="Enter phone number"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="fitnix-input"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    CNIC
                  </label>
                  <input
                    type="text"
                    placeholder="Enter CNIC (e.g., 12345-1234567-1)"
                    value={formData.cnic}
                    onChange={(e) => setFormData({ ...formData, cnic: e.target.value })}
                    className="fitnix-input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Specialization
                  </label>
                  <input
                    type="text"
                    placeholder="Enter specialization (e.g., Cardio, Strength)"
                    value={formData.specialization}
                    onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                    className="fitnix-input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Salary Rate (Rs.)
                  </label>
                  <input
                    type="number"
                    placeholder="Enter salary rate"
                    step="0.01"
                    value={formData.salary_rate}
                    onChange={(e) => setFormData({ ...formData, salary_rate: e.target.value })}
                    className="fitnix-input"
                    min="0"
                  />
                </div>
              </div>
            </div>
            
            {/* Availability/Timetable */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-fitnix-lime mb-3">Availability & Schedule</h3>
              <div>
                <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                  Available Time Slots
                </label>
                <textarea
                  placeholder="e.g., Mon-Fri: 6AM-2PM, Sat: 8AM-12PM"
                  value={formData.availability}
                  onChange={(e) => setFormData({ ...formData, availability: e.target.value })}
                  className="fitnix-input"
                  rows="3"
                />
                <p className="text-xs text-fitnix-off-white/50 mt-1">Enter the trainer's available days and time slots</p>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                type="submit"
                className="flex-1 fitnix-button-primary"
              >
                {editingTrainer ? 'Update Trainer' : 'Create Trainer'}
              </button>
              {editingTrainer && (
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="flex-1 fitnix-button-secondary"
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        )}

        <div className="fitnix-card overflow-hidden" style={{ border: 'none' }}>
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="bg-fitnix-black border-b-2 border-fitnix-lime/30">
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Full Name</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Gender</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">DOB</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">CNIC</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Phone</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Email</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Specialization</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Charges</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Available Timings</th>
                  <th className="px-6 py-5 text-center text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Members</th>
                  <th className="px-6 py-5 text-center text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-fitnix-charcoal/30">
                {trainers.length === 0 ? (
                  <tr>
                    <td colSpan="11" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <svg className="w-16 h-16 text-fitnix-off-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        <p className="text-fitnix-off-white/60 text-lg">No trainers found</p>
                        <p className="text-fitnix-off-white/40 text-sm">Add your first trainer to get started</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  trainers.map((trainer, index) => (
                    <tr key={trainer.id} className={`hover:bg-fitnix-black/50 transition-colors border-b border-fitnix-lime/10 ${index % 2 === 0 ? 'bg-fitnix-charcoal/20' : 'bg-fitnix-charcoal/40'}`}>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{trainer.full_name || 'N/A'}</td>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{trainer.gender || 'N/A'}</td>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">
                        {trainer.date_of_birth ? new Date(trainer.date_of_birth).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{trainer.cnic || 'N/A'}</td>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{trainer.phone || 'N/A'}</td>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{trainer.email || 'N/A'}</td>
                      <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{trainer.specialization || 'N/A'}</td>
                      <td className="px-6 py-6 text-base text-fitnix-lime font-bold whitespace-nowrap">Rs. {parseFloat(trainer.salary_rate || 0).toLocaleString()}</td>
                      <td className="px-6 py-6 text-sm text-fitnix-off-white/80">
                        {trainer.availability ? (
                          <div className="max-w-xs truncate" title={trainer.availability}>
                            {trainer.availability}
                          </div>
                        ) : (
                          <span className="text-fitnix-off-white/40 italic">Not set</span>
                        )}
                      </td>
                      <td className="px-6 py-6 text-center">
                        <span className="inline-flex items-center justify-center w-10 h-10 bg-fitnix-lime/20 text-fitnix-lime rounded-full font-bold border-2 border-fitnix-lime">
                          {trainer.assigned_members_count || 0}
                        </span>
                      </td>
                      <td className="px-6 py-6">
                        <div className="flex flex-col gap-1.5 items-center">
                          <button
                            onClick={() => handleEdit(trainer)}
                            className="w-24 bg-fitnix-lime hover:bg-fitnix-dark-lime text-fitnix-black px-3 py-1.5 rounded transition-all font-semibold text-xs shadow-sm hover:scale-105"
                            title="Edit trainer"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(trainer)}
                            className="w-24 bg-red-600 hover:bg-red-500 text-white px-3 py-1.5 rounded transition-all font-semibold text-xs shadow-sm hover:scale-105"
                            title="Delete trainer"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deletingTrainer && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-fitnix-charcoal border-2 border-red-500 rounded-xl max-w-md w-full p-6 shadow-2xl animate-scale-in">
            {/* Warning Icon */}
            <div className="flex justify-center mb-4">
              <div className="bg-red-500/20 rounded-full p-3">
                <svg className="w-12 h-12 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>

            {/* Title */}
            <h3 className="text-2xl font-bold text-fitnix-off-white text-center mb-2">
              Delete Trainer?
            </h3>

            {/* Trainer Info */}
            <div className="bg-fitnix-black/50 rounded-lg p-4 mb-4 border border-red-500/30">
              <p className="text-fitnix-off-white/80 text-sm mb-2">You are about to delete:</p>
              <p className="text-fitnix-lime font-bold text-lg">{deletingTrainer.username}</p>
              <p className="text-fitnix-off-white/60 text-sm">Specialization: {deletingTrainer.specialization}</p>
              {deletingTrainer.phone && <p className="text-fitnix-off-white/60 text-sm">Phone: {deletingTrainer.phone}</p>}
              {deletingTrainer.email && <p className="text-fitnix-off-white/60 text-sm">Email: {deletingTrainer.email}</p>}
            </div>

            {/* Warning Message */}
            <p className="text-fitnix-off-white/80 text-center mb-6">
              This action <span className="text-red-500 font-bold">cannot be undone</span>. All trainer data and associated records will be permanently deleted.
            </p>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={cancelDelete}
                className="flex-1 bg-fitnix-charcoal hover:bg-fitnix-charcoal/80 text-fitnix-off-white font-semibold py-3 px-4 rounded-lg transition border border-fitnix-off-white/20"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-4 rounded-lg transition shadow-lg"
              >
                Delete Trainer
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
