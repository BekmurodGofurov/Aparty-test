import { useEffect, useMemo, useState } from 'react'
import { CircleMarker, MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { PropertyMarker } from './PropertyMarker'
import { MapControls } from './MapControls'

function MapCenter({ center }) {
  const map = useMap()

  useEffect(() => {
    map.flyTo([center.lat, center.lng], 14, { duration: 0.8 })
  }, [center, map])

  return null
}

function VisibleBoundsTracker({ onBoundsChange }) {
  const map = useMapEvents({
    moveend: () => onBoundsChange(map.getBounds()),
    zoomend: () => onBoundsChange(map.getBounds()),
  })

  useEffect(() => {
    onBoundsChange(map.getBounds())
  }, [map, onBoundsChange])

  return null
}

export function MapView({
  center,
  properties,
  selectedProperty,
  onSelectProperty,
  onLocate,
  onToggleFullscreen,
  theme,
  onToggleTheme,
  mapOptions,
}) {
  const [bounds, setBounds] = useState(null)
  const [markerLimit, setMarkerLimit] = useState(10)

  useEffect(() => {
    setMarkerLimit(10)
    const id = window.setTimeout(() => setMarkerLimit(80), 140)
    return () => window.clearTimeout(id)
  }, [properties])

  const visibleProperties = useMemo(() => {
    const withinBounds = bounds
      ? properties.filter(property => bounds.pad(0.24).contains([property.lat, property.lng]))
      : properties

    return withinBounds.slice(0, markerLimit)
  }, [bounds, markerLimit, properties])

  return (
    <MapContainer center={[center.lat, center.lng]} zoom={14} minZoom={11} zoomControl={false} className="real-estate-map">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapCenter center={center} />
      <VisibleBoundsTracker onBoundsChange={setBounds} />
      <MapControls
        onLocate={onLocate}
        onToggleFullscreen={onToggleFullscreen}
        theme={theme}
        onToggleTheme={onToggleTheme}
      />
      {mapOptions?.radar !== false && <CurrentLocationMarker center={center} />}
      {visibleProperties.map(property => (
        <PropertyMarker
          key={property.id}
          property={property}
          selected={selectedProperty?.id === property.id}
          onSelect={onSelectProperty}
          premium={mapOptions?.premiumPins !== false}
        />
      ))}
    </MapContainer>
  )
}

function CurrentLocationMarker({ center }) {
  const icon = useMemo(() => L.divIcon({
    className: 'current-location-marker',
    html: '<span class="radar-ring ring-one"></span><span class="radar-ring ring-two"></span><span class="location-dot"></span>',
    iconSize: [74, 74],
    iconAnchor: [37, 37],
  }), [])

  return (
    <>
      <CircleMarker
        center={[center.lat, center.lng]}
        radius={32}
        pathOptions={{ color: '#38bdf8', weight: 1, fillColor: '#38bdf8', fillOpacity: 0.08 }}
      />
      <PropertyMarkerShim center={center} icon={icon} />
    </>
  )
}

function PropertyMarkerShim({ center, icon }) {
  return <Marker position={[center.lat, center.lng]} icon={icon} interactive={false} zIndexOffset={1000} />
}
