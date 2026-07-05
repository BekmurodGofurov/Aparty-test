import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, ChevronRight } from 'lucide-react'
import './AdminBreadcrumb.scss'

export function AdminBreadcrumb({ current }) {
  const navigate = useNavigate()

  return (
    <div className="admin-breadcrumb">
      <button className="admin-breadcrumb__back" onClick={() => navigate('/admin')}>
        <ArrowLeft size={17} />
        Orqaga qaytish
      </button>

      <nav className="admin-breadcrumb__path" aria-label="Admin navigatsiyasi">
        <Link to="/admin">Boshqaruv paneli</Link>
        <ChevronRight size={15} />
        <span>{current}</span>
      </nav>
    </div>
  )
}
