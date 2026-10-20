import { useRef } from 'react'
import { createPortal } from 'react-dom'
import { useTranslation } from 'react-i18next'
import { useModalDialog } from '../../hooks/useModalDialog'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { LocateFixed, MapPin, Navigation } from 'lucide-react'

export function LocationPermissionModal({ status, onRequest, onUseDefault }) {
  const { t } = useTranslation()
  const visible = status !== 'granted'
  const requesting = status === 'requesting'
  const error = ['denied', 'unavailable', 'timeout', 'unsupported'].includes(status)
  const dialogRef = useRef(null)
  const reduceMotion = useReducedMotion()
  useModalDialog({ open: visible, onClose: onUseDefault, dialogRef, initialFocus: '.permission-secondary' })

  return createPortal(
    <AnimatePresence>
      {visible && (
        <motion.div
          className="location-permission-backdrop"
          initial={reduceMotion ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.18 }}
        >
          <motion.div
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="map-permission-title"
            aria-describedby="map-permission-description"
            tabIndex={-1}
            className="location-permission-modal"
            initial={reduceMotion ? false : { scale: 0.94, y: 18, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.94, y: 18, opacity: 0 }}
            transition={{ duration: reduceMotion ? 0 : 0.22 }}
          >
            <span className="permission-icon"><Navigation size={22} /></span>
            <h2 id="map-permission-title">{t('map_location.title')}</h2>
            <p id="map-permission-description">{t('map_location.description')}</p>
            <div className="permission-status" role="status" aria-live="polite">
              {requesting && <small>{t('map_location.requesting_hint')}</small>}
              {error && <small>{t('map_location.' + status)}</small>}
            </div>
            <div className="permission-actions">
              <button type="button" className="permission-primary" onClick={onRequest} disabled={requesting || status === 'unsupported'}>
                <LocateFixed size={17} />
                {t(requesting ? 'map_location.requesting' : error ? 'map_location.retry' : 'map_location.allow')}
              </button>
              <button type="button" className="permission-secondary" onClick={onUseDefault}>
                <MapPin size={17} />{t('map_location.default')}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body,
  )
}
