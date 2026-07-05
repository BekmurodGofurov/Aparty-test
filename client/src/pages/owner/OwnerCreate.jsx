import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
  DoorOpen,
  Fan,
  Layers,
  Home,
  ImagePlus,
  LampDesk,
  MapPin,
  Refrigerator,
  Save,
  ShieldCheck,
  Sparkles,
  Trash2,
  Tv,
  WashingMachine,
  Wifi,
} from 'lucide-react'
import { createListing } from '../../services/listingService'
import { uploadService } from '../../services/uploadService'
import { REGIONS_DATA } from '../../data/regions'
import './OwnerCreate.scss'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const defaultMarkerIcon = L.icon({
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

L.Marker.prototype.options.icon = defaultMarkerIcon

const amenities = [
  { key: 'wifi', label: 'Wi-Fi', icon: Wifi },
  { key: 'gaz', label: 'Gaz', icon: Fan },
  { key: 'suv', label: 'Suv', icon: Bath },
  { key: 'tv', label: 'TV', icon: Tv },
  { key: 'konditsioner', label: 'Konditsioner', icon: Fan },
  { key: 'kir_mashina', label: 'Kir mashinasi', icon: WashingMachine },
  { key: 'holodilnik', label: 'Sovutkich', icon: Refrigerator },
  { key: 'oshxona_jihozi', label: 'Oshxona jihozlari', icon: LampDesk },
]

const propertyTypes = [
  { value: 'full', label: "To'liq kvartira", help: 'Butun uy bitta ijarachiga beriladi' },
  { value: 'shared', label: 'Kishi boshiga', help: "Joylar alohida ijaraga beriladi" },
]

const genderOptions = [
  { value: 'mixed', label: 'Farqi yo‘q' },
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

export function OwnerCreate() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [uploadingImages, setUploadingImages] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    nomi: '',
    tavsifi: '',
    viloyat: '',
    tuman: '',
    manzil: '',
    ijara_turi: 'full',
    xonalar_soni: 1,
    qavat: 1,
    jami_qavat: 1,
    max_kishi: 1,
    bosh_joy: 1,
    narx_usd: 100,
    latitude: 41.311081,
    longitude: 69.240562,
    rasmlar: [],
    jins: 'mixed',
    qulayliklar: {
      wifi: false,
      gaz: false,
      suv: false,
      tv: false,
      konditsioner: false,
      kir_mashina: false,
      holodilnik: false,
      oshxona_jihozi: false,
    },
  })

  const selectedAmenities = useMemo(
    () => amenities.filter((item) => form.qulayliklar[item.key]),
    [form.qulayliklar]
  )

  const districts = useMemo(() => REGIONS_DATA[form.viloyat] || [], [form.viloyat])
  const mapCenter = useMemo(
    () => [form.latitude, form.longitude],
    [form.latitude, form.longitude]
  )

  const handleChange = (e) => {
    const { name, value } = e.target
    const numericFields = ['xonalar_soni', 'qavat', 'jami_qavat', 'max_kishi', 'bosh_joy', 'narx_usd']
    setForm((prev) => ({
      ...prev,
      [name]: numericFields.includes(name) ? Number(value) : value,
    }))
  }

  const handleAmenity = (name) => {
    setForm((prev) => ({
      ...prev,
      qulayliklar: { ...prev.qulayliklar, [name]: !prev.qulayliklar[name] },
    }))
  }

  const setField = (name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleRentalTypeChange = (type) => {
    setForm((prev) => ({
      ...prev,
      ijara_turi: type,
      max_kishi: type === 'full' ? 1 : Math.max(prev.max_kishi, 2),
      bosh_joy: type === 'full' ? 1 : Math.max(prev.bosh_joy, 1),
    }))
  }

  const handleRegionChange = (region) => {
    if (!region) {
      setForm((prev) => ({
        ...prev,
        viloyat: '',
        tuman: '',
      }))
      return
    }

    const [latitude, longitude] = regionCenters[region] || regionCenters.Andijon
    setForm((prev) => ({
      ...prev,
      viloyat: region,
      tuman: '',
      latitude,
      longitude,
    }))
  }

  const handleLocationPick = (latitude, longitude) => {
    setForm((prev) => ({
      ...prev,
      latitude: Number(latitude.toFixed(6)),
      longitude: Number(longitude.toFixed(6)),
    }))
  }

  const handleImagesUpload = async (event) => {
    const files = Array.from(event.target.files || [])
    if (!files.length) return

    const remainingSlots = Math.max(0, 5 - form.rasmlar.length)
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
        rasmlar: [...prev.rasmlar, ...uploaded.map((item) => item.url)].slice(0, 5),
      }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Rasm yuklashda xatolik yuz berdi')
    } finally {
      setUploadingImages(false)
      event.target.value = ''
    }
  }

  const removeImage = (url) => {
    setForm((prev) => ({
      ...prev,
      rasmlar: prev.rasmlar.filter((imageUrl) => imageUrl !== url),
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { ijara_turi, ...payload } = form
      await createListing({
        ...payload,
        max_kishi: ijara_turi === 'full' ? 1 : payload.max_kishi,
        bosh_joy: ijara_turi === 'full' ? 1 : payload.bosh_joy,
      })
      navigate('/owner')
    } catch (err) {
      setError(err.response?.data?.detail || 'Kvartira yaratishda xatolik yuz berdi')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="owner-create">
      <div className="owner-create__shell">
        <section className="owner-create__hero">
          <button className="owner-create__back" type="button" onClick={() => navigate('/owner')}>
            <ArrowLeft size={18} />
            Boshqaruv paneli
          </button>
          <div>
            <p className="owner-create__eyebrow">Uy egasi paneli</p>
            <h1>Yangi kvartira qo'shish</h1>
            <div className="owner-create__status">
              <ShieldCheck size={16} />
              Saqlangandan keyin nofaol holatda turadi
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

              <div className="owner-field">
                <label htmlFor="nomi">E'lon nomi</label>
                <input
                  id="nomi"
                  type="text"
                  name="nomi"
                  value={form.nomi}
                  onChange={handleChange}
                  placeholder="Masalan: Markazda 2 xonali shinam kvartira"
                  required
                />
              </div>

              <div className="owner-image-uploader">
                <div className="owner-image-uploader__header">
                  <div>
                    <h3>Uy rasmlari</h3>
                    <p>Kamida 2 ta, maksimum 5 ta rasm yuklang.</p>
                  </div>
                  <strong>{form.rasmlar.length}/5</strong>
                </div>

                <div className="owner-image-grid">
                  {form.rasmlar.map((url) => (
                    <div className="owner-image-tile" key={url}>
                      <img src={url} alt="" />
                      <button type="button" onClick={() => removeImage(url)} aria-label="Rasmni o'chirish">
                        <Trash2 size={15} />
                      </button>
                    </div>
                  ))}

                  {form.rasmlar.length < 5 && (
                    <label className="owner-image-add">
                      <ImagePlus size={24} />
                      <span>{uploadingImages ? 'Yuklanmoqda...' : 'Rasm qo‘shish'}</span>
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
                <label htmlFor="tavsifi">Tavsif</label>
                <textarea
                  id="tavsifi"
                  name="tavsifi"
                  value={form.tavsifi}
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
                    className={`owner-choice-card ${form.ijara_turi === type.value ? 'is-selected' : ''}`}
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
                  <label htmlFor="xonalar_soni">Xonalar soni</label>
                  <div className="owner-field__with-icon">
                    <BedDouble size={18} />
                    <input
                      id="xonalar_soni"
                      type="number"
                      name="xonalar_soni"
                      min="1"
                      value={form.xonalar_soni}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="owner-field owner-field--select">
                  <label htmlFor="jins">Kimlar uchun</label>
                  <select id="jins" name="jins" value={form.jins} onChange={handleChange}>
                    {genderOptions.map((option) => (
                      <option value={option.value} key={option.value}>{option.label}</option>
                    ))}
                  </select>
                  <ChevronDown size={18} />
                </div>
              </div>

              <div className="owner-form-grid owner-form-grid--two">
                <div className="owner-field">
                  <label htmlFor="qavat">Qavat</label>
                  <div className="owner-field__with-icon">
                    <Layers size={18} />
                    <input
                      id="qavat"
                      type="number"
                      name="qavat"
                      min="0"
                      value={form.qavat}
                      onChange={handleChange}
                    />
                  </div>
                </div>

                <div className="owner-field">
                  <label htmlFor="jami_qavat">Jami qavat</label>
                  <input
                    id="jami_qavat"
                    type="number"
                    name="jami_qavat"
                    min="1"
                    value={form.jami_qavat}
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
                  <label htmlFor="viloyat">Viloyat</label>
                  <select
                    id="viloyat"
                    name="viloyat"
                    value={form.viloyat}
                    onChange={(event) => handleRegionChange(event.target.value)}
                    required
                  >
                    <option value="">Viloyatni tanlang</option>
                    {Object.keys(REGIONS_DATA).map((region) => (
                      <option value={region} key={region}>{region}</option>
                    ))}
                  </select>
                  <ChevronDown size={18} />
                </div>

                <div className="owner-field owner-field--select">
                  <label htmlFor="tuman">Tuman</label>
                  <select
                    id="tuman"
                    name="tuman"
                    value={form.tuman}
                    onChange={(event) => setField('tuman', event.target.value)}
                    disabled={!form.viloyat}
                    required
                  >
                    <option value="">{form.viloyat ? 'Tumanni tanlang' : 'Avval viloyat tanlang'}</option>
                    {districts.map((district) => (
                      <option value={district} key={district}>{district}</option>
                    ))}
                  </select>
                  <ChevronDown size={18} />
                </div>
              </div>

              <div className="owner-field">
                <label htmlFor="manzil">To'liq manzil</label>
                <div className="owner-field__with-icon">
                  <MapPin size={18} />
                  <input
                    id="manzil"
                    type="text"
                    name="manzil"
                    value={form.manzil}
                    onChange={handleChange}
                    placeholder="Ko'cha, uy raqami, orientir"
                  />
                </div>
              </div>

              <div className={`owner-map-picker ${!form.tuman ? 'is-disabled' : ''}`}>
                <div className="owner-map-picker__header">
                  <div>
                    <h3>Xaritadan aniq joyni belgilang</h3>
                    <p>{form.tuman ? `${form.tuman}, ${form.viloyat}` : 'Xarita uchun avval viloyat va tuman tanlang'}</p>
                  </div>
                  <span>{form.latitude.toFixed(5)}, {form.longitude.toFixed(5)}</span>
                </div>

                {form.tuman ? (
                  <MapContainer
                    key={`${form.viloyat}-${form.tuman}`}
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
                ) : (
                  <div className="owner-map-picker__placeholder">
                    <MapPin size={24} />
                    Viloyat va tuman tanlang, keyin xaritada joyni bosing.
                  </div>
                )}
              </div>
            </section>

            <section className="owner-form-card">
              <div className="owner-form-card__header">
                <span className="owner-form-card__icon"><CircleDollarSign size={20} /></span>
                <div>
                  <p className="owner-create__eyebrow">Narx</p>
                  <h2>Ijara shartlari</h2>
                </div>
              </div>

              <div className="owner-form-grid owner-form-grid--three">
                <div className="owner-field">
                  <label htmlFor="narx_usd">{form.ijara_turi === 'full' ? 'Oylik narx' : 'Kishi boshiga narx'}</label>
                  <div className="owner-field__with-icon">
                    <CircleDollarSign size={18} />
                    <input
                      id="narx_usd"
                      type="number"
                      name="narx_usd"
                      min="0"
                      value={form.narx_usd}
                      onChange={handleChange}
                      placeholder="0"
                    />
                  </div>
                </div>

                <div className="owner-field">
                  <label htmlFor="max_kishi">Maksimal odam</label>
                  <input
                    id="max_kishi"
                    type="number"
                    name="max_kishi"
                    min="1"
                    value={form.max_kishi}
                    disabled={form.ijara_turi === 'full'}
                    onChange={handleChange}
                  />
                </div>

                <div className="owner-field">
                  <label htmlFor="bosh_joy">Bo'sh joy</label>
                  <input
                    id="bosh_joy"
                    type="number"
                    name="bosh_joy"
                    min="1"
                    value={form.bosh_joy}
                    disabled={form.ijara_turi === 'full'}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="owner-create__metric">
                <span><DoorOpen size={18} /> Holati</span>
                <strong>Nofaol</strong>
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
                {amenities.map(({ key, label, icon: Icon }) => (
                  <button
                    type="button"
                    key={key}
                    className={`owner-amenity-chip ${form.qulayliklar[key] ? 'is-selected' : ''}`}
                    onClick={() => handleAmenity(key)}
                  >
                    <Icon size={18} />
                    <span>{label}</span>
                    {form.qulayliklar[key] && <Check size={16} />}
                  </button>
                ))}
              </div>
            </section>

            <div className="owner-create__actions">
              <button type="button" className="owner-create__secondary" onClick={() => navigate('/owner')}>
                Bekor qilish
              </button>
              <button type="submit" className="owner-create__primary" disabled={loading}>
                <Save size={18} />
                {loading ? 'Saqlanmoqda...' : 'Kvartirani saqlash'}
              </button>
            </div>
          </form>

          <aside className="owner-create__summary">
            <div className="owner-summary-card">
              <div className="owner-summary-card__image">
                {form.rasmlar[0] ? <img src={form.rasmlar[0]} alt="" /> : <Home size={34} />}
              </div>
              <div className="owner-summary-card__body">
                <p className="owner-create__eyebrow">Ko'rinish</p>
                <h2>{form.nomi || 'Kvartira nomi'}</h2>
                <span>{[form.tuman, form.viloyat].filter(Boolean).join(', ') || 'Manzil tanlanmagan'}</span>
              </div>
              <div className="owner-summary-card__stats">
                <div>
                  <span>Xona</span>
                  <strong>{form.xonalar_soni}</strong>
                </div>
                <div>
                  <span>Ijara</span>
                  <strong>{form.ijara_turi === 'full' ? 'To‘liq' : 'Joy'}</strong>
                </div>
                <div>
                  <span>Narx</span>
                  <strong>${form.narx_usd}</strong>
                </div>
              </div>
              <div className="owner-summary-card__amenities">
                {selectedAmenities.length === 0 ? (
                  <span>Qulayliklar tanlanmagan</span>
                ) : (
                  selectedAmenities.slice(0, 5).map((item) => <span key={item.key}>{item.label}</span>)
                )}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </main>
  )
}
