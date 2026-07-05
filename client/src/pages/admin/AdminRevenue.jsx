import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminRevenue.scss'

export function AdminRevenue() {
  const { t } = useTranslation()
  const [revenue, setRevenue] = useState({
    total: 0,
    lastMonth: 0,
    transactions: [],
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchRevenue = async () => {
      setRevenue({
        total: 0,
        lastMonth: 0,
        transactions: [],
      })
      setLoading(false)
    }

    void fetchRevenue()
  }, [])

  return (
    <main className="admin-revenue">
      <div className="page-container">
        <AdminBreadcrumb current="Tushum" />
        <h1>Tushum hisoboti</h1>
        {loading ? (
          <p>{t('common.loading', 'Yuklanmoqda...')}</p>
        ) : (
          <>
            <div className="revenue-stats">
              <div className="revenue-card">
                <h3>Jami tushum</h3>
                <p className="revenue-amount">${revenue.total}</p>
              </div>
              <div className="revenue-card">
                <h3>Oxirgi oy</h3>
                <p className="revenue-amount">${revenue.lastMonth}</p>
              </div>
            </div>
            <div className="transactions">
              <h2>So'nggi tranzaksiyalar</h2>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Sana</th>
                    <th>Foydalanuvchi</th>
                    <th>Miqdor</th>
                    <th>Turi</th>
                  </tr>
                </thead>
                <tbody>
                  {revenue.transactions.length === 0 ? (
                    <tr><td colSpan="4" className="empty">Tranzaksiyalar yo'q</td></tr>
                  ) : (
                    revenue.transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>{tx.date}</td>
                        <td>{tx.user}</td>
                        <td>${tx.amount}</td>
                        <td>{tx.type}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </main>
  )
}
