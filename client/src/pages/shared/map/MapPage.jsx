import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { SearchX } from 'lucide-react'
import { MapView } from '../../../components/map/MapView'
import { PropertyBottomSheet } from '../../../components/map/PropertyBottomSheet'
import { LocationPermissionModal } from '../../../components/map/LocationPermissionModal'
import { DEFAULT_ANDIJAN_LOCATION } from '../../../utils/geo'
import { locateBrowser } from '../../../utils/geolocation'
import { MAP_LISTING_LIMIT, fetchMapListings, toMapProperties } from '../../../services/mapPropertyService'
import { peekCache } from '../../../services/browserCache'
import { useThemeStore } from '../../../store/themeStore'
import './MapPage.scss'

export function MapPage() {
  const { theme, toggleTheme } = useThemeStore()
  const [locationStatus, setLocationStatus] = useState('idle')
  const [userLocation, setUserLocation] = useState(DEFAULT_ANDIJAN_LOCATION)
  // The same public search results the search page and home page use, so a session that already
  // browsed listings opens the map with pins straight away instead of a blank loading state.
  const cachedListings = peekCache('/listings/search', { page: 1, limit: MAP_LISTING_LIMIT })
  const [listings, setListings] = useState(() => cachedListings?.listings || [])
  const [selectedProperty, setSelectedProperty] = useState(null)
  const [loading, setLoading] = useState(!cachedListings)
  const [immersive, setImmersive] = useState(false)
  const locationRequest = useRef(null)
  const requestingLocation = useRef(false)
  const mapOptions = {
    premiumPins: true,
    radar: true,
    nightMap: theme === 'dark',
    compactTopbar: false,
  }

  const requestLocation = useCallback(() => {
    if (requestingLocation.current) return
    requestingLocation.current = true
    setLocationStatus('requesting')
    locationRequest.current = locateBrowser({
      geolocation: navigator.geolocation,
      onSuccess: position => {
        requestingLocation.current = false
        setUserLocation(position)
        setLocationStatus('granted')
      },
      onError: status => {
        requestingLocation.current = false
        setLocationStatus(status)
      },
    })
  }, [])

  useEffect(() => () => locationRequest.current?.(), [])

  useEffect(() => {
    let active = true

    fetchMapListings()
      .then(data => { if (active) setListings(data) })
      .catch(error => {
        console.error('Map listings load failed:', error)
        if (active) setListings([])
      })
      .finally(() => active && setLoading(false))

    return () => { active = false }
  }, [])

  const properties = useMemo(() => toMapProperties(listings, userLocation), [listings, userLocation])

  const useDefaultLocation = () => {
    locationRequest.current?.()
    requestingLocation.current = false
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
