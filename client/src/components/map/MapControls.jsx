import { Expand, LocateFixed, Minus, Moon, Plus, Sun } from 'lucide-react'
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { useMap } from 'react-leaflet'

export function MapControls({ onLocate, onToggleFullscreen, theme, onToggleTheme }) {
  const map = useMap()
  const controlsRef = useRef(null)

  useEffect(() => {
    const controls = controlsRef.current
    L.DomEvent.disableClickPropagation(controls)
    L.DomEvent.disableScrollPropagation(controls)
    L.DomEvent.on(controls, 'keydown', L.DomEvent.stopPropagation)
    return () => L.DomEvent.off(controls)
  }, [])

  return (
    <div ref={controlsRef} className="premium-map-controls" aria-label="Xarita boshqaruvlari">
      <button type="button" onClick={onLocate} aria-label="Mening joylashuvim">
        <LocateFixed size={18} />
      </button>
      <button type="button" onClick={() => map.zoomIn()} aria-label="Kattalashtirish">
        <Plus size={18} />
      </button>
      <button type="button" onClick={() => map.zoomOut()} aria-label="Kichiklashtirish">
        <Minus size={18} />
      </button>
      <button type="button" onClick={onToggleFullscreen} aria-label="Fullscreen">
        <Expand size={18} />
      </button>
      <button type="button" onClick={onToggleTheme} aria-label="Mavzuni almashtirish">
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>
    </div>
  )
}
