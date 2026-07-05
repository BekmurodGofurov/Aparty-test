import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowLeft,
  Edit2,
  Loader,
  Trash2,
  CheckCircle,
  Clock,
  XCircle,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import {
  getPayments,
  updatePaymentStatus,
  editPayment,
  deletePayment,
} from '../../services/paymentService'
import './MaklerPayments.scss'

const formatDate = (value) => {
  if (!value) return '-'
  return new Intl.DateTimeFormat('uz-UZ', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

const formatMoney = (value) =>
  new Intl.NumberFormat('uz-UZ', { maximumFractionDigits: 0 }).format(Number(value || 0))

const getStatusColor = (status) => {
  switch (status) {
    case 'paid':
      return 'success'
    case 'pending':
      return 'warning'
    case 'overdue':
      return 'danger'
    default:
      return 'default'
  }
}

const getStatusIcon = (status) => {
  switch (status) {
    case 'paid':
      return <CheckCircle size={16} />
    case 'pending':
      return <Clock size={16} />
    case 'overdue':
      return <AlertTriangle size={16} />
    default:
      return null
  }
}

export function MaklerPayments() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingId, setEditingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)
  const [formData, setFormData] = useState({ amount: '', month: '', status: 'pending' })
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!accessToken) {
      navigate('/login')
      return
    }

    const fetchPayments = async () => {
      try {
        setLoading(true)
        const data = await getPayments(0, 50)
        setPayments(Array.isArray(data) ? data : [])
      } catch (err) {
        console.error('Tolovlarni yuklashda xatolik:', err)
        setError('Tolovlarni yuklashda xatolik yuz berdi')
      } finally {
        setLoading(false)
      }
    }

    void fetchPayments()
  }, [accessToken, navigate])

  const handleEditClick = (payment) => {
    setEditingId(payment.id)
    setFormData({
      amount: payment.amount,
      month: payment.month,
      status: payment.status,
    })
  }

  const handleSaveEdit = async () => {
    try {
      const updated = await editPayment(editingId, formData)
      setPayments((prev) =>
        prev.map((p) => (p.id === editingId ? updated : p))
      )
      setEditingId(null)
    } catch (err) {
      console.error('Tolovni tahrirlashda xatolik:', err)
      setError('Tolovni tahrirlashda xatolik yuz berdi')
    }
  }

  const handleStatusChange = async (paymentId, newStatus) => {
    try {
      const updated = await updatePaymentStatus(paymentId, newStatus)
      setPayments((prev) =>
        prev.map((p) => (p.id === paymentId ? updated : p))
      )
    } catch (err) {
      console.error("Tolov holatini o'zgartirishda xatolik:", err)
      setError("Tolov holatini o'zgartirishda xatolik yuz berdi")
    }
  }

  const handleConfirmDelete = async () => {
    try {
      await deletePayment(deletingId)
      setPayments((prev) => prev.filter((p) => p.id !== deletingId))
      setDeletingId(null)
    } catch (err) {
      console.error('Tolovni o\'chirishda xatolik:', err)
      setError("Tolovni o'chirishda xatolik yuz berdi")
    }
  }

  return (
    <main className="makler-payments">
      <div className="page-container">
        <div className="payments-header">
          <button
            className="back-button"
            onClick={() => navigate('/makler')}
            aria-label="Orqaga"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <p className="eyebrow">Tolovlar boshqaruvi</p>
            <h1>Earnings Management</h1>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            <p>{error}</p>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        {loading ? (
          <div className="loading-state">
            <Loader size={32} className="spinner" />
            <p>Tolovlar yuklanmoqda...</p>
          </div>
        ) : payments.length === 0 ? (
          <div className="empty-state">
            <p>Hozircha tolov yo'q</p>
          </div>
        ) : (
          <div className="payments-grid">
            {payments.map((payment) => (
              <div key={payment.id} className="payment-card">
                <div className="payment-card__header">
                  <div className="payment-info">
                    <div className="payment-amount">{formatMoney(payment.amount)} so'm</div>
                    <div className="payment-month">{formatDate(payment.month)}</div>
                  </div>
                  <div className={`status-badge status-${getStatusColor(payment.status)}`}>
                    {getStatusIcon(payment.status)}
                    <span>{payment.status}</span>
                  </div>
                </div>

                <div className="payment-card__body">
                  <div className="payment-row">
                    <span className="label">Rental ID:</span>
                    <code>{payment.rental_id.substring(0, 8)}...</code>
                  </div>
                  <div className="payment-row">
                    <span className="label">Payer ID:</span>
                    <span>{payment.payer_id}</span>
                  </div>
                  <div className="payment-row">
                    <span className="label">Created:</span>
                    <span>{formatDate(payment.created_at)}</span>
                  </div>
                </div>

                <div className="payment-card__footer">
                  {editingId === payment.id ? (
                    <div className="edit-form">
                      <div className="form-group">
                        <label>Amount</label>
                        <input
                          type="number"
                          value={formData.amount}
                          onChange={(e) =>
                            setFormData({ ...formData, amount: e.target.value })
                          }
                          min="1"
                        />
                      </div>
                      <div className="form-group">
                        <label>Month</label>
                        <input
                          type="date"
                          value={formData.month}
                          onChange={(e) =>
                            setFormData({ ...formData, month: e.target.value })
                          }
                        />
                      </div>
                      <div className="form-group">
                        <label>Status</label>
                        <select
                          value={formData.status}
                          onChange={(e) =>
                            setFormData({ ...formData, status: e.target.value })
                          }
                        >
                          <option value="pending">Pending</option>
                          <option value="paid">Paid</option>
                          <option value="overdue">Overdue</option>
                        </select>
                      </div>
                      <div className="form-actions">
                        <button
                          className="btn btn-primary"
                          onClick={handleSaveEdit}
                        >
                          Saqlash
                        </button>
                        <button
                          className="btn btn-secondary"
                          onClick={() => setEditingId(null)}
                        >
                          Bekor qilish
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <select
                        className="status-select"
                        value={payment.status}
                        onChange={(e) =>
                          handleStatusChange(payment.id, e.target.value)
                        }
                      >
                        <option value="pending">Pending</option>
                        <option value="paid">Paid</option>
                        <option value="overdue">Overdue</option>
                      </select>
                      <div className="action-buttons">
                        <button
                          className="btn-icon btn-edit"
                          onClick={() => handleEditClick(payment)}
                          title="Tahrirlash"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          className="btn-icon btn-delete"
                          onClick={() => setDeletingId(payment.id)}
                          title="O'chirish"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deletingId && (
          <div className="modal-overlay">
            <div className="modal">
              <h2>Tolovni o'chirishni tasdiqlang</h2>
              <p>Bu tolov o'chiriladi. Bu amalni qaytarish mumkin emas.</p>
              <div className="modal-actions">
                <button
                  className="btn btn-secondary"
                  onClick={() => setDeletingId(null)}
                >
                  Bekor qilish
                </button>
                <button
                  className="btn btn-danger"
                  onClick={handleConfirmDelete}
                >
                  O'chirishni tasdiqlang
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
