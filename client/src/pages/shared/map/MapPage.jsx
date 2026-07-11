import { useCallback, useEffect, useState } from 'react'
import { SearchX } from 'lucide-react'
import { MapView } from '../../../components/map/MapView'
import { PropertyBottomSheet } from '../../../components/map/PropertyBottomSheet'
import { LocationPermissionModal } from '../../../components/map/LocationPermissionModal'
import { DEFAULT_ANDIJAN_LOCATION } from '../../../utils/geo'
import { mapPropertyApi } from '../../../services/mapPropertyService'
import { useThemeStore } from '../../../store/themeStore'
import './MapPage.scss'

export function MapPage() {
  const { theme, toggleTheme } = useThemeStore()
  const [locationStatus, setLocationStatus] = useState('idle')
  const [userLocation, setUserLocation] = useState(DEFAULT_ANDIJAN_LOCATION)
  const [properties, setProperties] = useState([])
  const [selectedProperty, setSelectedProperty] = useState(null)
  const [loading, setLoading] = useState(true)
  const [immersive, setImmersive] = useState(false)
  const mapOptions = {
    premiumPins: true,
    radar: true,
    nightMap: theme === 'dark',
    compactTopbar: false,
  }

  const requestLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setLocationStatus('unsupported')
      return
    }

    setLocationStatus('requesting')
    navigator.geolocation.getCurrentPosition(
      position => {
        setUserLocation({
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        })
        setLocationStatus('granted')
      },
      () => setLocationStatus('denied'),
      { enableHighAccuracy: true, timeout: 9000, maximumAge: 60000 },
    )
  }, [])

  useEffect(() => {
    requestLocation()
  }, [requestLocation])

  useEffect(() => {
    let active = true
    setLoading(true)

    mapPropertyApi.fetchNearby({ userLocation })
      .then(data => {
        if (!active) return
        setProperties(data)
        setSelectedProperty(current => current && !data.some(item => item.id === current.id) ? null : current)
      })
      .catch(error => {
        console.error('Map listings load failed:', error)
        if (!active) return
        setProperties([])
        setSelectedProperty(null)
      })
      .finally(() => active && setLoading(false))

    return () => { active = false }
  }, [userLocation])

  const useDefaultLocation = () => {
    setUserLocation(DEFAULT_ANDIJAN_LOCATION)
    setLocationStatus('granted')
  }

  return (
    <section className="map-page">
      <div className={`map-shell ${immersive ? 'immersive' : ''} ${selectedProperty ? 'modal-open' : ''} ${mapOptions.nightMap ? 'night-map' : 'clean-map'} ${mapOptions.compactTopbar ? 'compact-topbar' : ''}`}>
        <div className="map-stage">
          <MapView
            center={userLocation}
            properties={properties}
            selectedProperty={selectedProperty}
            onSelectProperty={setSelectedProperty}
            onLocate={requestLocation}
            onToggleFullscreen={() => setImmersive(value => !value)}
            theme={theme}
            onToggleTheme={toggleTheme}
            mapOptions={mapOptions}
          />
          {loading && (
            <div className="map-skeleton-stack" aria-label="Xarita yuklanmoqda">
              <span />
              <span />
              <span />
            </div>
          )}
          {!loading && properties.length === 0 && (
            <div className="map-empty">
              <SearchX size={26} />
              <strong>E'lon topilmadi</strong>
              <span>Hozircha xaritada yaqin atrofdagi e'lonlar ko'rinmayapti.</span>
            </div>
          )}
        </div>
      </div>

      <LocationPermissionModal
        status={locationStatus}
        onRequest={requestLocation}
        onUseDefault={useDefaultLocation}
      />
      <PropertyBottomSheet property={selectedProperty} onClose={() => setSelectedProperty(null)} />
    </section>
  )
}
