import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, BadgeCheck, Camera, Home, LogOut, Phone, Save, UserRound } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { userService } from '../../services/userService'
import { uploadService } from '../../services/uploadService'
import './OwnerProfile.scss'

export function OwnerProfile() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const clearAuth = useAuthStore((s) => s.clear)
  const [owner, setOwner] = useState(null)
  const [form, setForm] = useState({ ism: '', telefon: '', rasm_url: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchOwner = async () => {
      try {
        const data = await userService.getCurrentUser()
        setOwner(data)
        setForm({
          ism: data.ism || '',
          telefon: data.telefon || '',
          rasm_url: data.rasm_url || '',
        })
      } catch {
        setError('Profilni yuklab bo‘lmadi')
      } finally {
        setLoading(false)
      }
    }

    if (!accessToken) {
      navigate('/login')
      return
    }

    void fetchOwner()
  }, [accessToken, navigate])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    setError('')
    try {
      const { url } = await uploadService.uploadImage(file)
      // Update form with new image URL
      const updatedForm = { ...form, rasm_url: url }
      setForm(updatedForm)

      // Auto-save the profile picture to database
      setSaving(true)
      try {
        const updated = await userService.updateProfile(updatedForm)
        setOwner(updated)
        setForm({
          ism: updated.ism || '',
          telefon: updated.telefon || '',
          rasm_url: updated.rasm_url || '',
        })
        window.dispatchEvent(new CustomEvent('user-updated', { detail: updated }))
      } catch (saveErr) {
        setError(saveErr.response?.data?.detail || 'Rasm saqlashda xatolik yuz berdi')
      } finally {
        setSaving(false)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Rasm yuklashda xatolik yuz berdi')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      const updated = await userService.updateProfile(form)
      setOwner(updated)
      setForm({
        ism: updated.ism || '',
        telefon: updated.telefon || '',
        rasm_url: updated.rasm_url || '',
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Profilni saqlashda xatolik yuz berdi')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = () => {
    clearAuth()
    navigate('/')
  }

  if (loading) {
    return (
      <main className="owner-profile-page">
        <div className="owner-profile-page__shell">
          <div className="owner-profile-page__state">Uy egasi profili yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="owner-profile-page">
      <div className="owner-profile-page__shell">
        <section className="owner-profile-page__hero">
          <button className="owner-profile-page__back" type="button" onClick={() => navigate('/owner')}>
            <ArrowLeft size={18} />
            Boshqaruv paneli
          </button>
          <div className="owner-profile-page__avatar">
            {form.rasm_url ? <img src={form.rasm_url} alt="" /> : <UserRound size={38} />}
            <label>
              <Camera size={15} />
              <input type="file" accept="image/*" onChange={handleImageUpload} disabled={uploading} />
            </label>
          </div>
          <div>
            <p className="owner-profile-page__eyebrow">Uy egasi profili</p>
            <h1>{owner?.ism || 'Uy egasi'}</h1>
            <div className="owner-profile-page__badges">
              <span><BadgeCheck size={15} /> {owner?.verified ? 'Tasdiqlangan' : 'Tasdiqlanmagan'}</span>
              <span><Home size={15} /> Uy egasi</span>
            </div>
          </div>
        </section>

        {error && <div className="owner-profile-page__error">{error}</div>}

        <form className="owner-profile-page__grid" onSubmit={handleSubmit}>
          <section className="owner-profile-panel">
            <h2>Shaxsiy ma'lumotlar</h2>
            <div className="owner-profile-field">
              <label htmlFor="owner-name">Ism familya</label>
              <input id="owner-name" name="ism" value={form.ism} onChange={handleChange} />
            </div>
            <div className="owner-profile-field">
              <label htmlFor="owner-phone">Telefon</label>
              <div className="owner-profile-field__with-icon">
                <Phone size={18} />
                <input id="owner-phone" name="telefon" value={form.telefon} onChange={handleChange} />
              </div>
            </div>
            <button className="owner-profile-page__primary" type="submit" disabled={saving || uploading}>
              <Save size={18} />
              {saving ? 'Saqlanmoqda...' : 'Profilni saqlash'}
            </button>
          </section>

          <aside className="owner-profile-panel owner-profile-panel--side">
            <h2>Hisob</h2>
            <div className="owner-profile-info">
              <span>Uy egasi ID</span>
              <strong>#{owner?.id}</strong>
            </div>
            <div className="owner-profile-info">
              <span>Rasm</span>
              <strong>{uploading ? 'Yuklanmoqda...' : form.rasm_url ? 'Bor' : 'Yo‘q'}</strong>
            </div>
            <button className="owner-profile-page__danger" type="button" onClick={handleLogout}>
              <LogOut size={18} />
              Tizimdan chiqish
            </button>
          </aside>
        </form>
      </div>
    </main>
  )
}
