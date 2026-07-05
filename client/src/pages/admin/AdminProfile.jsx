import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CalendarDays, CheckCircle2, ClipboardList, LogOut, Phone, ShieldCheck, UserRound } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { userService } from '../../services/userService'
import { api } from '../../services/api'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminProfile.scss'

export function AdminProfile() {
  const navigate = useNavigate()
  const { accessToken, clear } = useAuthStore()
  const [admin, setAdmin] = useState(null)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!accessToken) {
      navigate('/login?admin=true')
      return
    }

    const fetchAdminProfile = async () => {
      try {
        const [userData, dashboardData] = await Promise.all([
          userService.getCurrentUser(),
          api.get('/admin/dashboard').then((res) => res.data),
        ])

        if (userData.rol !== 'admin') {
          navigate('/profile', { replace: true })
          return
        }

        setAdmin(userData)
        setSummary(dashboardData)
      } finally {
        setLoading(false)
      }
    }

    void fetchAdminProfile()
  }, [accessToken, navigate])

  const joinedAt = admin?.created_at
    ? new Intl.DateTimeFormat('uz-UZ', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }).format(new Date(admin.created_at))
    : '-'

  const handleLogout = () => {
    clear()
    navigate('/')
  }

  if (loading) {
    return (
      <main className="admin-profile">
        <div className="admin-profile__shell">
          <div className="admin-profile__loading">Admin profil yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="admin-profile">
      <div className="admin-profile__shell">
        <AdminBreadcrumb current="Profile" />
        <section className="admin-hero">
          <div className="admin-avatar" aria-hidden="true">
            {admin?.rasm_url ? <img src={admin.rasm_url} alt="" /> : <UserRound size={38} />}
          </div>
          <div className="admin-identity">
            <p className="eyebrow">Admin account</p>
            <h1>{admin?.ism || 'Admin'}</h1>
            <div className="admin-badges">
              <span><ShieldCheck size={15} /> {admin?.rol}</span>
              <span><CheckCircle2 size={15} /> {admin?.verified ? 'Tasdiqlangan' : 'Tasdiqlanmagan'}</span>
            </div>
          </div>
          <button className="logout-admin" onClick={handleLogout}>
            <LogOut size={18} />
            Chiqish
          </button>
        </section>

        <section className="admin-profile-grid">
          <div className="profile-panel">
            <div className="panel-title">
              <UserRound size={19} />
              <h2>Shaxsiy ma'lumotlar</h2>
            </div>
            <dl className="info-list">
              <div>
                <dt>Ism familya</dt>
                <dd>{admin?.ism || '-'}</dd>
              </div>
              <div>
                <dt>Telefon</dt>
                <dd><Phone size={15} /> {admin?.telefon || '-'}</dd>
              </div>
              <div>
                <dt>Admin ID</dt>
                <dd>#{admin?.id}</dd>
              </div>
              <div>
                <dt>Qo'shilgan sana</dt>
                <dd><CalendarDays size={15} /> {joinedAt}</dd>
              </div>
            </dl>
          </div>

          <div className="profile-panel">
            <div className="panel-title">
              <ClipboardList size={19} />
              <h2>Admin nazorati</h2>
            </div>
            <div className="control-stats">
              <div>
                <span>Foydalanuvchilar</span>
                <strong>{summary?.users ?? 0}</strong>
              </div>
              <div>
                <span>E'lonlar</span>
                <strong>{summary?.listings ?? 0}</strong>
              </div>
              <div>
                <span>Shikoyatlar</span>
                <strong>{summary?.complaints ?? 0}</strong>
              </div>
            </div>
            <button className="dashboard-link" onClick={() => navigate('/admin')}>
              Dashboardga qaytish
            </button>
          </div>
        </section>
      </div>
    </main>
  )
}
