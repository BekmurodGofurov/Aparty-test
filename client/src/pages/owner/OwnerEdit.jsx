import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  ArrowLeft,
  Bath,
  BedDouble,
  Building2,
  Check,
  ChevronDown,
  CircleDollarSign,
  Fan,
  Layers,
  Home,
  ImagePlus,
  LampDesk,
  MapPin,
  Refrigerator,
  Save,
  Sparkles,
  Trash2,
  Tv,
  WashingMachine,
  Wifi,
} from 'lucide-react'
import { getListingById, updateListing } from '../../services/listingService.js'
import { uploadService } from '../../services/uploadService'
import { useAuthStore } from '../../store/authStore'
import { REGIONS_DATA } from '../../data/regions'
import './OwnerCreate.scss'
import './OwnerEdit.scss'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { DEFAULT_LISTING_LOCATION } from '../../utils/geo'
import { getErrorMessage } from '../../utils/auth'
import { FallbackImage } from '../../components/ui/FallbackImage'

const defaultMarkerIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

L.Marker.prototype.options.icon = defaultMarkerIcon

const amenitiesList = [
  { key: 'wifi', label: 'Wi-Fi', icon: Wifi },
  { key: 'gas', label: 'Gaz', icon: Fan },
  { key: 'water', label: 'Suv', icon: Bath },
  { key: 'tv', label: 'TV', icon: Tv },
  { key: 'air_conditioner', label: 'Konditsioner', icon: Fan },
  { key: 'washing_machine', label: 'Kir mashinasi', icon: WashingMachine },
  { key: 'fridge', label: 'Sovutkich', icon: Refrigerator },
  { key: 'kitchen', label: 'Oshxona jihozlari', icon: LampDesk },
]

const propertyTypes = [
  { value: 'full_unit', label: "To'liq kvartira", help: 'Butun uy bitta ijarachiga beriladi' },
  { value: 'shared_room', label: 'Kishi boshiga', help: "Joylar alohida ijaraga beriladi" },
]

const genderOptions = [
  { value: 'mixed', label: "Farqi yo'q" },
  { value: 'male', label: 'Erkaklar' },
  { value: 'female', label: 'Ayollar' },
]

const regionCenters = {
  Tashkent: [41.3111, 69.2797],
  Andijon: [40.7821, 72.3442],
  Bukhara: [39.7747, 64.4286],
  Fergana: [40.3734, 71.7978],
  Jizzakh: [40.1158, 67.8422],
  Kashkadarya: [38.861, 65.7847],
  Khorezm: [41.3565, 60.8567],
  Navoiy: [40.1039, 65.3688],
  Navoi: [40.1039, 65.3688],
  Samarkand: [39.6542, 66.9597],
  Sirdarya: [40.4897, 68.7842],
  Surkhandarya: [37.2242, 67.2783],
  'Tashkent Region': [41.1102, 69.0476],
  Namangan: [41.0011, 71.6726],
}

function LocationClickHandler({ onPick }) {
  useMapEvents({
    click(event) {
      onPick(event.latlng.lat, event.latlng.lng)
    },
  })
  return null
}

/**
 * Normalize a raw backend listing response into the English frontend form shape.
 * Backend already uses English keys — this is a direct mapping, no translation.
 */
const normalizeListing = (listing = {}) => ({
  title: listing.title || listing.address || '',
  description: listing.description || '',
  region: listing.region || '',
  district: listing.district || '',
  address: listing.address || '',
  rental_type: listing.rental_type || ((listing.max_guests || 1) > 1 ? 'shared_room' : 'full_unit'),
  rooms_count: listing.rooms_count || 1,
  floor: listing.floor ?? 1,
  total_floors: listing.total_floors ?? 1,
  max_guests: listing.max_guests || 1,
  available_spaces: listing.available_spaces || 1,
  price: listing.price || 1,
  latitude: listing.latitude || DEFAULT_LISTING_LOCATION.lat,
  longitude: listing.longitude || DEFAULT_LISTING_LOCATION.lng,
  images: listing.images || [],
  target_gender: listing.target_gender || 'mixed',
  amenities: listing.amenities || {},
  is_active: Boolean(listing.is_active),
  is_premium: Boolean(listing.is_premium),
})

export function OwnerEdit() {
  const { id } = useParams()
  const navigate = useNavigate()
  const role = useAuthStore((state) => state.role)
  const basePath = role === 'makler' ? '/makler' : '/owner'
  const panelLabel = role === 'makler' ? 'Makler paneli' : 'Uy egasi paneli'
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingImages, setUploadingImages] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState(null)

  useEffect(() => {
    const fetchListing = async () => {
      try {
        setLoading(true)
        const data = await getListingById(id)
        setForm(normalizeListing(data))
      } catch {
        setError("E'lonni yuklab bo'lmadi")
      } finally {
        setLoading(false)
      }
    }

    void fetchListing()
  }, [id])

  const districts = useMemo(() => REGIONS_DATA[form?.region] || [], [form?.region])
  const mapCenter = useMemo(
    () => [form?.latitude || DEFAULT_LISTING_LOCATION.lat, form?.longitude || DEFAULT_LISTING_LOCATION.lng],
    [form?.latitude, form?.longitude]
  )

  const handleChange = (e) => {
    const { name, value } = e.target
    const numericFields = ['rooms_count', 'floor', 'total_floors', 'max_guests', 'available_spaces', 'price']
    setForm((prev) => ({
      ...prev,
      [name]: numericFields.includes(name) ? Number(value) : value,
    }))
  }

  const setField = (name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleRentalTypeChange = (type) => {
    setForm((prev) => ({
      ...prev,
      rental_type: type,
      max_guests: type === 'full_unit' ? 1 : Math.max(prev.max_guests, 2),
      available_spaces: type === 'full_unit' ? 1 : Math.max(prev.available_spaces, 1),
    }))
  }

  const handleRegionChange = (region) => {
    if (!region) {
      setForm((prev) => ({ ...prev, region: '', district: '' }))
      return
    }

    const [latitude, longitude] = regionCenters[region] || regionCenters.Andijon
    setForm((prev) => ({ ...prev, region, district: '', latitude, longitude }))
  }

  const handleLocationPick = (latitude, longitude) => {
    setForm((prev) => ({
      ...prev,
      latitude: Number(latitude.toFixed(6)),
      longitude: Number(longitude.toFixed(6)),
    }))
  }

  const handleAmenity = (name) => {
    setForm((prev) => ({
      ...prev,
      amenities: { ...prev.amenities, [name]: !prev.amenities?.[name] },
    }))
  }

  const handleImagesUpload = async (event) => {
    const files = Array.from(event.target.files || [])
    if (!files.length) return

    const remainingSlots = Math.max(0, 5 - form.images.length)
    const uploadFiles = files.slice(0, remainingSlots)
    if (!uploadFiles.length) {
      setError('Maksimum 5 ta rasm yuklash mumkin')
      event.target.value = ''
      return
    }

    setError('')
    setUploadingImages(true)
    try {
      const uploaded = await Promise.all(uploadFiles.map((file) => uploadService.uploadImage(file)))
      setForm((prev) => ({
        ...prev,
        images: [...prev.images, ...uploaded.map((item) => item.url)].slice(0, 5),
      }))
    } catch (err) {
      setError(getErrorMessage(err, 'Rasm yuklashda xatolik yuz berdi'))
    } finally {
      setUploadingImages(false)
      event.target.value = ''
    }
  }

  const removeImage = (url) => {
    setForm((prev) => ({
      ...prev,
      images: prev.images.filter((imageUrl) => imageUrl !== url),
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const payload = {
        region: form.region,
        district: form.district,
        address: form.address || null,
        rental_type: form.rental_type,
        rooms_count: form.rooms_count,
        floor: form.floor,
        total_floors: form.total_floors,
        max_guests: form.rental_type === 'full_unit' ? 1 : form.max_guests,
        available_spaces: form.rental_type === 'full_unit' ? 1 : form.available_spaces,
        price: form.price,
        latitude: form.latitude,
        longitude: form.longitude,
        images: form.images,
        target_gender: form.target_gender,
        amenities: form.amenities,
        description: form.description || null,
      }
      await updateListing(id, payload)
      navigate(basePath)
    } catch (err) {
      setError(getErrorMessage(err, "E'lonni saqlashda xatolik yuz berdi"))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <main className="owner-create owner-edit">
        <div className="owner-create__shell">
          <div className="owner-edit__state">E'lon yuklanmoqda...</div>
        </div>
      </main>
    )
  }

  if (!form) {
    return (
      <main className="owner-create owner-edit">
        <div className="owner-create__shell">
          <div className="owner-create__error">{error}</div>
        </div>
      </main>
    )
  }

  return (
    <main className="owner-create owner-edit">
      <div className="owner-create__shell">
        <section className="owner-create__hero">
          <button className="owner-create__back" type="button" onClick={() => navigate(basePath)}>
            <ArrowLeft size={18} />
            Boshqaruv paneli
          </button>
          <div>
            <p className="owner-create__eyebrow">{panelLabel}</p>
            <h1>E'lonni tahrirlash</h1>
            <div className="owner-create__status">
              {form.is_active ? 'Faol' : 'Nofaol'} {form.is_premium ? 'Premium' : 'Oddiy'}
            </div>
          </div>
        </section>

        {error && <div className="owner-create__error">{error}</div>}

        <div className="owner-create__layout">
          <form onSubmit={handleSubmit} className="owner-create__form">
            <section className="owner-form-card">
              <div className="owner-form-card__header">
                <span className="owner-form-card__icon"><Building2 size={20} /></span>
                <div>
                  <p className="owner-create__eyebrow">Asosiy</p>
                  <h2>Uy haqida</h2>
                </div>
              </div>

              <div className="owner-image-uploader">
                <div className="owner-image-uploader__header">
                  <div>
                    <h3>Uy rasmlari</h3>
                    <p>Kamida 2 ta, maksimum 5 ta rasm saqlang.</p>
                  </div>
                  <strong>{form.images.length}/5</strong>
                </div>

                <div className="owner-image-grid">
                  {form.images.map((url) => (
                    <div className="owner-image-tile" key={url}>
                      <FallbackImage src={url} alt="" />
                      <button type="button" onClick={() => removeImage(url)} aria-label="Rasmni o'chirish">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  ))}

                  {form.images.length < 5 && (
                    <label className="owner-image-add">
                      <ImagePlus size={24} />
                      <span>{uploadingImages ? 'Yuklanmoqda...' : "Rasm qo'shish"}</span>
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        disabled={uploadingImages}
                        onChange={handleImagesUpload}
                      />
                    </label>
                  )}
                </div>
              </div>

              <div className="owner-field">
                <label htmlFor="description">Tavsif</label>
                <textarea
                  id="description"
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="Kvartira holati, yaqin joylar va shartlarni yozing"
                  rows={5}
                />
              </div>

              <div className="owner-choice-group">
                {propertyTypes.map((type) => (
                  <button
                    type="button"
                    key={type.value}
                    className={`owner-choice-card ${form.rental_type === type.value ? 'is-selected' : ''}`}
                    onClick={() => handleRentalTypeChange(type.value)}
                  >
                    <Home size={19} />
                    <span>{type.label}</span>
                    <small>{type.help}</small>
                  </button>
                ))}
              </div>

              <div className="owner-form-grid owner-form-grid--two">
                <div className="owner-field">
                  <label htmlFor="rooms_count">Xonalar soni</label>
                  <div className="owner-field__with-icon">
                    <BedDouble size={18} />
                    <input
                      id="rooms_count"
                      type="number"
                      name="rooms_count"
                      min="1"
                      value={form.rooms_count}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="owner-field owner-field--select">
                  <label htmlFor="target_gender">Kimlar uchun</label>
                  <select id="target_gender" name="target_gender" value={form.target_gender} onChange={handleChange}>
                    {genderOptions.map((option) => (
                      <option value={option.value} key={option.value}>{option.label}</option>
                    ))}
                  </select>
                  <ChevronDown size={18} />
                </div>
              </div>

              <div className="owner-form-grid owner-form-grid--two">
                <div className="owner-field">
                  <label htmlFor="floor">Qavat</label>
                  <div className="owner-field__with-icon">
                    <Layers size={18} />
                    <input
                      id="floor"
                      type="number"
                      name="floor"
                      min="0"
                      value={form.floor}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="owner-field">
                  <label htmlFor="total_floors">Jami qavat</label>
                  <input
                    id="total_floors"
                    type="number"
                    name="total_floors"
                    min="1"
                    value={form.total_floors}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </section>

            <section className="owner-form-card">
              <div className="owner-form-card__header">
                <span className="owner-form-card__icon"><MapPin size={20} /></span>
                <div>
                  <p className="owner-create__eyebrow">Manzil</p>
                  <h2>Joylashuv</h2>
                </div>
              </div>

              <div className="owner-form-grid owner-form-grid--two">
                <div className="owner-field owner-field--select">
                  <label htmlFor="region">Viloyat</label>
                  <select id="region" name="region" value={form.region} onChange={(event) => handleRegionChange(event.target.value)}>
                    <option value="">Viloyatni tanlang</option>
                    {Object.keys(REGIONS_DATA).map((region) => (
                      <option value={region} key={region}>{region}</option>
                    ))}
                  </select>
                  <ChevronDown size={18} />
                </div>

                <div className="owner-field owner-field--select">
                  <label htmlFor="district">Tuman</label>
                  <select
                    id="district"
                    name="district"
                    value={form.district}
                    onChange={(event) => setField('district', event.target.value)}
                    disabled={!form.region}
                  >
                    <option value="">{form.region ? 'Tumanni tanlang' : 'Avval viloyat tanlang'}</option>
                    {districts.map((district) => (
                      <option value={district} key={district}>{district}</option>
                    ))}
                  </select>
                  <ChevronDown size={18} />
                </div>
              </div>

              <div className="owner-field">
                <label htmlFor="address">To'liq manzil</label>
                <div className="owner-field__with-icon">
                  <MapPin size={18} />
                  <input
                    id="address"
                    type="text"
                    name="address"
                    value={form.address}
                    onChange={handleChange}
                    placeholder="Ko'cha, uy raqami, orientir"
                  />
                </div>
              </div>

              <div className="owner-map-picker">
                <div className="owner-map-picker__header">
                  <div>
                    <h3>Xaritadagi joy</h3>
                    <p>{form.district ? `${form.district}, ${form.region}` : 'Viloyat va tuman tanlang'}</p>
                  </div>
                  <span>{form.latitude.toFixed(5)}, {form.longitude.toFixed(5)}</span>
                </div>
                <MapContainer
                  key={`${form.region}-${form.district}-${id}`}
                  center={mapCenter}
                  zoom={13}
                  scrollWheelZoom={false}
                  className="owner-map-picker__map"
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <LocationClickHandler onPick={handleLocationPick} />
                  <Marker position={mapCenter} />
                </MapContainer>
              </div>
            </section>

            <section className="owner-form-card">
              <div className="owner-form-card__header">
                <span className="owner-form-card__icon"><CircleDollarSign size={20} /></span>
                <div>
                  <p className="owner-create__eyebrow">Narx</p>
                  <h2>Ijara narxi</h2>
                </div>
              </div>
              <div className="owner-field">
                <label htmlFor="price">{form.rental_type === 'full_unit' ? 'Oylik narx' : 'Kishi boshiga narx'}</label>
                <div className="owner-field__with-icon">
                  <CircleDollarSign size={18} />
                  <input
                    id="price"
                    type="number"
                    name="price"
                    min="1"
                    value={form.price}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="owner-form-grid owner-form-grid--two">
                <div className="owner-field">
                  <label htmlFor="max_guests">Maksimal odam</label>
                  <input
                    id="max_guests"
                    type="number"
                    name="max_guests"
                    min="1"
                    value={form.max_guests}
                    disabled={form.rental_type === 'full_unit'}
                    onChange={handleChange}
                  />
                </div>
                <div className="owner-field">
                  <label htmlFor="available_spaces">Bo'sh joy</label>
                  <input
                    id="available_spaces"
                    type="number"
                    name="available_spaces"
                    min="1"
                    value={form.available_spaces}
                    disabled={form.rental_type === 'full_unit'}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </section>

            <section className="owner-form-card">
              <div className="owner-form-card__header">
                <span className="owner-form-card__icon"><Sparkles size={20} /></span>
                <div>
                  <p className="owner-create__eyebrow">Qulayliklar</p>
                  <h2>Uy ichidagi imkoniyatlar</h2>
                </div>
              </div>
              <div className="owner-amenities-grid">
                {amenitiesList.map(({ key, label, icon: Icon }) => (
                  <button
                    type="button"
                    key={key}
                    className={`owner-amenity-chip ${form.amenities?.[key] ? 'is-selected' : ''}`}
                    onClick={() => handleAmenity(key)}
                  >
                    <Icon size={18} />
                    <span>{label}</span>
                    {form.amenities?.[key] && <Check size={16} />}
                  </button>
                ))}
              </div>
            </section>

            <div className="owner-create__actions">
              <button type="button" className="owner-create__secondary" onClick={() => navigate(basePath)}>
                Bekor qilish
              </button>
              <button type="submit" className="owner-create__primary" disabled={saving}>
                <Save size={18} />
                {saving ? 'Saqlanmoqda...' : "O'zgarishlarni saqlash"}
              </button>
            </div>
          </form>

          <aside className="owner-create__summary">
            <div className="owner-summary-card">
              <div className="owner-summary-card__image">
                <FallbackImage src={form.images[0]} alt="" fallback={<Home size={34} />} />
              </div>
              <div className="owner-summary-card__body">
                <p className="owner-create__eyebrow">Ko'rinish</p>
                <h2>{form.address || 'Kvartira manzili'}</h2>
                <span>{[form.district, form.region].filter(Boolean).join(', ') || 'Manzil tanlanmagan'}</span>
              </div>
              <div className="owner-summary-card__stats">
                <div>
                  <span>Xona</span>
                  <strong>{form.rooms_count}</strong>
                </div>
                <div>
                  <span>Joy</span>
                  <strong>{form.rental_type === 'full_unit' ? "To'liq" : form.available_spaces}</strong>
                </div>
                <div>
                  <span>Narx</span>
                  <strong>${form.price}</strong>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </main>
  )
}
