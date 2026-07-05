import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Building2, CalendarDays, Phone, ShieldCheck, UserRound } from 'lucide-react'
import { api } from '../../services/api'
import { normalizeUser } from '../../services/userService'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminDetail.scss'

export function AdminUserDetail() {
  const { userId } = useParams()
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUserDetail = async () => {
      try {
        const { data } = await api.get(`/admin/users/${userId}/detail`)
        setUser(normalizeUser(data.user))
        setListings(data.listings || [])
      } finally {
        setLoading(false)
      }
    }

    void fetchUserDetail()
  }, [userId])

  const toggleStatus = async () => {
    if (!user || user.rol === 'admin') return
    const { data } = await api.patch(`/admin/users/${user.id}/status`, { verified: !user.verified })
    setUser(normalizeUser(data.user))
  }

  const formatDate = (value) => value
    ? new Intl.DateTimeFormat('uz-UZ', { year: 'numeric', month: 'short', day: 'numeric' }).format(new Date(value))
    : '-'

  if (loading) {
    return (
      <main className="admin-detail">
        <div className="page-container">
          <AdminBreadcrumb current="Foydalanuvchi" />
          <div className="detail-loading">Foydalanuvchi ma'lumotlari yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="admin-detail">
      <div className="page-container">
        <AdminBreadcrumb current={`Foydalanuvchilar / ${user?.ism || userId}`} />

        <section className="detail-hero">
          <div className="detail-avatar"><UserRound size={34} /></div>
          <div>
            <p className="eyebrow">Foydalanuvchi profili</p>
            <h1>{user?.ism || '-'}</h1>
            <div className="meta-row">
              <span><Phone size={15} /> {user?.telefon || '-'}</span>
              <span><ShieldCheck size={15} /> {user?.verified ? 'Faol' : 'Nofaol'}</span>
              <span><CalendarDays size={15} /> {formatDate(user?.created_at)}</span>
            </div>
          </div>
          <button className={`status-action ${user?.verified ? 'deactivate' : 'activate'}`} onClick={toggleStatus} disabled={user?.rol === 'admin'}>
            {user?.verified ? 'Nofaol qilish' : 'Faol qilish'}
          </button>
        </section>

        <section className="detail-panel">
          <div className="panel-title">
            <Building2 size={20} />
            <h2>Reklamalari</h2>
            <span>{listings.length} ta</span>
          </div>

          <div className="detail-table-wrap">
            <table className="detail-table">
              <thead>
                <tr>
                  <th>E'lon</th>
                  <th>Narx</th>
                  <th>Holati</th>
                  <th>Izoh</th>
                  <th>Sana</th>
                </tr>
              </thead>
              <tbody>
                {listings.length === 0 ? (
                  <tr><td colSpan="5" className="empty">Bu foydalanuvchida e'lon yo'q</td></tr>
                ) : listings.map((listing) => (
                  <tr key={listing.id} onClick={() => navigate(`/admin/listings/${listing.id}`)}>
                    <td>{listing.manzil || `${listing.tuman}, ${listing.viloyat}`}</td>
                    <td>{Number(listing.narx_usd || 0).toLocaleString('uz-UZ')} USD</td>
                    <td><span className={`pill ${listing.faol ? 'active' : 'inactive'}`}>{listing.faol ? 'Faol' : 'Nofaol'}</span></td>
                    <td>{listing.reviews_count || 0}</td>
                    <td>{formatDate(listing.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  )
}
