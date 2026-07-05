import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, BadgeDollarSign, Building2, ClipboardList, Crown, ShieldCheck, Users } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { api } from '../../services/api'
import './AdminDashboard.scss'

export function AdminDashboard() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const [stats, setStats] = useState({
    totalUsers: 0,
    verifiedUsers: 0,
    totalListings: 0,
    totalRevenue: 0,
    complaints: 0,
    roleCounts: {},
    limits: {},
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!accessToken) {
      navigate('/login')
      return
    }

    const fetchStats = async () => {
      try {
        const { data } = await api.get('/admin/dashboard')
        setStats({
          totalUsers: data.users ?? 0,
          verifiedUsers: data.verified_users ?? 0,
          totalListings: data.listings ?? 0,
          totalRevenue: data.revenue ?? 0,
          complaints: data.complaints ?? 0,
          roleCounts: data.role_counts ?? {},
          limits: data.limits ?? {},
        })
      } finally {
        setLoading(false)
      }
    }

    void fetchStats()
  }, [accessToken, navigate])

  const formatMoney = (value) =>
    new Intl.NumberFormat('uz-UZ', { maximumFractionDigits: 0 }).format(Number(value || 0))

  const limitRows = [
    { key: 'owner', label: 'Uy egasi', description: "Uy egasi e'lon limiti" },
    { key: 'makler', label: 'Makler', description: "Makler e'lon limiti" },
    { key: 'admin', label: 'Admin', description: 'Admin boshqaruv limiti' },
  ]

  return (
    <main className="admin-dashboard">
      <div className="page-container">
        <header className="admin-dashboard__header">
          <div>
            <p className="eyebrow">Admin panel</p>
            <h1>{t('admin.dashboard', 'Admin boshqaruv paneli')}</h1>
          </div>
          <button className="profile-shortcut" onClick={() => navigate('/admin/profile')}>
            <ShieldCheck size={18} />
            Admin profil
          </button>
        </header>

        {loading ? (
          <div className="dashboard-loading">{t('common.loading', 'Yuklanmoqda...')}</div>
        ) : (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon"><Users size={22} /></div>
                <div className="stat-content">
                  <div className="stat-value">{stats.totalUsers}</div>
                  <div className="stat-label">{t('admin.total_users', 'Jami foydalanuvchilar')}</div>
                  <span>{stats.verifiedUsers} tasdiqlangan</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon"><Building2 size={22} /></div>
                <div className="stat-content">
                  <div className="stat-value">{stats.totalListings}</div>
                  <div className="stat-label">{t('admin.total_listings', "Jami e'lonlar")}</div>
                  <span>Jami aktiv e'lonlar</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon"><BadgeDollarSign size={22} /></div>
                <div className="stat-content">
                  <div className="stat-value">{formatMoney(stats.totalRevenue)} so'm</div>
                  <div className="stat-label">{t('admin.total_revenue', 'Jami tushum')}</div>
                  <span>To'lovlardan tushum</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon"><AlertTriangle size={22} /></div>
                <div className="stat-content">
                  <div className="stat-value">{stats.complaints}</div>
                  <div className="stat-label">{t('admin.complaints', 'Shikoyatlar')}</div>
                  <span>Ko'rib chiqilishi kerak</span>
                </div>
              </div>
            </div>

            <section className="limit-panel">
              <div className="section-title">
                <ClipboardList size={20} />
                <h2>Rol bo'yicha limitlar</h2>
              </div>
              <div className="limit-grid">
                {limitRows.map((item) => {
                  const limit = stats.limits[item.key] ?? { simple: 0, premium: 0 }
                  return (
                    <div className="limit-card" key={item.key}>
                      <div className="limit-card__top">
                        <div>
                          <strong>{item.label}</strong>
                          <p>{item.description}</p>
                        </div>
                        <span>{stats.roleCounts[item.key] ?? 0} foydalanuvchi</span>
                      </div>
                      <div className="limit-values">
                        <div><small>Oddiy</small><b>{limit.simple}</b></div>
                        <div><small>Premium</small><b>{limit.premium}</b></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </section>

            <div className="admin-links">
              <button onClick={() => navigate('/admin/users')} className="admin-link">
                <Users size={18} /> Foydalanuvchilar
              </button>
              <button onClick={() => navigate('/admin/listings')} className="admin-link">
                <Building2 size={18} /> E'lonlar
              </button>
              <button onClick={() => navigate('/admin/complaints')} className="admin-link">
                <AlertTriangle size={18} /> Shikoyatlar
              </button>
              <button onClick={() => navigate('/admin/revenue')} className="admin-link">
                <Crown size={18} /> Tushum
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
