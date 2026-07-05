import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { ExternalLink, MapPin, Navigation } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './ListingMap.scss'

// Fix for default marker icon in Leaflet
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
})
L.Marker.prototype.options.icon = DefaultIcon

const buildYandexMapsUrl = (lat, lng) => {
  const coords = `${Number(lng).toFixed(6)},${Number(lat).toFixed(6)}`
  return `https://yandex.com/maps/?ll=${coords}&mode=whatshere&whatshere%5Bpoint%5D=${coords}&z=17`
}

export function ListingMap({ lat, lng, address, fullscreen = false }) {
  if (!lat || !lng) return null

  const yandexUrl = buildYandexMapsUrl(lat, lng)
  const openYandexMaps = () => {
    window.open(yandexUrl, '_blank', 'noopener,noreferrer')
  }

  return (
    <div
      className={"listing-map-container" + (fullscreen ? ' fullscreen' : '')}
    >
      <div className="map-hud">
        <span className="map-pin-orb"><MapPin size={16} /></span>
        <div>
          <strong>Yandex Maps</strong>
          <small>{address || 'Manzil'}</small>
        </div>
        <span className="map-nav-chip"><Navigation size={14} /></span>
      </div>
      <MapContainer center={[lat, lng]} zoom={fullscreen ? 16 : 15} scrollWheelZoom={fullscreen} className={"listing-map" + (fullscreen ? ' listing-map-fullscreen' : '')}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Marker position={[lat, lng]}>
          <Popup>
            {address || "Manzil"}
          </Popup>
        </Marker>
      </MapContainer>
      <a
        className="map-click-target"
        href={yandexUrl}
        target="_blank"
        rel="noreferrer"
        aria-label="Joylashuvni Yandex Maps orqali ochish"
      />
      <button
        type="button"
        className="open-yandex-btn"
        onClick={(event) => {
          event.stopPropagation()
          openYandexMaps()
        }}
      >
        <ExternalLink size={15} />
        Yandex Maps
      </button>
    </div>
  )
}
