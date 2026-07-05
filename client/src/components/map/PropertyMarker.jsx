import { Marker } from 'react-leaflet'
import L from 'leaflet'

export function PropertyMarker({ property, selected, onSelect, premium = true }) {
  const priceIcon = L.divIcon({
    className: `property-price-marker ${premium ? 'premium' : 'simple'} ${selected ? 'active' : ''}`,
    html: `<button type="button" aria-label="${property.title}"><span>${property.currency}${property.price}</span></button>`,
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
