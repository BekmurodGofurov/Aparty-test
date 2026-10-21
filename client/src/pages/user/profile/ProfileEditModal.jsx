import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion'
import { X, Camera, User, Phone } from 'lucide-react'
import { PremiumInput, Button } from '../../../components/ui/PremiumComponents'
import { useModalDialog } from '../../../hooks/useModalDialog'
import { userService } from '../../../services/userService'
import { uploadService } from '../../../services/uploadService'
import { getErrorMessage } from '../../../utils/auth'
import { FallbackImage } from '../../../components/ui/FallbackImage'
import './ProfileEditModal.scss'

// The phone number comes from Telegram and cannot be changed here, so it is shown read-only.
export function ProfileEditModal({ isOpen, onClose, userData, onUpdate }) {
  const [name, setName] = useState(userData?.ism || '')
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const dialogRef = useRef(null)
  const reduceMotion = useReducedMotion()
  useModalDialog({ open: isOpen, onClose, dialogRef, initialFocus: '.close' })

  useEffect(() => {
    if (isOpen) {
      setName(userData?.ism || '')
      setError('')
    }
  }, [isOpen, userData])

  const applyUpdate = (updatedUser) => {
    window.dispatchEvent(new CustomEvent('user-updated', { detail: updatedUser }))
    onUpdate(updatedUser)
  }

  const handleSave = async () => {
    if (!name.trim()) {
      setError('Ism kiritilishi shart')
      return
    }
    setLoading(true)
    setError('')
    try {
      applyUpdate(await userService.updateProfile({ ism: name.trim() }))
      onClose()
    } catch (err) {
      setError(getErrorMessage(err, 'Xatolik yuz berdi'))
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const { url } = await uploadService.uploadImage(file)
      applyUpdate(await userService.updateProfile({ rasm_url: url }))
    } catch (err) {
      setError(getErrorMessage(err, 'Rasm yuklashda xatolik yuz berdi'))
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  // Use Portal to render at body level for perfect centering
  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="modal-overlay-clean">
          <motion.div
            className="backdrop"
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduceMotion ? 0 : 0.18 }}
            onClick={onClose}
          />
          <motion.div
            className="edit-modal-minimal"
            ref={dialogRef}
            role="dialog"
            aria-modal="true"
            aria-label="Profilni tahrirlash"
            tabIndex={-1}
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={reduceMotion ? { duration: 0 } : { type: 'spring', damping: 25, stiffness: 350 }}
          >
            <div className="modal-header">
              <h3>Profilni tahrirlash</h3>
              <button className="close" type="button" aria-label="Yopish" onClick={onClose}><X size={20}/></button>
            </div>

            <div className="modal-body">
              <div className="avatar-edit-minimal">
                <div className="img-box">
                  <FallbackImage
                    src={userData?.rasm_url}
                    alt="Profile"
                    fallback={<div className="placeholder">{userData?.ism?.charAt(0)}</div>}
                  />
                  <input type="file" id="modal-upload" hidden accept="image/*" onChange={handleImageUpload} />
                  <label htmlFor="modal-upload" className="cam-btn"><Camera size={14}/></label>
                </div>
                {uploading && <span className="uploading-txt">Yuklanmoqda...</span>}
              </div>

              <div className="form-content">
                <PremiumInput
                  label="To'liq ism"
                  name="ism"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  icon={<User size={18}/>}
                />
                <div className="phone-input-wrap">
                  <PremiumInput
                    label="Telefon raqami"
                    name="telefon"
                    value={userData?.telefon || ''}
                    icon={<Phone size={18}/>}
                    disabled
                  />
                  <p className="field-hint">Raqam Telegram hisobingizdan olinadi va o'zgartirilmaydi</p>
                </div>
                {error && <p className="field-hint" role="alert">{error}</p>}
              </div>
            </div>

            <div className="modal-footer">
              <Button variant="outline" onClick={onClose} disabled={loading}>Bekor qilish</Button>
              <Button variant="primary" onClick={handleSave} isLoading={loading}>Saqlash</Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  )
}
