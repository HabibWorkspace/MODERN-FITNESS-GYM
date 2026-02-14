import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../../services/api'
import AdminLayout from '../../components/layouts/AdminLayout'
import logo from '/fitcore-logo.png'
import modernLogo from '/modern-fitness-logo.png'

export default function AdminFinance() {
  const [transactions, setTransactions] = useState([])
  const [members, setMembers] = useState({})
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showPrintModal, setShowPrintModal] = useState(null)
  const navigate = useNavigate()

  // Filter states
  const [selectedMember, setSelectedMember] = useState('all')
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [filteredTransactions, setFilteredTransactions] = useState([])

  useEffect(() => {
    fetchData()
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

  // Apply filters whenever transactions or filter values change
  useEffect(() => {
    applyFilters()
  }, [transactions, selectedMember, selectedStatus, selectedMonth])

  const applyFilters = () => {
    let filtered = [...transactions]

    // Filter by member
    if (selectedMember !== 'all') {
      filtered = filtered.filter(t => t.member_id === selectedMember)
    }

    // Filter by status
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(t => t.status === selectedStatus)
    }

    // Filter by month
    if (selectedMonth) {
      const [year, month] = selectedMonth.split('-')
      filtered = filtered.filter(t => {
        if (!t.due_date) return false
        const dueDate = new Date(t.due_date)
        return dueDate.getFullYear() === parseInt(year) && 
               (dueDate.getMonth() + 1) === parseInt(month)
      })
    }

    setFilteredTransactions(filtered)
  }

  const handleResetFilters = () => {
    setSelectedMember('all')
    setSelectedStatus('all')
    setSelectedMonth('')
  }

  const fetchData = async () => {
    try {
      const cacheParam = `?_t=${Date.now()}`
      const [paymentsRes, packagesRes, membersRes] = await Promise.all([
        apiClient.get(`/admin/finance/member-payments-fixed${cacheParam}`),
        apiClient.get(`/packages${cacheParam}`),
        apiClient.get(`/admin/members${cacheParam}`)
      ])
      
      setTransactions(paymentsRes.data.payments || [])
      setPackages(packagesRes.data.packages || [])
      
      // Create a map of member_id to full member info
      const memberMap = {}
      const membersList = membersRes.data.members || []
      membersList.forEach(member => {
        memberMap[member.id] = member
      })
      setMembers(memberMap)
    } catch (err) {
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleMarkPaid = async (transactionId) => {
    // Get transaction data BEFORE marking as paid
    const transaction = transactions.find(t => t.id === transactionId)
    if (!transaction) {
      setError('Transaction not found')
      return
    }
    
    try {
      // Prepare request body - include data for virtual transactions
      const requestBody = {
        member_id: transaction.member_id,
        amount: transaction.amount,
        due_date: transaction.due_date
      }
      
      await apiClient.post(`/admin/finance/transactions/${transactionId}/mark-paid`, requestBody)
      setSuccess('Payment marked as paid successfully')
      
      // Refresh data
      await fetchData()
      
      // Show stylish print modal after marking as paid
      setTimeout(() => {
        setShowPrintModal(transaction)
      }, 300)
    } catch (err) {
      setError('Failed to mark payment')
      console.error('Mark paid error:', err)
    }
  }

  const handlePrintReceipt = (transaction) => {
    const member = members[transaction.member_id]
    if (!member) {
      setError('Member information not found')
      return
    }

    const pkg = packages.find(p => p.id === member.current_package_id)
    
    // Generate short transaction ID (last 8 characters)
    const shortTxnId = transaction.id.slice(-8).toUpperCase()
    
    // Create receipt content
    const receiptContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Payment Receipt - ${member.full_name || member.username}</title>
        <style>
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          body {
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 700px;
            margin: 0 auto;
            padding: 15px;
            background: #fff;
            color: #1a1a1a;
          }
          .receipt-meta {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 4px;
            font-size: 9px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          .receipt-meta-left {
            color: #666;
          }
          .receipt-meta-right {
            text-align: right;
          }
          .receipt-meta-right div {
            margin: 1px 0;
          }
          .receipt-no {
            font-size: 10px;
            font-weight: 900;
            color: #000;
            letter-spacing: 1px;
          }
          .receipt-date {
            color: #666;
          }
          .header {
            text-align: center;
            border-bottom: 2px double #000;
            padding-bottom: 10px;
            margin-bottom: 12px;
          }
          .logo {
            width: 80px;
            height: auto;
            margin: 0 auto 8px;
            display: block;
          }
          .gym-name {
            font-size: 18px;
            font-weight: 900;
            margin: 5px 0 2px 0;
            letter-spacing: 1px;
            text-transform: uppercase;
          }
          .receipt-title {
            font-size: 11px;
            font-weight: 700;
            margin: 2px 0;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #333;
          }
          .section {
            margin-bottom: 12px;
            padding: 10px;
            border: 1px solid #000;
            position: relative;
            background: #fafafa;
          }
          .section-title {
            position: absolute;
            top: -8px;
            left: 10px;
            background: #fff;
            padding: 0 6px;
            font-weight: 900;
            font-size: 9px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #000;
          }
          .row {
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            margin: 4px 0;
            padding: 3px 0;
            border-bottom: 1px dotted #ccc;
          }
          .row:last-child {
            border-bottom: none;
          }
          .label {
            font-weight: 700;
            color: #333;
            text-transform: uppercase;
            font-size: 9px;
            letter-spacing: 0.3px;
          }
          .value {
            text-align: right;
            color: #000;
            font-weight: 600;
          }
          .amount-section {
            margin: 12px 0;
            padding: 15px;
            border: 2px double #000;
            background: #f5f5f5;
            text-align: center;
          }
          .amount-label {
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 6px;
          }
          .amount-box {
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 1px;
            color: #000;
          }
          .disclaimer {
            text-align: center;
            font-size: 9px;
            font-weight: 900;
            margin: 12px 0;
            padding: 8px;
            border: 2px solid #000;
            background: #fff;
            letter-spacing: 0.3px;
            text-transform: uppercase;
          }
          .footer {
            text-align: center;
            margin-top: 12px;
            padding-top: 10px;
            border-top: 2px double #000;
            font-size: 9px;
            line-height: 1.4;
          }
          .footer p {
            margin: 2px 0;
          }
          .footer-thank-you {
            font-weight: 900;
            font-size: 14px;
            margin: 6px 0 4px 0;
            letter-spacing: 0.5px;
            text-transform: uppercase;
          }
          .footer-brand {
            font-weight: 900;
            font-size: 10px;
            margin-top: 6px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
          }
          @media print {
            body {
              padding: 15px;
              margin: 0;
            }
          }
        </style>
      </head>
      <body>
        <div class="receipt-meta">
          <div class="receipt-meta-left">
            Payment Receipt
          </div>
          <div class="receipt-meta-right">
            <div class="receipt-no">Receipt #${shortTxnId}</div>
            <div class="receipt-date">Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</div>
          </div>
        </div>

        <div class="header">
          <img src="${window.location.origin}${modernLogo}" alt="Modern Fitness Gym Logo" class="logo" />
          <div class="gym-name">Modern Fitness Gym</div>
          <div class="receipt-title">Payment Receipt</div>
        </div>

        <div class="section">
          <div class="section-title">Member Information</div>
          <div class="row">
            <span class="label">Name:</span>
            <span class="value">${member.full_name || member.username}</span>
          </div>
          <div class="row">
            <span class="label">Phone:</span>
            <span class="value">${member.phone || 'N/A'}</span>
          </div>
          <div class="row">
            <span class="label">CNIC:</span>
            <span class="value">${member.cnic || 'N/A'}</span>
          </div>
          <div class="row">
            <span class="label">Email:</span>
            <span class="value">${member.email || 'N/A'}</span>
          </div>
          ${member.trainer_name ? `
          <div class="row">
            <span class="label">Assigned Trainer:</span>
            <span class="value">${member.trainer_name}</span>
          </div>
          ` : ''}
        </div>

        <div class="section">
          <div class="section-title">Package Information</div>
          <div class="row">
            <span class="label">Package:</span>
            <span class="value">${pkg ? pkg.name : 'Not Assigned'}</span>
          </div>
          <div class="row">
            <span class="label">Start Date:</span>
            <span class="value">${member.package_start_date ? new Date(member.package_start_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Not Set'}</span>
          </div>
          <div class="row">
            <span class="label">Expiry Date:</span>
            <span class="value">${member.package_expiry_date ? new Date(member.package_expiry_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Not Set'}</span>
          </div>
        </div>

        <div class="section">
          <div class="section-title">Payment Details</div>
          <div class="row">
            <span class="label">Payment Month:</span>
            <span class="value">${new Date(transaction.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</span>
          </div>
          ${transaction.transaction_type === 'ADMISSION' ? `
          <div class="row">
            <span class="label">Admission Fee:</span>
            <span class="value">Rs. ${(() => {
              // Calculate admission fee: amount + discount - trainer_fee - package_price
              let admissionFee = parseFloat(transaction.amount) + parseFloat(transaction.discount_amount || 0) - parseFloat(transaction.trainer_fee || 0) - parseFloat(transaction.package_price || 0)
              return Math.max(0, admissionFee).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            })()}</span>
          </div>
          ` : ''}
          ${transaction.package_price && transaction.package_price > 0 ? `
          <div class="row">
            <span class="label">Package:</span>
            <span class="value">Rs. ${parseFloat(transaction.package_price).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          ` : ''}
          ${transaction.trainer_fee && transaction.trainer_fee > 0 ? `
          <div class="row">
            <span class="label">Trainer Fee:</span>
            <span class="value">Rs. ${parseFloat(transaction.trainer_fee).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          ` : ''}
          ${transaction.discount_amount && transaction.discount_amount > 0 ? `
          <div class="row">
            <span class="label">Discount:</span>
            <span class="value">- ${transaction.discount_type === 'percentage' ? `${((transaction.discount_amount / (transaction.amount + transaction.discount_amount)) * 100).toFixed(2)}%` : `Rs. ${parseFloat(transaction.discount_amount).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}</span>
          </div>
          ` : ''}
          ${transaction.paid_date ? `
          <div class="row">
            <span class="label">Paid Date:</span>
            <span class="value">${new Date(transaction.paid_date).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
          </div>
          ` : ''}
        </div>

        <div class="amount-section">
          <div class="amount-label">TOTAL PAYABLE AMOUNT</div>
          <div class="amount-box">Rs. ${transaction.amount.toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>

        <div class="disclaimer">
          FEES ONCE PAID IS NON-REFUNDABLE
        </div>

        <div class="footer">
          <div class="footer-thank-you">THANK YOU</div>
          <p>For any queries, please contact us at the gym reception.</p>
          <div class="footer-brand">MODERN FITNESS GYM - Ladies & Gents</div>
        </div>
      </body>
      </html>
    `

    // Open print window
    const printWindow = window.open('', '_blank')
    printWindow.document.write(receiptContent)
    printWindow.document.close()
    printWindow.focus()
    
    // Wait for content to load then print
    setTimeout(() => {
      printWindow.print()
    }, 250)
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
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-fitnix-off-white">
            Finance <span className="fitnix-gradient-text">Management</span>
          </h1>
          <p className="text-fitnix-off-white/60 mt-2">
            Track payments and manage financial transactions
          </p>
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

        {/* Filter Section */}
        <div className="fitnix-card-glow p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
            {/* Member Filter */}
            <div>
              <label className="block text-sm font-semibold text-fitnix-off-white mb-2">
                Member
              </label>
              <select
                value={selectedMember}
                onChange={(e) => setSelectedMember(e.target.value)}
                className="w-full bg-fitnix-black text-fitnix-off-white border border-fitnix-off-white/20 rounded-lg px-4 py-2.5 focus:outline-none focus:border-fitnix-lime transition-colors"
              >
                <option value="all">All Members</option>
                {Object.values(members).map(member => (
                  <option key={member.id} value={member.id}>
                    {member.full_name || member.username}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-semibold text-fitnix-off-white mb-2">
                Status
              </label>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="w-full bg-fitnix-black text-fitnix-off-white border border-fitnix-off-white/20 rounded-lg px-4 py-2.5 focus:outline-none focus:border-fitnix-lime transition-colors"
              >
                <option value="all">All Status</option>
                <option value="PENDING">PENDING</option>
                <option value="OVERDUE">OVERDUE</option>
                <option value="COMPLETED">COMPLETED</option>
              </select>
            </div>

            {/* Month Filter */}
            <div>
              <label className="block text-sm font-semibold text-fitnix-off-white mb-2">
                Month
              </label>
              <input
                type="month"
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(e.target.value)}
                className="w-full bg-fitnix-black text-fitnix-off-white border border-fitnix-off-white/20 rounded-lg px-4 py-2.5 focus:outline-none focus:border-fitnix-lime transition-colors hover:border-fitnix-lime/50 cursor-pointer"
                style={{
                  colorScheme: 'dark'
                }}
              />
            </div>

            {/* Reset Button */}
            <div>
              <button
                onClick={handleResetFilters}
                className="w-full bg-fitnix-charcoal hover:bg-fitnix-black text-fitnix-off-white font-bold py-2.5 px-6 rounded-lg transition-all border border-fitnix-off-white/20 hover:border-fitnix-lime/50"
              >
                Reset Filters
              </button>
            </div>
          </div>
        </div>

        <div className="fitnix-card overflow-hidden" style={{ border: 'none' }}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-fitnix-black border-b-2 border-fitnix-lime/30">
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap w-1/6">Month</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap w-1/4">Member</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap w-1/6">Total Amount</th>
                  <th className="px-6 py-5 text-left text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap w-1/4">Due Date</th>
                  <th className="px-6 py-5 text-center text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap w-1/12">Status</th>
                  <th className="px-6 py-5 text-center text-sm font-bold text-fitnix-lime uppercase tracking-wider whitespace-nowrap w-1/12">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-fitnix-charcoal/30">
                {filteredTransactions.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center">
                      <div className="flex flex-col items-center justify-center space-y-3">
                        <svg className="w-16 h-16 text-fitnix-off-white/20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                        <p className="text-fitnix-off-white/60 text-lg">No transactions found</p>
                        <p className="text-fitnix-off-white/40 text-sm">Transactions will appear here</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredTransactions.map((transaction, index) => {
                    const member = members[transaction.member_id]
                    const memberName = member ? (member.full_name || member.username) : transaction.member_id
                    return (
                      <tr key={transaction.id} className={`hover:bg-fitnix-black/50 transition-colors border-b border-fitnix-lime/10 ${index % 2 === 0 ? 'bg-fitnix-charcoal/20' : 'bg-fitnix-charcoal/40'}`}>
                        <td className="px-6 py-6 text-base text-fitnix-off-white font-semibold whitespace-nowrap">
                          {transaction.due_date ? new Date(transaction.due_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : 'N/A'}
                        </td>
                        <td className="px-6 py-6 text-base text-fitnix-off-white font-semibold whitespace-nowrap overflow-hidden text-ellipsis" title={memberName}>
                          {memberName}
                        </td>
                        <td className="px-6 py-6 text-base text-fitnix-lime font-bold whitespace-nowrap">
                          Rs. {parseFloat(transaction.amount || 0).toLocaleString('en-PK', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-6 text-sm text-fitnix-off-white">
                          <div className="flex flex-col">
                            <span className="whitespace-nowrap">
                              {transaction.due_date ? new Date(transaction.due_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : 'N/A'}
                            </span>
                            {transaction.status === 'COMPLETED' && transaction.paid_date && (
                              <span className="text-xs text-fitnix-lime/70 mt-1 whitespace-nowrap">
                                Paid: {new Date(transaction.paid_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-6 text-center">
                          <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border whitespace-nowrap ${
                            transaction.status === 'COMPLETED' 
                              ? 'bg-fitnix-black text-emerald-400 border-emerald-500' 
                              : transaction.status === 'OVERDUE'
                              ? 'bg-red-900/30 text-red-400 border-red-500'
                              : 'bg-fitnix-black text-amber-400 border-amber-500'
                          }`}>
                            {transaction.status}
                          </span>
                        </td>
                        <td className="px-6 py-6">
                          <div className="flex flex-col gap-1.5 items-center">
                            {transaction.status !== 'COMPLETED' ? (
                              <button
                                onClick={() => handleMarkPaid(transaction.id)}
                                className="w-20 bg-fitnix-lime hover:bg-fitnix-dark-lime text-fitnix-black px-2 py-1 rounded-md transition-all font-semibold text-xs shadow-md hover:scale-105 whitespace-nowrap"
                              >
                                Mark Paid
                              </button>
                            ) : (
                              <button
                                onClick={() => handlePrintReceipt(transaction)}
                                className="w-20 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 border border-cyan-500 px-2 py-1 rounded-md transition-all font-semibold text-xs shadow-md hover:scale-105 flex items-center justify-center gap-1 whitespace-nowrap"
                              >
                                <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                                </svg>
                                Print
                              </button>
                            )}
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

        {/* Stylish Print Receipt Modal */}
        {showPrintModal && (
          <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fadeIn">
            <div className="bg-fitnix-charcoal border-2 border-fitnix-lime rounded-2xl p-8 max-w-md w-full shadow-2xl shadow-fitnix-lime/20">
              <div className="flex items-center justify-center mb-6">
                <div className="w-20 h-20 bg-fitnix-lime rounded-full flex items-center justify-center animate-pulse">
                  <svg className="w-10 h-10 text-fitnix-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              
              <h3 className="text-2xl font-bold text-fitnix-off-white mb-3 text-center">Payment Successful!</h3>
              <p className="text-fitnix-off-white/60 text-center mb-8">
                Would you like to print the receipt now?
              </p>
              
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    handlePrintReceipt(showPrintModal)
                    setShowPrintModal(null)
                  }}
                  className="flex-1 bg-fitnix-lime hover:bg-fitnix-dark-lime text-fitnix-black font-bold py-3 px-6 rounded-xl transition-all hover:scale-105 shadow-lg hover:shadow-fitnix-lime/50 uppercase tracking-wide flex items-center justify-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                  </svg>
                  Print Receipt
                </button>
                <button
                  onClick={() => setShowPrintModal(null)}
                  className="flex-1 bg-fitnix-black hover:bg-fitnix-black/80 text-fitnix-off-white font-bold py-3 px-6 rounded-xl transition-all border-2 border-fitnix-off-white/20 hover:border-fitnix-off-white/40 uppercase tracking-wide"
                >
                  Skip
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
