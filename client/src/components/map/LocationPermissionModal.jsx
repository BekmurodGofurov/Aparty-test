import { AnimatePresence, motion } from 'framer-motion'
import { LocateFixed, MapPin, Navigation } from 'lucide-react'

export function LocationPermissionModal({ status, onRequest, onUseDefault }) {
  const visible = status === 'idle' || status === 'requesting' || status === 'denied' || status === 'unsupported'

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="location-permission-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            className="location-permission-modal"
            initial={{ scale: 0.94, y: 18, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.94, y: 18, opacity: 0 }}
            transition={{ duration: 0.22 }}
          >
            <span className="permission-icon"><Navigation size={22} /></span>
            <h2>Joylashuvingizni aniqlaymiz</h2>
            <p>
              Yaqin atrofdagi kvartira va uylarni masofa bo'yicha ko'rsatish uchun brauzer geolocation ruxsati kerak.
            </p>
            {status === 'denied' && <small>Ruxsat berilmadi. Brauzer sozlamalaridan location ruxsatini yoqishingiz mumkin.</small>}
            {status === 'unsupported' && <small>Bu brauzer Geolocation API ni qo'llab-quvvatlamaydi.</small>}
            <div className="permission-actions">
              <button type="button" className="permission-primary" onClick={onRequest} disabled={status === 'requesting'}>
                <LocateFixed size={17} />
                {status === 'requesting' ? 'Aniqlanmoqda...' : 'Ruxsat berish'}
              </button>
              <button type="button" className="permission-secondary" onClick={onUseDefault}>
                <MapPin size={17} />
                Andijon markazi
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
