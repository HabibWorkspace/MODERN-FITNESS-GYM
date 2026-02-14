import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../../services/api'
import AdminLayout from '../../components/layouts/AdminLayout'
import logo from '/fitcore-logo.png'
import modernLogo from '/modern-fitness-logo.png'

export default function AdminMembers() {
  const [members, setMembers] = useState([])
  const [packages, setPackages] = useState([])
  const [trainers, setTrainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingMember, setEditingMember] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  const [defaultAdmissionFee, setDefaultAdmissionFee] = useState(0)
  const [deletingMember, setDeletingMember] = useState(null)
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    cnic: '',
    email: '',
    gender: '',
    date_of_birth: '',
    admission_date: new Date().toISOString().split('T')[0],
    admission_fee: 0,
    waive_admission_fee: false,
    discount: 0,
    discount_type: 'fixed', // 'fixed' or 'percentage'
    final_payable: 0,
    package_id: '',
    trainer_id: '',
  })
  const navigate = useNavigate()

  useEffect(() => {
    fetchMembers()
    fetchPackages()
    fetchTrainers()
    fetchSettings()
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

  // Calculate final payable whenever relevant fields change
  useEffect(() => {
    calculateFinalPayable()
  }, [formData.admission_fee, formData.waive_admission_fee, formData.discount, formData.discount_type, formData.package_id, formData.trainer_id])

  const fetchMembers = async () => {
    try {
      // Add cache buster to force fresh data
      const response = await apiClient.get(`/admin/members?_t=${Date.now()}`, {
        headers: { 
          'Cache-Control': 'no-cache', 
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      })
      setMembers(response.data.members || [])
    } catch (err) {
      setError('Failed to load members')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchPackages = async () => {
    try {
      const response = await apiClient.get('/packages')
      setPackages(response.data.packages || [])
    } catch (err) {
      console.error('Failed to load packages:', err)
    }
  }

  const fetchTrainers = async () => {
    try {
      const response = await apiClient.get('/admin/trainers')
      setTrainers(response.data.trainers || [])
    } catch (err) {
      console.error('Failed to load trainers:', err)
    }
  }

  const fetchSettings = async () => {
    try {
      const response = await apiClient.get('/admin/settings')
      const admissionFee = parseFloat(response.data.admission_fee) || 0
      setDefaultAdmissionFee(admissionFee)
      // Update formData with the fetched admission fee
      setFormData(prev => ({ 
        ...prev, 
        admission_fee: admissionFee
      }))
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  const calculateFinalPayable = () => {
    let finalAmount = 0
    
    // Start with admission fee
    if (!formData.waive_admission_fee) {
      finalAmount = parseFloat(formData.admission_fee) || 0
    }
    
    // Add package price if a package is selected
    if (formData.package_id) {
      const selectedPackage = packages.find(pkg => pkg.id === formData.package_id)
      if (selectedPackage) {
        finalAmount += parseFloat(selectedPackage.price) || 0
      }
    }
    
    // Add trainer charge if a trainer is selected (get from trainer's salary_rate)
    if (formData.trainer_id) {
      const selectedTrainer = trainers.find(t => t.id === formData.trainer_id)
      if (selectedTrainer) {
        finalAmount += parseFloat(selectedTrainer.salary_rate) || 0
      }
    }
    
    // Apply discount if any
    const discount = parseFloat(formData.discount) || 0
    if (discount > 0 && !formData.waive_admission_fee) {
      if (formData.discount_type === 'percentage') {
        finalAmount = finalAmount - (finalAmount * discount / 100)
      } else {
        finalAmount = finalAmount - discount
      }
    }
    
    // Ensure final payable is not negative
    finalAmount = Math.max(0, finalAmount)
    
    // Only update if the value actually changed to avoid infinite loops
    if (formData.final_payable !== finalAmount) {
      setFormData(prev => ({ ...prev, final_payable: finalAmount }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    
    // Validation
    if (!formData.full_name || !formData.email || !formData.phone) {
      setError('Full Name, Email, and Phone are required')
      return
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address')
      return
    }
    
    if (!editingMember && !formData.waive_admission_fee) {
      const discount = parseFloat(formData.discount) || 0
      const admissionFee = parseFloat(formData.admission_fee) || 0
      
      // Calculate total amount (admission fee + package price)
      let totalAmount = admissionFee
      if (formData.package_id) {
        const selectedPackage = packages.find(pkg => pkg.id === formData.package_id)
        if (selectedPackage) {
          totalAmount += parseFloat(selectedPackage.price) || 0
        }
      }
      
      if (formData.discount_type === 'fixed' && discount > totalAmount) {
        setError('Discount cannot exceed total amount (Admission Fee + Package Price)')
        return
      }
      
      if (formData.discount_type === 'percentage' && discount > 100) {
        setError('Discount percentage cannot exceed 100%')
        return
      }
    }
    
    try {
      if (editingMember) {
        // Update existing member
        const updateData = {
          full_name: formData.full_name,
          phone: formData.phone,
          cnic: formData.cnic,
          email: formData.email,
          gender: formData.gender,
          date_of_birth: formData.date_of_birth,
          admission_date: formData.admission_date,
          package_id: formData.package_id,
          trainer_id: formData.trainer_id,
          package_start_date: formData.package_start_date,
          package_expiry_date: formData.package_expiry_date,
        }
        const response = await apiClient.put(
          `/admin/members/${editingMember.id}?_t=${Date.now()}`, 
          updateData,
          { 
            headers: { 
              'Cache-Control': 'no-cache, no-store, must-revalidate', 
              'Pragma': 'no-cache',
              'Expires': '0'
            } 
          }
        )
        setSuccess('Member updated successfully')
        setEditingMember(null)
      } else {
        // Create new member without username/password
        // Get trainer charge from trainer's salary_rate if trainer is selected
        let trainerCharge = 0
        if (formData.trainer_id) {
          const selectedTrainer = trainers.find(t => t.id === formData.trainer_id)
          if (selectedTrainer) {
            trainerCharge = parseFloat(selectedTrainer.salary_rate) || 0
          }
        }

        const createData = {
          full_name: formData.full_name,
          phone: formData.phone,
          cnic: formData.cnic,
          email: formData.email,
          gender: formData.gender,
          date_of_birth: formData.date_of_birth,
          admission_date: formData.admission_date,
          admission_fee: formData.waive_admission_fee ? 0 : formData.admission_fee,
          discount: formData.waive_admission_fee ? 0 : formData.discount,
          discount_type: formData.discount_type,
          trainer_charge: trainerCharge,
          package_id: formData.package_id,
          trainer_id: formData.trainer_id,
        }
        await apiClient.post('/admin/members', createData)
        setSuccess('Member created successfully')
      }
      
      resetForm()
      setShowForm(false)
      
      // Wait a moment for database to commit, then refetch
      await new Promise(resolve => setTimeout(resolve, 300))
      await fetchMembers()
    } catch (err) {
      setError(err.response?.data?.error || `Failed to ${editingMember ? 'update' : 'create'} member`)
    }
  }

  const resetForm = () => {
    const admissionFee = defaultAdmissionFee || 0
    setFormData({
      full_name: '',
      phone: '',
      cnic: '',
      email: '',
      gender: '',
      date_of_birth: '',
      admission_date: new Date().toISOString().split('T')[0],
      admission_fee: admissionFee,
      waive_admission_fee: false,
      discount: 0,
      discount_type: 'fixed',
      final_payable: admissionFee,
      package_id: '',
      trainer_id: '',
      package_start_date: '',
      package_expiry_date: '',
    })
    setShowPassword(false)
  }

  const handleEdit = (member) => {
    // Fetch latest settings before opening form
    fetchSettings().then(() => {
      const admissionFee = defaultAdmissionFee || 0
      setEditingMember(member)
      setFormData({
        full_name: member.full_name || '',
        phone: member.phone,
        cnic: member.cnic,
        email: member.email,
        gender: member.gender || '',
        date_of_birth: member.date_of_birth || '',
        admission_date: member.admission_date || new Date().toISOString().split('T')[0],
        admission_fee: admissionFee,
        waive_admission_fee: false,
        discount: 0,
        discount_type: 'fixed',
        final_payable: admissionFee,
        package_id: member.current_package_id || '',
        trainer_id: member.trainer_id || '',
        package_start_date: member.package_start_date || '',
        package_expiry_date: member.package_expiry_date || '',
      })
      setShowForm(true)
      setShowPassword(false)
      setError('')
      setSuccess('')
      
      // Scroll to top to show the form
      window.scrollTo({ top: 0, behavior: 'smooth' })
    })
  }

  const handleCancelEdit = () => {
    setEditingMember(null)
    resetForm()
    setShowForm(false)
    setError('')
    setSuccess('')
  }

  const handleDelete = async (member) => {
    setDeletingMember(member)
  }

  const confirmDelete = async () => {
    if (!deletingMember) return
    
    setError('')
    setSuccess('')
    
    try {
      await apiClient.delete(`/admin/members/${deletingMember.id}`)
      setSuccess('Member deleted successfully')
      setDeletingMember(null)
      fetchMembers()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to delete member')
      setDeletingMember(null)
    }
  }

  const cancelDelete = () => {
    setDeletingMember(null)
  }

  const handlePrintReceipt = (member) => {
    const payment = memberPayments[member.id]
    if (!payment) {
      setError('No payment information found')
      return
    }

    const pkg = packages.find(p => p.id === member.current_package_id)
    
    // Generate short transaction ID (last 8 characters)
    const shortTxnId = payment.id.slice(-8).toUpperCase()
    
    // Create a hidden iframe for printing
    const iframe = document.createElement('iframe')
    iframe.style.position = 'absolute'
    iframe.style.width = '0'
    iframe.style.height = '0'
    iframe.style.border = 'none'
    document.body.appendChild(iframe)
    
    const iframeDoc = iframe.contentWindow.document
    
    // Create receipt content
    const receiptContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Payment Receipt - ${member.full_name || member.username}</title>
        <style>
          @page {
            size: A4;
            margin: 15mm;
          }
          body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
            background: #fff;
            font-size: 28px;
            line-height: 1.6;
          }
          .header {
            text-align: center;
            border-bottom: 6px solid #B6FF00;
            padding-bottom: 40px;
            margin-bottom: 50px;
            page-break-after: avoid;
          }
          .logo {
            width: 220px;
            height: 220px;
            margin: 0 auto 30px;
            display: block;
            object-fit: contain;
          }
          .gym-name {
            color: #B6FF00;
            margin: 25px 0;
            font-size: 68px;
            font-weight: bold;
            text-shadow: 3px 3px 8px rgba(0,0,0,0.3);
            letter-spacing: 1px;
          }
          .receipt-title {
            font-size: 48px;
            font-weight: 800;
            color: #333;
            margin: 25px 0;
            text-transform: uppercase;
            letter-spacing: 2px;
          }
          .receipt-date {
            color: #666;
            font-size: 30px;
            font-weight: 600;
            margin-top: 15px;
          }
          .receipt-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 35px;
            margin-bottom: 50px;
            page-break-inside: avoid;
          }
          .info-section {
            background: #f8f9fa;
            padding: 35px;
            border-radius: 18px;
            border: 3px solid #e9ecef;
          }
          .info-section h3 {
            margin-top: 0;
            margin-bottom: 30px;
            color: #0B0B0B;
            font-size: 36px;
            font-weight: 800;
            border-bottom: 5px solid #B6FF00;
            padding-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
          }
          .info-row {
            display: flex;
            justify-content: space-between;
            margin: 22px 0;
            padding: 15px 0;
            border-bottom: 2px solid #e9ecef;
          }
          .info-row:last-child {
            border-bottom: none;
          }
          .info-label {
            font-weight: 800;
            color: #495057;
            font-size: 28px;
          }
          .info-value {
            color: #212529;
            font-size: 28px;
            text-align: right;
            font-weight: 700;
            max-width: 60%;
            word-wrap: break-word;
          }
          .payment-details {
            background: linear-gradient(135deg, #B6FF00 0%, #9FE600 100%);
            padding: 50px;
            border-radius: 24px;
            margin: 50px 0;
            box-shadow: 0 10px 25px rgba(182, 255, 0, 0.5);
            page-break-inside: avoid;
          }
          .payment-details h2 {
            margin-top: 0;
            margin-bottom: 40px;
            color: #0B0B0B;
            font-size: 48px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
          }
          .payment-details .info-row {
            border-bottom: 3px solid rgba(11, 11, 11, 0.25);
            padding: 20px 0;
            margin: 25px 0;
          }
          .payment-details .info-label {
            color: #0B0B0B;
            font-weight: 800;
            font-size: 32px;
          }
          .payment-details .info-value {
            color: #0B0B0B;
            font-weight: 800;
            font-size: 32px;
          }
          .amount {
            font-size: 88px;
            font-weight: 900;
            color: #0B0B0B;
            text-align: center;
            margin: 50px 0 30px 0;
            padding: 45px;
            background: rgba(255, 255, 255, 0.6);
            border-radius: 20px;
            letter-spacing: 3px;
            border: 4px solid rgba(11, 11, 11, 0.2);
          }
          .footer {
            text-align: center;
            margin-top: 60px;
            padding-top: 35px;
            border-top: 5px solid #e9ecef;
            color: #6c757d;
            page-break-inside: avoid;
          }
          .footer p {
            margin: 15px 0;
            font-size: 28px;
            line-height: 1.8;
          }
          .footer strong {
            color: #0B0B0B;
            font-size: 30px;
          }
          .status {
            display: inline-block;
            padding: 15px 35px;
            border-radius: 35px;
            font-weight: 900;
            font-size: 30px;
            background: ${payment.status === 'COMPLETED' ? '#10B981' : '#EF4444'};
            color: white;
            text-transform: uppercase;
            letter-spacing: 3px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
          }
          .txn-id {
            font-family: 'Courier New', monospace;
            font-weight: 900;
            letter-spacing: 3px;
            font-size: 32px;
          }
          @media print {
            body {
              padding: 10mm;
              font-size: 28px;
            }
            .payment-details {
              box-shadow: none;
            }
            .header, .receipt-info, .payment-details, .footer {
              page-break-inside: avoid;
            }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <img src="${window.location.origin}${modernLogo}" alt="Modern Fitness Gym Logo" class="logo" />
          <h1 class="gym-name">Modern Fitness Gym</h1>
          <p class="receipt-title">Payment Receipt</p>
          <p class="receipt-date">Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>

        <div class="receipt-info">
          <div class="info-section">
            <h3>Member Information</h3>
            <div class="info-row">
              <span class="info-label">Name:</span>
              <span class="info-value">${member.full_name || member.username}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Phone:</span>
              <span class="info-value">${member.phone || 'N/A'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">CNIC:</span>
              <span class="info-value">${member.cnic || 'N/A'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Email:</span>
              <span class="info-value">${member.email || 'N/A'}</span>
            </div>
          </div>

          <div class="info-section">
            <h3>Package Information</h3>
            <div class="info-row">
              <span class="info-label">Package:</span>
              <span class="info-value">${pkg ? pkg.name : 'Not Assigned'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Duration:</span>
              <span class="info-value">${pkg ? pkg.duration_days + ' days' : 'N/A'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Start Date:</span>
              <span class="info-value">${member.package_start_date ? new Date(member.package_start_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Not Set'}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Expiry Date:</span>
              <span class="info-value">${member.package_expiry_date ? new Date(member.package_expiry_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Not Set'}</span>
            </div>
          </div>
        </div>

        <div class="payment-details">
          <h2>Payment Details</h2>
          <div class="info-row">
            <span class="info-label">Receipt No:</span>
            <span class="info-value txn-id">#${shortTxnId}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Payment Status:</span>
            <span class="status">${payment.status}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Due Date:</span>
            <span class="info-value">${new Date(payment.due_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
          </div>
          ${payment.paid_date ? `
          <div class="info-row">
            <span class="info-label">Paid Date:</span>
            <span class="info-value">${new Date(payment.paid_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
          </div>
          ` : ''}
          <div class="amount">Rs. ${payment.amount.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>

          <div class="footer">
            <p style="font-size: 26px; margin-bottom: 15px; font-weight: 600;">Thank you for your payment!</p>
            <p style="font-size: 28px; font-weight: 600;">For any queries, please contact us at the gym reception.</p>
            <p style="margin-top: 20px; font-size: 32px;"><strong>Modern Fitness Gym</strong> - Your Fitness Partner</p>
          </div>
        </body>
      </html>
    `

    // Write content to iframe
    iframeDoc.open()
    iframeDoc.write(receiptContent)
    iframeDoc.close()
    
    // Wait for images to load, then print
    iframe.onload = () => {
      setTimeout(() => {
        iframe.contentWindow.focus()
        iframe.contentWindow.print()
        // Remove iframe after printing
        setTimeout(() => {
          document.body.removeChild(iframe)
        }, 1000)
      }, 1000)
    }
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
              Member <span className="fitnix-gradient-text">Management</span>
            </h1>
            <p className="text-fitnix-off-white/60 mt-2">
              Manage gym members, profiles, and access
            </p>
          </div>
          <button
            onClick={() => {
              if (showForm && !editingMember) {
                setShowForm(false)
                resetForm()
              } else if (editingMember) {
                handleCancelEdit()
              } else {
                // Refresh settings before opening form for new member
                fetchSettings().then(() => {
                  setShowForm(true)
                })
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
                <span>Add Member</span>
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
              {editingMember ? 'Edit Member' : 'Add New Member'}
            </h2>
            
            {/* Basic Information */}
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
                    Gender
                  </label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="fitnix-input"
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
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
              </div>
            </div>

            {/* Package Selection - Show for both new and edit */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-fitnix-lime mb-3">Package & Trainer Assignment</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Package
                  </label>
                  <select
                    value={formData.package_id}
                    onChange={(e) => setFormData({ ...formData, package_id: e.target.value })}
                    className="fitnix-input"
                  >
                    <option value="">No Package</option>
                    {packages.filter(pkg => pkg.is_active).map(pkg => (
                      <option key={pkg.id} value={pkg.id}>
                        {pkg.name} - Rs. {pkg.price} ({pkg.duration_days} days)
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-fitnix-off-white/50 mt-1">
                    {editingMember ? 'Update member package assignment' : 'Select a package for the new member'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                    Assigned Trainer
                  </label>
                  <select
                    value={formData.trainer_id}
                    onChange={(e) => setFormData({ ...formData, trainer_id: e.target.value })}
                    className="fitnix-input"
                  >
                    <option value="">No Trainer</option>
                    {trainers.map(trainer => (
                      <option key={trainer.id} value={trainer.id}>
                        {trainer.full_name} - {trainer.specialization}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-fitnix-off-white/50 mt-1">
                    Assign a personal trainer to this member
                  </p>
                </div>

                {formData.trainer_id && !editingMember && (
                  <div>
                    <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                      Trainer Charge (Rs.)
                    </label>
                    <div className="fitnix-card p-4 bg-fitnix-charcoal/50 border border-fitnix-lime/30">
                      <p className="text-lg font-bold text-fitnix-lime">
                        Rs. {(() => {
                          const trainer = trainers.find(t => t.id === formData.trainer_id)
                          return trainer ? parseFloat(trainer.salary_rate).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0'
                        })()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Package Dates - Only for editing */}
            {editingMember && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-fitnix-lime mb-3">Package Dates</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                      Package Start Date
                    </label>
                    <input
                      type="date"
                      value={formData.package_start_date ? formData.package_start_date.split('T')[0] : ''}
                      onChange={(e) => setFormData({ ...formData, package_start_date: e.target.value })}
                      className="fitnix-input"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                      Package Expiry Date
                    </label>
                    <input
                      type="date"
                      value={formData.package_expiry_date ? formData.package_expiry_date.split('T')[0] : ''}
                      onChange={(e) => setFormData({ ...formData, package_expiry_date: e.target.value })}
                      className="fitnix-input"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Payment Information - Only for new members */}
            {!editingMember && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-fitnix-lime mb-3">Admission Fee</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-fitnix-charcoal/50 border border-fitnix-lime/30 rounded-lg p-4">
                    <p className="text-sm text-fitnix-off-white/60 mb-1">Standard Admission Fee</p>
                    <p className="text-2xl font-bold text-fitnix-lime">Rs. {defaultAdmissionFee.toLocaleString('en-PK', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
                  </div>
                  
                  <div className="flex items-center">
                    <label className="flex items-center space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.waive_admission_fee}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          waive_admission_fee: e.target.checked,
                          discount: e.target.checked ? 0 : formData.discount
                        })}
                        className="w-5 h-5 text-fitnix-lime bg-fitnix-charcoal border-fitnix-off-white/20 rounded focus:ring-fitnix-lime focus:ring-2"
                      />
                      <span className="text-sm font-medium text-fitnix-off-white/80">
                        Waive Admission Fee
                      </span>
                    </label>
                  </div>
                  
                  {!formData.waive_admission_fee && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                          Discount Type
                        </label>
                        <select
                          value={formData.discount_type}
                          onChange={(e) => setFormData({ ...formData, discount_type: e.target.value, discount: 0 })}
                          className="fitnix-input"
                        >
                          <option value="fixed">Fixed Amount (Rs.)</option>
                          <option value="percentage">Percentage (%)</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                          Discount {formData.discount_type === 'percentage' ? '(%)' : '(Rs.)'}
                        </label>
                        <input
                          type="number"
                          placeholder={`Enter discount ${formData.discount_type === 'percentage' ? 'percentage' : 'amount'}`}
                          value={formData.discount}
                          onChange={(e) => setFormData({ ...formData, discount: parseFloat(e.target.value) || 0 })}
                          className="fitnix-input"
                          step="0.01"
                          min="0"
                          max={formData.discount_type === 'percentage' ? 100 : (() => {
                            let total = parseFloat(formData.admission_fee) || 0
                            if (formData.package_id) {
                              const pkg = packages.find(p => p.id === formData.package_id)
                              if (pkg) total += parseFloat(pkg.price) || 0
                            }
                            return total
                          })()}
                        />
                      </div>
                    </>
                  )}
                  
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-fitnix-off-white/80 mb-2">
                      Final Payable Amount
                    </label>
                    <div className="bg-fitnix-black border-2 border-fitnix-lime rounded-lg px-4 py-3">
                      {/* Breakdown */}
                      {!formData.waive_admission_fee && (
                        <div className="space-y-1 mb-3 pb-3 border-b border-fitnix-lime/20">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-fitnix-off-white/60">Admission Fee:</span>
                            <span className="text-fitnix-off-white">Rs. {parseFloat(formData.admission_fee || 0).toFixed(2)}</span>
                          </div>
                          {formData.package_id && (() => {
                            const pkg = packages.find(p => p.id === formData.package_id)
                            return pkg ? (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-fitnix-off-white/60">Package ({pkg.name}):</span>
                                <span className="text-fitnix-off-white">Rs. {parseFloat(pkg.price).toFixed(2)}</span>
                              </div>
                            ) : null
                          })()}
                          {formData.trainer_id && (() => {
                            const trainer = trainers.find(t => t.id === formData.trainer_id)
                            return trainer ? (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-fitnix-off-white/60">Trainer Fee:</span>
                                <span className="text-fitnix-off-white">Rs. {parseFloat(trainer.salary_rate).toFixed(2)}</span>
                              </div>
                            ) : null
                          })()}
                          {formData.discount > 0 && (
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-fitnix-off-white/60">Discount:</span>
                              <span className="text-cyan-400">
                                - Rs. {(() => {
                                  let total = parseFloat(formData.admission_fee || 0)
                                  if (formData.package_id) {
                                    const pkg = packages.find(p => p.id === formData.package_id)
                                    if (pkg) total += parseFloat(pkg.price)
                                  }
                                  if (formData.trainer_id) {
                                    const trainer = trainers.find(t => t.id === formData.trainer_id)
                                    if (trainer) total += parseFloat(trainer.salary_rate)
                                  }
                                  const discountAmount = formData.discount_type === 'percentage' 
                                    ? (total * formData.discount / 100) 
                                    : formData.discount
                                  return discountAmount.toFixed(2)
                                })()}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Total */}
                      <div className="flex items-center justify-between">
                        <span className="text-fitnix-off-white/60">Total Amount:</span>
                        <span className="text-2xl font-bold text-fitnix-lime">
                          Rs. {formData.final_payable.toFixed(2)}
                        </span>
                      </div>
                      
                      {/* Status messages */}
                      {formData.waive_admission_fee && (
                        <p className="text-xs text-amber-400 mt-2">✓ Admission fee waived</p>
                      )}
                      {!formData.waive_admission_fee && formData.discount > 0 && (
                        <p className="text-xs text-cyan-400 mt-2">
                          ✓ Discount applied: {formData.discount_type === 'percentage' ? `${formData.discount}%` : `Rs. ${formData.discount}`}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="flex space-x-3 mt-6">
              <button
                type="submit"
                className="flex-1 fitnix-button-primary"
              >
                {editingMember ? 'Update Member' : 'Create Member'}
              </button>
              {editingMember && (
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
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Phone</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Gender</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">DOB</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Admission</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Package</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Trainer</th>
                  <th className="px-6 py-5 text-center text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-fitnix-charcoal/30">
                {members.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <svg className="w-16 h-16 text-fitnix-off-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        <p className="text-fitnix-off-white/60 text-lg">No members found</p>
                        <p className="text-fitnix-off-white/40 text-sm">Add your first member to get started</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  members.map((member, index) => {
                    return (
                      <tr key={member.id} className={`hover:bg-fitnix-black/50 transition-colors border-b border-fitnix-lime/10 ${index % 2 === 0 ? 'bg-fitnix-charcoal/20' : 'bg-fitnix-charcoal/40'}`}>
                        <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{member.full_name || 'N/A'}</td>
                        <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{member.phone}</td>
                        <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">{member.gender || 'N/A'}</td>
                        <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">
                          {member.date_of_birth ? new Date(member.date_of_birth).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'N/A'}
                        </td>
                        <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">
                          {member.admission_date ? new Date(member.admission_date).toLocaleDateString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'N/A'}
                        </td>
                        <td className="px-6 py-6 text-base text-fitnix-off-white whitespace-nowrap">
                          {(() => {
                            const pkg = packages.find(p => p.id === member.current_package_id)
                            return pkg ? pkg.name : 'No Package'
                          })()}
                        </td>
                        <td className="px-6 py-6 text-sm text-fitnix-off-white whitespace-nowrap">
                          <div>
                            <div className="font-medium">{member.trainer_name || 'No Trainer'}</div>
                            {member.trainer_charges > 0 && (
                              <div className="text-xs text-fitnix-off-white/60 mt-1">
                                Charges: Rs. {member.trainer_charges.toLocaleString()}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-6">
                          <div className="flex flex-col gap-1.5 items-center">
                            <button
                              onClick={() => handleEdit(member)}
                              className="w-24 bg-fitnix-lime hover:bg-fitnix-dark-lime text-fitnix-black px-3 py-1.5 rounded transition-all font-semibold text-xs shadow-sm hover:scale-105"
                              title="Edit member"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleDelete(member)}
                              className="w-24 bg-red-600 hover:bg-red-500 text-white px-3 py-1.5 rounded transition-all font-semibold text-xs shadow-sm hover:scale-105"
                              title="Delete member"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>

      {/* Delete Confirmation Modal */}
      {deletingMember && (
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
              Delete Member?
            </h3>

            {/* Member Info */}
            <div className="bg-fitnix-black/50 rounded-lg p-4 mb-4 border border-red-500/30">
              <p className="text-fitnix-off-white/80 text-sm mb-2">You are about to delete:</p>
              <p className="text-fitnix-lime font-bold text-lg">{deletingMember.full_name}</p>
              <p className="text-fitnix-off-white/60 text-sm">Email: {deletingMember.email}</p>
              <p className="text-fitnix-off-white/60 text-sm">Phone: {deletingMember.phone}</p>
            </div>

            {/* Warning Message */}
            <p className="text-fitnix-off-white/80 text-center mb-6">
              This action <span className="text-red-500 font-bold">cannot be undone</span>. All member data, attendance records, and transactions will be permanently deleted.
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
                Delete Member
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  )
}
