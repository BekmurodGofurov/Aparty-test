import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AdminBreadcrumb } from './AdminBreadcrumb'
import './AdminComplaints.scss'

export function AdminComplaints() {
  const { t } = useTranslation()
  const [complaints, setComplaints] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchComplaints = async () => {
      setComplaints([])
      setLoading(false)
    }

    void fetchComplaints()
  }, [])

  return (
    <main className="admin-complaints">
      <div className="page-container">
        <AdminBreadcrumb current="Shikoyatlar" />
        <h1>Shikoyatlarni boshqarish</h1>
        {loading ? (
          <p>{t('common.loading', 'Yuklanmoqda...')}</p>
        ) : (
          <div className="table-responsive">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Kimdan</th>
                  <th>Mavzu</th>
                  <th>Sana</th>
                  <th>Holati</th>
                  <th>Amallar</th>
                </tr>
              </thead>
              <tbody>
                {complaints.length === 0 ? (
                  <tr><td colSpan="6" className="empty">Shikoyatlar yo'q</td></tr>
                ) : (
                  complaints.map((complaint) => (
                    <tr key={complaint.id}>
                      <td>{complaint.id}</td>
                      <td>{complaint.from}</td>
                      <td>{complaint.about}</td>
                      <td>{complaint.date}</td>
                      <td>{complaint.status}</td>
                      <td><button>Hal qilish</button></td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  )
}
