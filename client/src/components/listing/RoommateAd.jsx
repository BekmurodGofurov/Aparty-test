import './RoommateAd.scss'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createRoommateListing } from '../../services/listingService'
import { getErrorMessage } from '../../utils/auth'

const GENDER_LABELS = { male: 'Erkak', female: 'Ayol', mixed: 'Farqi yo\'q' }
const MS_PER_DAY = 24 * 60 * 60 * 1000

const EMPTY_FORM = {
  residentsMale: 0,
  residentsFemale: 0,
  residentsChildren: 0,
  availableSpaces: 1,
  targetGender: 'mixed',
  anytime: true,
  availableFrom: '',
  price: '',
  description: '',
}

const formatDate = (value) =>
  new Intl.DateTimeFormat('uz-UZ', { day: '2-digit', month: 'long', year: 'numeric' }).format(new Date(value))

// Shows who lives in the apartment now and who the tenants are looking for.
export function RoommateAdInfo({ listing }) {
  const daysLeft = listing.expires_at
    ? Math.max(0, Math.ceil((new Date(listing.expires_at) - new Date()) / MS_PER_DAY))
    : null

  return (
    <section className="roommate-ad panel-card">
      <h2>Sherik qidirilmoqda</h2>
      <ul>
        <li>
          Kvartirada hozir: <strong>{listing.residents_male ?? 0}</strong> erkak, <strong>{listing.residents_female ?? 0}</strong> ayol,{' '}
          <strong>{listing.residents_children ?? 0}</strong> bola
        </li>
        <li>Qidirilayotgan: <strong>{GENDER_LABELS[listing.target_gender] || GENDER_LABELS.mixed}</strong></li>
        <li>Bo'sh joylar: <strong>{listing.available_spaces}</strong></li>
        <li>
          Kirish mumkin: <strong>{listing.available_from ? formatDate(listing.available_from) : 'istalgan vaqt (kutishyapti)'}</strong>
        </li>
        {daysLeft !== null && <li>E'lon yana <strong>{daysLeft}</strong> kun amal qiladi</li>}
      </ul>
      <p className="roommate-ad__hint">
        Ijarachilar bilan to'g'ridan-to'g'ri gaplashing: pastdagi "Bog'lanish" tugmasi ularga qo'ng'iroq qiladi. Uy egasi bilan emas.
      </p>
      {listing.parent_listing_id && <Link to={`/listing/${listing.parent_listing_id}`}>Kvartirani ko'rish</Link>}
    </section>
  )
}

// A tenant of this apartment posts a roommate ad. No permission is needed.
export function RoommateAdForm({ apartmentId }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const setField = (name, value) => setForm((prev) => ({ ...prev, [name]: value }))
  const setNumber = (name) => (event) => setField(name, Math.max(0, Number(event.target.value) || 0))

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      const ad = await createRoommateListing({
        apartmentId,
        residentsMale: form.residentsMale,
        residentsFemale: form.residentsFemale,
        residentsChildren: form.residentsChildren,
        availableSpaces: Math.max(1, form.availableSpaces),
        targetGender: form.targetGender,
        availableFrom: form.anytime ? null : form.availableFrom,
        price: Number(form.price),
        description: form.description,
      })
      navigate(`/listing/${ad.id}`)
    } catch (requestError) {
      setError(getErrorMessage(requestError, "E'lonni joylab bo'lmadi."))
    } finally {
      setSaving(false)
    }
  }

  if (!open) {
    return (
      <section className="roommate-ad panel-card">
        <h2>Shu kvartirada yashaysizmi?</h2>
        <p className="roommate-ad__hint">Sherik kerak bo'lsa, e'lon bering. E'lon 30 kun amal qiladi, hozircha bepul.</p>
        <button type="button" className="roommate-ad__button" onClick={() => setOpen(true)}>Sherik qidirish</button>
      </section>
    )
  }

  return (
    <form className="roommate-ad panel-card" onSubmit={submit}>
      <h2>Sherik qidirish</h2>
      <p className="roommate-ad__hint">Manzil va rasmlar shu kvartiradan olinadi. Hech kimdan ruxsat so'ralmaydi, kvartira egasiga xabar boradi.</p>

      <fieldset>
        <legend>Hozir kvartirada kimlar yashaydi</legend>
        <label>Erkak <input type="number" min="0" value={form.residentsMale} onChange={setNumber('residentsMale')} /></label>
        <label>Ayol <input type="number" min="0" value={form.residentsFemale} onChange={setNumber('residentsFemale')} /></label>
        <label>Bola <input type="number" min="0" value={form.residentsChildren} onChange={setNumber('residentsChildren')} /></label>
      </fieldset>

      <label>
        Nechta odam kelishi mumkin
        <input type="number" min="1" max="10" value={form.availableSpaces} onChange={setNumber('availableSpaces')} />
      </label>

      <label>
        Kimni qidiryapsiz
        <select value={form.targetGender} onChange={(e) => setField('targetGender', e.target.value)}>
          <option value="mixed">Farqi yo'q</option>
          <option value="male">Erkak</option>
          <option value="female">Ayol</option>
        </select>
      </label>

      <label className="roommate-ad__check">
        <input type="checkbox" checked={form.anytime} onChange={(e) => setField('anytime', e.target.checked)} />
        Istalgan vaqt kelishi mumkin (kutishyapti)
      </label>
      {!form.anytime && (
        <label>
          Qaysi kundan kelishi mumkin
          <input type="date" required value={form.availableFrom} onChange={(e) => setField('availableFrom', e.target.value)} />
        </label>
      )}

      <label>
        Bir kishi uchun narx
        <input type="number" min="1" required value={form.price} onChange={(e) => setField('price', e.target.value)} />
      </label>

      <label>
        Qisqacha ma'lumot
        <textarea rows={3} value={form.description} onChange={(e) => setField('description', e.target.value)} />
      </label>

      {error && <p className="roommate-ad__error">{error}</p>}
      <div className="roommate-ad__actions">
        <button type="submit" className="roommate-ad__button" disabled={saving}>{saving ? 'Joylanmoqda...' : "E'lon joylash"}</button>
        <button type="button" onClick={() => setOpen(false)}>Yopish</button>
      </div>
    </form>
  )
}
