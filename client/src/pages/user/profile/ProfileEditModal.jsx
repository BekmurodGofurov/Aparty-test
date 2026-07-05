import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Camera, Trash2, Save, User, Phone, Lock, Eye, EyeOff, AlertCircle, CheckCircle2 } from 'lucide-react'
import { PremiumInput, Button } from '../../../components/ui/PremiumComponents'
import { userService } from '../../../services/userService'
import { uploadService } from '../../../services/uploadService'
import { useTranslation } from 'react-i18next'
import './ProfileEditModal.scss'

export function ProfileEditModal({ isOpen, onClose, userData, onUpdate, mode = 'all' }) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState({
    ism: userData?.ism || '',
    telefon: userData?.telefon || '',
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
  
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showPass, setShowPass] = useState(false)
  const [phoneConfirmStep, setPhoneConfirmStep] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setFormData({
        ism: userData?.ism || '',
        telefon: userData?.telefon || '',
        old_password: '',
        new_password: '',
        confirm_password: ''
      })
      setPhoneConfirmStep(false)
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [isOpen, userData])

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSave = async () => {
    if (mode === 'all' || mode === 'name') {
      if (!formData.ism.trim()) return alert("Ism kiritilishi shart")
    }

    if ((mode === 'all' || mode === 'phone') && formData.telefon !== userData?.telefon && !phoneConfirmStep) {
      setPhoneConfirmStep(true)
      return
    }

    setLoading(true)
    try {
      let payload = {}
      if (mode === 'all') {
        payload = { ism: formData.ism }
      } else if (mode === 'name') {
        payload = { ism: formData.ism }
      } else if (mode === 'phone') {
        payload = { telefon: formData.telefon }
      } else if (mode === 'password') {
        if (formData.new_password !== formData.confirm_password) throw new Error("Parollar mos kelmadi")
        payload = { old_password: formData.old_password, new_password: formData.new_password }
      }
      
      const updatedUser = await userService.updateProfile(payload)
      window.dispatchEvent(new CustomEvent('user-updated', { detail: updatedUser }))
      onUpdate(updatedUser)
      onClose()
    } catch (err) {
      alert(err.message || "Xatolik yuz berdi")
    } finally {
      setLoading(false)
    }
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const { url } = await uploadService.uploadImage(file)
      const updatedUser = await userService.updateProfile({ rasm_url: url })
      window.dispatchEvent(new CustomEvent('user-updated', { detail: updatedUser }))
      onUpdate(updatedUser)
    } catch (err) {
      alert('Rasm yuklashda xatolik yuz berdi')
    } finally {
      setUploading(false)
    }
  }

  // Use Portal to render at body level for perfect centering
  return createPortal(
    <AnimatePresence>
      {isOpen && (
        <div className="modal-overlay-clean">
          <motion.div 
            className="backdrop" 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }} 
            onClick={onClose} 
          />
          <motion.div 
            className="edit-modal-minimal"
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 350 }}
          >
            <div className="modal-header">
              <h3>{mode === 'password' ? 'Parolni o\'zgartirish' : 'Profilni tahrirlash'}</h3>
              <button className="close" onClick={onClose}><X size={20}/></button>
            </div>

            <div className="modal-body">
              {mode === 'all' && (
                <div className="avatar-edit-minimal">
                  <div className="img-box">
                    {userData?.rasm_url ? <img src={userData.rasm_url} alt="Profile" /> : <div className="placeholder">{userData?.ism?.charAt(0)}</div>}
                    <input type="file" id="modal-upload" hidden accept="image/*" onChange={handleImageUpload} />
                    <label htmlFor="modal-upload" className="cam-btn"><Camera size={14}/></label>
                  </div>
                  {uploading && <span className="uploading-txt">Yuklanmoqda...</span>}
                </div>
              )}

              <div className="form-content">
                {(mode === 'all' || mode === 'name') && (
                  <PremiumInput 
                    label="To'liq ism"
                    name="ism"
                    value={formData.ism}
                    onChange={handleChange}
                    icon={<User size={18}/>}
                  />
                )}

                {(mode === 'all' || mode === 'phone') && (
                  <div className={`phone-input-wrap ${phoneConfirmStep ? 'confirm-mode' : ''}`}>
                    <PremiumInput 
                      label="Telefon raqami"
                      name="telefon"
                      value={formData.telefon}
                      onChange={handleChange}
                      icon={<Phone size={18}/>}
                      disabled={phoneConfirmStep || mode === 'all'}
                    />
                    {mode === 'all' && (
                      <p className="field-hint">Raqamni o'zgartirish uchun sozlamalardan foydalaning</p>
                    )}
                    {phoneConfirmStep && (
                      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="phone-warning">
                        <AlertCircle size={14}/>
                        <span>Raqamni o'zgartirishni tasdiqlaysizmi?</span>
                      </motion.div>
                    )}
                  </div>
                )}

                {mode === 'password' && (
                  <>
                    <PremiumInput 
                      label="Hozirgi parol"
                      name="old_password"
                      type={showPass ? 'text' : 'password'}
                      value={formData.old_password}
                      onChange={handleChange}
                      icon={<Lock size={18}/>}
                      rightIcon={showPass ? <EyeOff size={18} onClick={() => setShowPass(false)}/> : <Eye size={18} onClick={() => setShowPass(true)}/>}
                    />
                    <PremiumInput 
                      label="Yangi parol"
                      name="new_password"
                      type={showPass ? 'text' : 'password'}
                      value={formData.new_password}
                      onChange={handleChange}
                      icon={<Lock size={18}/>}
                    />
                    <PremiumInput 
                      label="Parolni tasdiqlash"
                      name="confirm_password"
                      type={showPass ? 'text' : 'password'}
                      value={formData.confirm_password}
                      onChange={handleChange}
                      icon={<Lock size={18}/>}
                    />
                  </>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <Button variant="outline" onClick={onClose} disabled={loading}>Bekor qilish</Button>
              <Button variant="primary" onClick={handleSave} isLoading={loading}>
                {phoneConfirmStep ? 'Ha, tasdiqlayman' : 'Saqlash'}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>,
    document.body
  )
}
