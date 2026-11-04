import { Marker } from 'react-leaflet'
import L from 'leaflet'

const escapeHtml = (str) =>
  String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

export function PropertyMarker({ property, selected, onSelect, premium = true }) {
  const safeTitle = escapeHtml(property.title)
  const safeCurrency = escapeHtml(property.currency)
  const safePrice = escapeHtml(property.price)

  const priceIcon = L.divIcon({
    className: `property-price-marker ${premium ? 'premium' : 'simple'} ${selected ? 'active' : ''}`,
    html: `<button type="button" aria-label="${safeTitle}"><span>${safeCurrency}${safePrice}</span></button>`,
    iconSize: [92, 42],
    iconAnchor: [46, 21],
  })

  return (
    <Marker
      position={[property.lat, property.lng]}
      icon={priceIcon}
      zIndexOffset={selected ? 800 : 200}
      eventHandlers={{ click: () => onSelect(property) }}
    />
  )
}
