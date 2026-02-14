import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../../services/api'
import AdminLayout from '../../components/layouts/AdminLayout'
import logo from '/fitcore-logo.png'

export default function AdminPackages() {
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingPackage, setEditingPackage] = useState(null)
  const [deletingPackage, setDeletingPackage] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    duration_days: '',
    price: '',
    description: '',
    is_active: true
  })
  const navigate = useNavigate()

  useEffect(() => {
    fetchPackages()
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

  const fetchPackages = async () => {
    try {
      const response = await apiClient.get('/packages/')
      setPackages(response.data.packages || [])
    } catch (err) {
      setError('Failed to load packages')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      if (editingPackage) {
        await apiClient.put(`/packages/${editingPackage.id}`, formData)
        setSuccess('Package updated successfully')
        setEditingPackage(null)
      } else {
        await apiClient.post('/packages/', formData)
        setSuccess('Package created successfully')
      }
      setFormData({ name: '', duration_days: '', price: '', description: '', is_active: true })
      setShowForm(false)
      fetchPackages()
    } catch (err) {
      setError(err.response?.data?.error || `Failed to ${editingPackage ? 'update' : 'create'} package`)
    }
  }

  const handleEdit = (pkg) => {
    setEditingPackage(pkg)
    setFormData({
      name: pkg.name,
      duration_days: pkg.duration_days,
      price: pkg.price,
      description: pkg.description || '',
      is_active: pkg.is_active
    })
    setShowForm(true)
    setError('')
    setSuccess('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleCancelEdit = () => {
    setEditingPackage(null)
    setFormData({ name: '', duration_days: '', price: '', description: '', is_active: true })
    setShowForm(false)
    setError('')
    setSuccess('')
  }

  const handleDelete = async (pkg) => {
    setDeletingPackage(pkg)
  }

  const confirmDelete = async () => {
    if (!deletingPackage) return

    setError('')
    setSuccess('')

    try {
      await apiClient.delete(`/packages/${deletingPackage.id}`)
      setSuccess('Package deleted successfully')
      setDeletingPackage(null)
      fetchPackages()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete package')
      setDeletingPackage(null)
    }
  }

  const cancelDelete = () => {
    setDeletingPackage(null)
  }

  const toggleActive = async (pkg) => {
    try {
      await apiClient.put(`/packages/${pkg.id}`, {
        ...pkg,
        is_active: !pkg.is_active
      })
      fetchPackages()
    } catch (err) {
      setError('Failed to update package status')
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

  return (
    <AdminLayout onLogout={handleLogout}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-fitnix-off-white">
              Package <span className="fitnix-gradient-text">Management</span>
            </h1>
            <p className="text-fitnix-off-white/60 mt-2">
              Create and manage membership packages
            </p>
          </div>
          <button
            onClick={() => {
              if (showForm && !editingPackage) {
                setShowForm(false)
                setFormData({ name: '', duration_days: '', price: '', description: '', is_active: true })
              } else if (editingPackage) {
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
                <span>Create Package</span>
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
              {editingPackage ? 'Edit Package' : 'Add New Package'}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                  Package Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="Enter package name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="fitnix-input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                  Duration (days) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  placeholder="Enter duration in days"
                  value={formData.duration_days}
                  onChange={(e) => setFormData({ ...formData, duration_days: e.target.value })}
                  className="fitnix-input"
                  required
                  min="1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                  Price (Rs.) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  placeholder="Enter price"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  className="fitnix-input"
                  required
                  min="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                  Status
                </label>
                <div className="flex items-center h-10">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="w-4 h-4 text-fitnix-lime bg-fitnix-charcoal border-fitnix-off-white/20 rounded focus:ring-fitnix-lime focus:ring-2"
                  />
                  <label htmlFor="is_active" className="ml-2 text-fitnix-off-white">Active</label>
                </div>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                  Description
                </label>
                <textarea
                  placeholder="Enter package description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="fitnix-input"
                  rows="3"
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                type="submit"
                className="flex-1 fitnix-button-primary"
              >
                {editingPackage ? 'Update Package' : 'Create Package'}
              </button>
              {editingPackage && (
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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {packages.map((pkg) => (
            <div key={pkg.id} className="fitnix-card-hover border-2 border-fitnix-lime/20 hover:border-fitnix-lime/40 hover:shadow-neon-lime transform hover:scale-105">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-fitnix-lime">{pkg.name}</h3>
                  <p className="text-sm text-fitnix-off-white/60">{pkg.duration_days} days</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                  pkg.is_active 
                    ? 'bg-fitnix-black text-fitnix-lime border-fitnix-lime' 
                    : 'bg-fitnix-black text-fitnix-off-white/50 border-fitnix-off-white/30'
                }`}>
                  {pkg.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="mb-4">
                <p className="text-3xl sm:text-4xl font-extrabold fitnix-gradient-text">Rs. {pkg.price}</p>
                {pkg.description && (
                  <p className="text-sm text-fitnix-off-white/80 mt-2">{pkg.description}</p>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(pkg)}
                  className="flex-1 bg-fitnix-lime hover:bg-fitnix-dark-lime text-fitnix-black px-3 py-1.5 rounded-md transition font-semibold text-xs shadow-md hover:scale-105"
                >
                  Edit
                </button>
                <button
                  onClick={() => toggleActive(pkg)}
                  className="flex-1 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-500 px-3 py-1.5 rounded-md transition font-semibold text-xs shadow-md hover:scale-105"
                >
                  {pkg.is_active ? 'Deactivate' : 'Activate'}
                </button>
                <button
                  onClick={() => handleDelete(pkg)}
                  className="bg-red-600 hover:bg-red-500 text-white px-3 py-1.5 rounded-md transition font-semibold shadow-md hover:scale-105"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>

        {packages.length === 0 && !showForm && (
          <div className="text-center py-12">
            <div className="flex flex-col items-center justify-center space-y-3">
              <svg className="w-16 h-16 text-fitnix-off-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              <p className="text-fitnix-off-white/60 text-lg">No packages found</p>
              <p className="text-fitnix-off-white/40 text-sm">Create your first package to get started</p>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deletingPackage && (
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
              Delete Package?
            </h3>

            {/* Package Info */}
            <div className="bg-fitnix-black/50 rounded-lg p-4 mb-4 border border-red-500/30">
              <p className="text-fitnix-off-white/80 text-sm mb-2">You are about to delete:</p>
              <p className="text-fitnix-lime font-bold text-lg">{deletingPackage.name}</p>
              <p className="text-fitnix-off-white/60 text-sm">Duration: {deletingPackage.duration_days} days</p>
              <p className="text-fitnix-off-white/60 text-sm">Price: Rs. {deletingPackage.price}</p>
              {deletingPackage.description && (
                <p className="text-fitnix-off-white/60 text-sm mt-2">{deletingPackage.description}</p>
              )}
            </div>

            {/* Warning Message */}
            <p className="text-fitnix-off-white/80 text-center mb-6">
              This action <span className="text-red-500 font-bold">cannot be undone</span>. Members currently using this package may be affected.
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
                Delete Package
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
