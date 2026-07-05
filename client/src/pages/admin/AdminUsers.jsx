import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Edit3, Filter, Search, ShieldCheck, UserRound, Users } from 'lucide-react'
import { api } from '../../services/api'
import { normalizeUser } from '../../services/userService'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminUsers.scss'

const roleOptions = [
  { value: 'all', label: 'Barcha rollar' },
  { value: 'student', label: 'Talaba' },
  { value: 'owner', label: 'Uy egasi' },
  { value: 'makler', label: 'Makler' },
  { value: 'admin', label: 'Admin' },
]

const statusOptions = [
  { value: 'all', label: 'Barcha holatlar' },
  { value: 'active', label: 'Faol' },
  { value: 'inactive', label: 'Nofaol' },
]

function getPageItems(currentPage, pageCount) {
  if (pageCount <= 7) return Array.from({ length: pageCount }, (_, index) => index + 1)

  const start = Math.max(2, currentPage - 2)
  const end = Math.min(pageCount - 1, currentPage + 2)
  const middle = Array.from({ length: end - start + 1 }, (_, index) => start + index)

  return [
    1,
    ...(start > 2 ? ['dots-left'] : []),
    ...middle,
    ...(end < pageCount - 1 ? ['dots-right'] : []),
    pageCount,
  ]
}

export function AdminUsers() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(1)

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const { data } = await api.get('/admin/users')
        setUsers(data.map(normalizeUser))
      } finally {
        setLoading(false)
      }
    }
    void fetchUsers()
  }, [])

  const filteredUsers = useMemo(() => {
    const query = searchTerm.trim().toLowerCase()

    return users.filter((user) => {
      const matchesQuery = !query || [
        user.id,
        user.ism,
        user.telefon,
        user.email,
      ].some((value) => String(value ?? '').toLowerCase().includes(query))

      const matchesRole = roleFilter === 'all' || user.rol === roleFilter
      const matchesStatus = statusFilter === 'all'
        || (statusFilter === 'active' && user.verified)
        || (statusFilter === 'inactive' && !user.verified)

      return matchesQuery && matchesRole && matchesStatus
    })
  }, [users, searchTerm, roleFilter, statusFilter])

  const pageCount = Math.max(1, Math.ceil(filteredUsers.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const startIndex = (currentPage - 1) * pageSize
  const paginatedUsers = filteredUsers.slice(startIndex, startIndex + pageSize)
  const pageItems = getPageItems(currentPage, pageCount)

  const handleSearch = (value) => {
    setSearchTerm(value)
    setPage(1)
  }

  const handleRoleFilter = (value) => {
    setRoleFilter(value)
    setPage(1)
  }

  const handleStatusFilter = (value) => {
    setStatusFilter(value)
    setPage(1)
  }

  const handlePageSize = (value) => {
    setPageSize(Number(value))
    setPage(1)
  }

  const toggleUserStatus = async (event, user) => {
    event.stopPropagation()
    if (user.rol === 'admin') return

    const { data } = await api.patch(`/admin/users/${user.id}/status`, { verified: !user.verified })
    const updatedUser = normalizeUser(data.user)
    setUsers((items) => items.map((item) => item.id === updatedUser.id ? updatedUser : item))
  }

  return (
    <main className="admin-users">
      <div className="page-container">
        <AdminBreadcrumb current="Foydalanuvchilar" />
        <header className="admin-users__header">
          <div>
            <p className="eyebrow">Admin panel</p>
            <h1><Users size={30} /> Foydalanuvchilarni boshqarish</h1>
          </div>
          <div className="user-count">
            <strong>{filteredUsers.length}</strong>
            <span>topildi</span>
          </div>
        </header>

        <section className="user-tools" aria-label="Foydalanuvchi filtrlari">
          <label className="search-box">
            <Search size={18} />
            <input
              value={searchTerm}
              onChange={(event) => handleSearch(event.target.value)}
              placeholder="Ism, telefon yoki ID bo'yicha qidirish"
            />
          </label>

          <div className="filter-group">
            <Filter size={18} />
            <select value={roleFilter} onChange={(event) => handleRoleFilter(event.target.value)}>
              {roleOptions.map((option) => (
                <option value={option.value} key={option.value}>{option.label}</option>
              ))}
            </select>
            <select value={statusFilter} onChange={(event) => handleStatusFilter(event.target.value)}>
              {statusOptions.map((option) => (
                <option value={option.value} key={option.value}>{option.label}</option>
              ))}
            </select>
            <select value={pageSize} onChange={(event) => handlePageSize(event.target.value)}>
              <option value="10">10 tadan</option>
              <option value="20">20 tadan</option>
            </select>
          </div>
        </section>

        {loading ? (
          <div className="users-loading">{t('common.loading', 'Yuklanmoqda...')}</div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Ism familya</th>
                    <th>Telefon</th>
                    <th>Rol</th>
                    <th>Holati</th>
                    <th>Amallar</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedUsers.length === 0 ? (
                    <tr><td colSpan="6" className="empty">Foydalanuvchi topilmadi</td></tr>
                  ) : (
                    paginatedUsers.map((user) => (
                      <tr key={user.id} onClick={() => navigate(`/admin/users/${user.id}`)} className="clickable-row">
                        <td><span className="mono">#{user.id}</span></td>
                        <td>
                          <div className="user-cell">
                            <span className="user-avatar"><UserRound size={16} /></span>
                            <strong>{user.ism || '-'}</strong>
                          </div>
                        </td>
                        <td>{user.telefon || '-'}</td>
                        <td><span className={`role-pill ${user.rol || 'unknown'}`}>{user.rol || '-'}</span></td>
                        <td>
                          <span className={`status-pill ${user.verified ? 'active' : 'inactive'}`}>
                            <ShieldCheck size={14} />
                            {user.verified ? 'Faol' : 'Nofaol'}
                          </span>
                        </td>
                        <td>
                          <button className="edit-btn">
                            <Edit3 size={15} />
                            Ochish
                          </button>
                          <button
                            className={`status-action ${user.verified ? 'deactivate' : 'activate'}`}
                            onClick={(event) => toggleUserStatus(event, user)}
                            disabled={user.rol === 'admin'}
                          >
                            {user.verified ? 'Nofaol qilish' : 'Faol qilish'}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <footer className="users-footer">
              <p>
                {filteredUsers.length === 0
                  ? '0 ta natija'
                  : `${startIndex + 1}-${Math.min(startIndex + pageSize, filteredUsers.length)} / ${filteredUsers.length}`}
              </p>

              {pageCount > 1 && (
                <nav className="pagination" aria-label="Foydalanuvchilar sahifalari">
                  <button
                    className="prev"
                    onClick={() => setPage((value) => Math.max(value - 1, 1))}
                    disabled={currentPage === 1}
                    aria-label="Previous page"
                  >
                    <ChevronLeft size={24} />
                  </button>
                  {pageItems.map((item) => (
                    String(item).startsWith('dots') ? (
                      <span className="pagination-dots" key={item}>...</span>
                    ) : (
                      <button
                        key={item}
                        className={item === currentPage ? 'active' : ''}
                        onClick={() => setPage(item)}
                        aria-current={item === currentPage ? 'page' : undefined}
                      >
                        {item}
                      </button>
                    )
                  ))}
                  <button
                    className="next"
                    onClick={() => setPage((value) => Math.min(value + 1, pageCount))}
                    disabled={currentPage === pageCount}
                    aria-label="Next page"
                  >
                    <ChevronRight size={24} />
                  </button>
                </nav>
              )}
            </footer>
          </>
        )}
      </div>
    </main>
  )
}
