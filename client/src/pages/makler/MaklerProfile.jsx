import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, BadgeCheck, BriefcaseBusiness, Camera, LogOut, Phone, Save, UserRound } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { userService } from '../../services/userService'
import { uploadService } from '../../services/uploadService'
import './MaklerProfile.scss'
import { getErrorMessage } from '../../utils/auth'

export function MaklerProfile() {
  const navigate = useNavigate()
  const accessToken = useAuthStore((s) => s.accessToken)
  const clearAuth = useAuthStore((s) => s.clear)
  const basePath = '/makler'
  const roleLabel = 'Makler'
  const [broker, setBroker] = useState(null)
  const [form, setForm] = useState({ ism: '', rasm_url: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBroker = async () => {
      try {
        const data = await userService.getCurrentUser()
        setBroker(data)
        setForm({
          ism: data.ism || '',
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

    void fetchBroker()
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
        const updated = await userService.updateProfile({ ism: updatedForm.ism, rasm_url: updatedForm.rasm_url })
        setBroker(updated)
        setForm({
          ism: updated.ism || '',
          rasm_url: updated.rasm_url || '',
        })
        window.dispatchEvent(new CustomEvent('user-updated', { detail: updated }))
      } catch (saveErr) {
        setError(getErrorMessage(saveErr, 'Rasm saqlashda xatolik yuz berdi'))
      } finally {
        setSaving(false)
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Rasm yuklashda xatolik yuz berdi'))
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
      const updated = await userService.updateProfile({ ism: form.ism, rasm_url: form.rasm_url })
      setBroker(updated)
      setForm({
        ism: updated.ism || '',
        rasm_url: updated.rasm_url || '',
      })
      window.dispatchEvent(new CustomEvent('user-updated', { detail: updated }))
    } catch (err) {
      setError(getErrorMessage(err, 'Profilni saqlashda xatolik yuz berdi'))
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
      <main className="broker-profile-page">
        <div className="broker-profile-page__shell">
          <div className="broker-profile-page__state">Broker profil yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  return (
    <main className="broker-profile-page">
      <div className="broker-profile-page__shell">
        <section className="broker-profile-page__hero">
          <button className="broker-profile-page__back" type="button" onClick={() => navigate(basePath)}>
            <ArrowLeft size={18} />
            Dashboard
          </button>
          <div className="broker-profile-page__avatar">
            {form.rasm_url ? <img src={form.rasm_url} alt="" /> : <UserRound size={38} />}
            <label>
              <Camera size={15} />
              <input type="file" accept="image/*" onChange={handleImageUpload} disabled={uploading} />
            </label>
          </div>
          <div>
            <p className="broker-profile-page__eyebrow">{roleLabel} profile</p>
            <h1>{broker?.ism || roleLabel}</h1>
            <div className="broker-profile-page__badges">
              <span><BadgeCheck size={15} /> {broker?.verified ? 'Tasdiqlangan' : 'Tasdiqlanmagan'}</span>
              <span><BriefcaseBusiness size={15} /> {roleLabel}</span>
            </div>
          </div>
        </section>

        {error && <div className="broker-profile-page__error">{error}</div>}

        <form className="broker-profile-page__grid" onSubmit={handleSubmit}>
          <section className="broker-profile-panel">
            <h2>Shaxsiy ma'lumotlar</h2>
            <div className="broker-profile-field">
              <label htmlFor="broker-name">Ism familya</label>
              <input id="broker-name" name="ism" value={form.ism} onChange={handleChange} />
            </div>
            <div className="broker-profile-field">
              <label htmlFor="broker-phone">Telefon</label>
              <div className="broker-profile-field__with-icon">
                <Phone size={18} />
                <input id="broker-phone" name="telefon" value={broker?.telefon || ''} readOnly />
              </div>
            </div>
            <button className="broker-profile-page__primary" type="submit" disabled={saving || uploading}>
              <Save size={18} />
              {saving ? 'Saqlanmoqda...' : 'Profilni saqlash'}
            </button>
          </section>

          <aside className="broker-profile-panel broker-profile-panel--side">
            <h2>Hisob</h2>
            <div className="broker-profile-info">
              <span>Broker ID</span>
              <strong>#{broker?.id}</strong>
            </div>
            <div className="broker-profile-info">
              <span>Rasm</span>
              <strong>{uploading ? 'Yuklanmoqda...' : form.rasm_url ? 'Bor' : 'Yo‘q'}</strong>
            </div>
            <button className="broker-profile-page__danger" type="button" onClick={handleLogout}>
              <LogOut size={18} />
              Tizimdan chiqish
            </button>
          </aside>
        </form>
      </div>
    </main>
  )
}
