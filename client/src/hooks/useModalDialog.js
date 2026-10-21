import { useEffect, useRef } from 'react'

// Dialogs using this hook render through a portal outside #root.
export function useModalDialog({ open, onClose, dialogRef, initialFocus = 'button' }) {
  const closeRef = useRef(onClose)
  useEffect(() => { closeRef.current = onClose }, [onClose])

  useEffect(() => {
    if (!open) return undefined
    const previousFocus = document.activeElement
    const previousOverflow = document.body.style.overflow
    const root = document.getElementById('root')
    const previousInert = root?.inert
    document.body.style.overflow = 'hidden'
    if (root) root.inert = true
    const dialog = dialogRef.current
    const focusTarget = dialog?.querySelector(initialFocus) || dialog
    focusTarget?.focus({ preventScroll: true })

    const handleKeyDown = event => {
      if (event.key === 'Escape' && closeRef.current) {
        event.preventDefault()
        closeRef.current()
        return
      }
      if (event.key !== 'Tab' || !dialog) return
      const controls = [...dialog.querySelectorAll('button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), summary, [tabindex="0"]')]
        .filter(element => element.getClientRects().length > 0)
      const first = controls[0]
      const last = controls.at(-1)
      if (!first) { event.preventDefault(); dialog.focus() }
      else if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      if (root) root.inert = previousInert
      document.removeEventListener('keydown', handleKeyDown)
      if (previousFocus?.isConnected && !previousFocus.closest('[inert]')) previousFocus.focus({ preventScroll: true })
    }
  }, [open, dialogRef, initialFocus])
}
