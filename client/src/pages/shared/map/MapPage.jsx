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

const LOCATION_PREFERENCE_KEY = 'aparty_map_location_preference'

function getStoredLocationPreference() {
  try {
    const raw = localStorage.getItem(LOCATION_PREFERENCE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function saveLocationPreference(status, location) {
  try {
    localStorage.setItem(
      LOCATION_PREFERENCE_KEY,
      JSON.stringify({ status, location, updatedAt: Date.now() }),
    )
  } catch {
    // Ignore storage quota/permission errors
  }
}

export function MapPage() {
  const { theme, toggleTheme } = useThemeStore()

  // Load saved preference if previously granted or defaulted, to avoid re-prompting on every navigation
  const savedPref = useMemo(() => getStoredLocationPreference(), [])

  // If the user already decided (granted or default), start as 'granted' so no modal is shown on page visits
  const [locationStatus, setLocationStatus] = useState(() => (savedPref?.status ? 'granted' : 'idle'))
  const [userLocation, setUserLocation] = useState(() => savedPref?.location || DEFAULT_ANDIJAN_LOCATION)

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

  const applyDefaultLocation = useCallback(() => {
    locationRequest.current?.()
    requestingLocation.current = false
    setUserLocation(DEFAULT_ANDIJAN_LOCATION)
    setLocationStatus('granted')
    saveLocationPreference('default', DEFAULT_ANDIJAN_LOCATION)
  }, [])

  const requestLocation = useCallback((options = {}) => {
    const { silent = false } = options
    if (requestingLocation.current) return
    requestingLocation.current = true

    if (!silent) {
      setLocationStatus('requesting')
    }

    locationRequest.current = locateBrowser({
      geolocation: navigator.geolocation,
      timeoutMs: 15000,
      onSuccess: (position) => {
        requestingLocation.current = false
        setUserLocation(position)
        setLocationStatus('granted')
        saveLocationPreference('granted', position)
      },
      onError: (status) => {
        requestingLocation.current = false
        if (silent) {
          applyDefaultLocation()
        } else {
          setLocationStatus(status)
        }
      },
    })
  }, [applyDefaultLocation])

  // Handle initial location check on first visit or silent background update on revisiting
  useEffect(() => {
    if (savedPref?.status === 'granted' && savedPref?.location) {
      // User previously gave permission. If browser still has permission granted, update location silently in background
      if (navigator.permissions?.query) {
        navigator.permissions.query({ name: 'geolocation' }).then((result) => {
          if (result.state === 'granted') {
            locateBrowser({
              geolocation: navigator.geolocation,
              onSuccess: (position) => {
                setUserLocation(position)
                saveLocationPreference('granted', position)
              },
              onError: () => {},
            })
          }
        }).catch(() => {})
      }
      return
    }

    if (savedPref?.status === 'default') {
      // User explicitly previously selected default location; do nothing
      return
    }

    // First visit without saved preference: check browser permissions
    if (navigator.permissions?.query) {
      navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        if (result.state === 'granted') {
          // Native permission is already granted, locate silently without modal
          requestLocation({ silent: true })
        } else if (result.state === 'denied') {
          // Permission is blocked, fall back to default
          applyDefaultLocation()
        }
        // If 'prompt', locationStatus stays 'idle' and modal is shown once
      }).catch(() => {})
    }
  }, [savedPref, requestLocation, applyDefaultLocation])

  useEffect(() => () => locationRequest.current?.(), [])

  useEffect(() => {
    let active = true

    fetchMapListings()
      .then((data) => { if (active) setListings(data) })
      .catch((error) => {
        console.error('Map listings load failed:', error)
        if (active) setListings([])
      })
      .finally(() => active && setLoading(false))

    return () => { active = false }
  }, [])

  const properties = useMemo(() => toMapProperties(listings, userLocation), [listings, userLocation])

  // Manual locate from the map control button: request directly without interrupting map view
  const handleMapLocate = useCallback(() => {
    requestLocation({ silent: false })
  }, [requestLocation])

  const boundsDebounce = useRef(null)
  const isFirstBounds = useRef(true)

  const handleBoundsChange = useCallback((newBounds) => {
    if (!newBounds || typeof newBounds.getSouth !== 'function') return
    if (isFirstBounds.current) {
      isFirstBounds.current = false
      return
    }
    clearTimeout(boundsDebounce.current)
    boundsDebounce.current = setTimeout(() => {
      fetchMapListings({
        min_lat: newBounds.getSouth(),
        max_lat: newBounds.getNorth(),
        min_lng: newBounds.getWest(),
        max_lng: newBounds.getEast(),
      })
        .then((data) => {
          if (Array.isArray(data)) {
            setListings(data)
          }
        })
        .catch(() => {})
    }, 450)
  }, [])

  return (
    <section className="map-page">
      <div className={`map-shell ${immersive ? 'immersive' : ''} ${selectedProperty ? 'modal-open' : ''} ${mapOptions.nightMap ? 'night-map' : 'clean-map'} ${mapOptions.compactTopbar ? 'compact-topbar' : ''}`}>
        <div className="map-stage">
          <MapView
            center={userLocation}
            properties={properties}
            selectedProperty={selectedProperty}
            onSelectProperty={setSelectedProperty}
            onLocate={handleMapLocate}
            onToggleFullscreen={() => setImmersive((value) => !value)}
            theme={theme}
            onToggleTheme={toggleTheme}
            mapOptions={mapOptions}
            onBoundsChange={handleBoundsChange}
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
        onRequest={() => requestLocation({ silent: false })}
        onUseDefault={applyDefaultLocation}
      />
      <PropertyBottomSheet property={selectedProperty} onClose={() => setSelectedProperty(null)} />
    </section>
  )
}
