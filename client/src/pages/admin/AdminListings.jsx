import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { BadgeDollarSign, Building2, ChevronLeft, ChevronRight, Eye, Filter, MapPin, Search, ShieldCheck } from 'lucide-react'
import { api } from '../../services/api'
import { getAdminListings } from '../../services/listingService'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminListings.scss'

const statusOptions = [
  { value: 'all', label: 'Barcha holatlar' },
  { value: 'active', label: 'Faol' },
  { value: 'inactive', label: 'Nofaol' },
]

const premiumOptions = [
  { value: 'all', label: 'Barcha turlar' },
  { value: 'premium', label: 'Premium' },
  { value: 'simple', label: 'Oddiy' },
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

function listingTitle(listing) {
  return listing.address || [listing.district, listing.region]
    .filter(Boolean)
    .join(', ') || 'Manzil kiritilmagan'
}

function listingLocation(listing) {
  return [listing.district, listing.region].filter(Boolean).join(', ') || '-'
}

export function AdminListings() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [listings, setListings] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [premiumFilter, setPremiumFilter] = useState('all')
  const [pageSize, setPageSize] = useState(10)
  const [page, setPage] = useState(1)

  useEffect(() => {
    const fetchListings = async () => {
      try {
        const data = await getAdminListings()
        setListings(data)
      } finally {
        setLoading(false)
      }
    }
    void fetchListings()
  }, [])

  const filteredListings = useMemo(() => {
    const query = searchTerm.trim().toLowerCase()

    return listings.filter((listing) => {
      const isActive = listing.is_active ?? false
      const isPremium = listing.is_premium ?? false
      const price = listing.price_usd

      const matchesQuery = !query || [
        listing.id,
        listingTitle(listing),
        listingLocation(listing),
        listing.owner_id,
        price,
      ].some((value) => String(value ?? '').toLowerCase().includes(query))

      const matchesStatus = statusFilter === 'all'
        || (statusFilter === 'active' && isActive)
        || (statusFilter === 'inactive' && !isActive)

      const matchesPremium = premiumFilter === 'all'
        || (premiumFilter === 'premium' && isPremium)
        || (premiumFilter === 'simple' && !isPremium)

      return matchesQuery && matchesStatus && matchesPremium
    })
  }, [listings, searchTerm, statusFilter, premiumFilter])

  const pageCount = Math.max(1, Math.ceil(filteredListings.length / pageSize))
  const currentPage = Math.min(page, pageCount)
  const startIndex = (currentPage - 1) * pageSize
  const paginatedListings = filteredListings.slice(startIndex, startIndex + pageSize)
  const pageItems = getPageItems(currentPage, pageCount)

  const handleSearch = (value) => {
    setSearchTerm(value)
    setPage(1)
  }

  const handleStatusFilter = (value) => {
    setStatusFilter(value)
    setPage(1)
  }

  const handlePremiumFilter = (value) => {
    setPremiumFilter(value)
    setPage(1)
  }

  const handlePageSize = (value) => {
    setPageSize(Number(value))
    setPage(1)
  }

  const toggleListingStatus = async (event, listing) => {
    event.stopPropagation()
    const current = listing.is_active ?? false
    const { data } = await api.patch(`/admin/listings/${listing.id}/status`, { is_active: !current })
    const updated = data.listing
    setListings((items) => items.map((item) => String(item.id) === String(updated.id) ? updated : item))
  }

  return (
    <main className="admin-listings">
      <div className="page-container">
        <AdminBreadcrumb current="E'lonlar" />
        <header className="admin-listings__header">
          <div>
            <p className="eyebrow">Admin panel</p>
            <h1><Building2 size={30} /> E'lonlarni moderatsiya qilish</h1>
          </div>
          <div className="listing-count">
            <strong>{filteredListings.length}</strong>
            <span>topildi</span>
          </div>
        </header>

        <section className="listing-tools" aria-label="E'lon filtrlari">
          <label className="search-box">
            <Search size={18} />
            <input
              value={searchTerm}
              onChange={(event) => handleSearch(event.target.value)}
              placeholder="Manzil, tuman, ID yoki egasi bo'yicha qidirish"
            />
          </label>

          <div className="filter-group">
            <Filter size={18} />
            <select value={statusFilter} onChange={(event) => handleStatusFilter(event.target.value)}>
              {statusOptions.map((option) => (
                <option value={option.value} key={option.value}>{option.label}</option>
              ))}
            </select>
            <select value={premiumFilter} onChange={(event) => handlePremiumFilter(event.target.value)}>
              {premiumOptions.map((option) => (
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
          <div className="listings-loading">{t('common.loading', 'Yuklanmoqda...')}</div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>E'lon</th>
                    <th>Egasi</th>
                    <th>Narx</th>
                    <th>Turi</th>
                    <th>Holati</th>
                    <th>Amallar</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedListings.length === 0 ? (
                    <tr><td colSpan="7" className="empty">E'lon topilmadi</td></tr>
                  ) : (
                    paginatedListings.map((listing) => {
                      const isActive = listing.is_active ?? false
                      const isPremium = listing.is_premium ?? false
                      const price = listing.price_usd ?? 0

                      return (
                        <tr key={listing.id} onClick={() => navigate(`/admin/listings/${listing.id}`)} className="clickable-row">
                          <td><span className="mono">#{String(listing.id).slice(0, 8)}</span></td>
                          <td>
                            <div className="listing-cell">
                              <span className="listing-icon"><MapPin size={16} /></span>
                              <div>
                                <strong>{listingTitle(listing)}</strong>
                                <span>{listingLocation(listing)}</span>
                              </div>
                            </div>
                          </td>
                          <td><span className="mono">{listing.owner_id}</span></td>
                          <td>
                            <span className="price-pill">
                              <BadgeDollarSign size={14} />
                              {Number(price).toLocaleString('uz-UZ')} USD
                            </span>
                          </td>
                          <td><span className={`type-pill ${isPremium ? 'premium' : 'simple'}`}>{isPremium ? 'Premium' : 'Oddiy'}</span></td>
                          <td>
                            <span className={`status-pill ${isActive ? 'active' : 'inactive'}`}>
                              <ShieldCheck size={14} />
                              {isActive ? 'Faol' : 'Nofaol'}
                            </span>
                          </td>
                          <td>
                            <button className="review-btn" onClick={(event) => { event.stopPropagation(); navigate(`/admin/listings/${listing.id}`) }}>
                              <Eye size={15} />
                              Ko'rish
                            </button>
                            <button
                              className={`status-action ${isActive ? 'deactivate' : 'activate'}`}
                              onClick={(event) => toggleListingStatus(event, listing)}
                            >
                              {isActive ? 'Nofaol qilish' : 'Faol qilish'}
                            </button>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            <footer className="listings-footer">
              <p>
                {filteredListings.length === 0
                  ? '0 ta natija'
                  : `${startIndex + 1}-${Math.min(startIndex + pageSize, filteredListings.length)} / ${filteredListings.length}`}
              </p>

              {pageCount > 1 && (
                <nav className="pagination" aria-label="E'lonlar sahifalari">
                  <button
                    className="prev"
                    onClick={() => setPage((value) => Math.max(value - 1, 1))}
                    disabled={currentPage === 1}
                    aria-label="Oldingi sahifa"
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
                    aria-label="Keyingi sahifa"
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
