/**
 * REUSABLE COMPONENT LIBRARY
 * Premium Glass Components
 */

import { motion } from 'framer-motion'
import { ANIMATIONS } from '../../styles/design-system'
import './PremiumComponents.scss'

// ════════════════════════════════════════════════════════
// GLASS CARD COMPONENT
// ════════════════════════════════════════════════════════
export function GlassCard({
  children,
  variant = 'default',
  className = '',
  ...props
}) {
  return (
    <motion.div
      className={`premium-glass-card variant-${variant} ${className}`}
      {...ANIMATIONS.fadeInUp}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════
// BUTTON COMPONENTS
// ════════════════════════════════════════════════════════
export function Button({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  isLoading = false,
  ...props
}) {
  return (
    <motion.button
      className={`premium-btn variant-${variant} size-${size} ${className}`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      disabled={isLoading}
      {...props}
    >
      {isLoading && <span className="loader">⏳</span>}
      {children}
    </motion.button>
  )
}

// ════════════════════════════════════════════════════════
// BADGE COMPONENT
// ════════════════════════════════════════════════════════
export function Badge({ children, variant = 'primary', className = '' }) {
  return (
    <span className={`premium-badge variant-${variant} ${className}`}>
      {children}
    </span>
  )
}

// ════════════════════════════════════════════════════════
// PREMIUM INPUT
// ════════════════════════════════════════════════════════
export function PremiumInput({ label, error, icon, className = '', ...props }) {
  return (
    <div className={`premium-input-wrapper ${className}`}>
      {label && <label>{label}</label>}
      <div className="input-container">
        {icon && <span className="icon">{icon}</span>}
        <input {...props} />
      </div>
      {error && <p className="error-text">{error}</p>}
    </div>
  )
}

// ════════════════════════════════════════════════════════
// SECTION WRAPPER
// ════════════════════════════════════════════════════════
export function Section({ children, title, subtitle, className = '', fullWidth = false }) {
  return (
    <motion.section
      className={`premium-section ${className}`}
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.6 }}
    >
      <div className={fullWidth ? '' : 'section-container'}>
        {(title || subtitle) && (
          <div className="section-header">
            {title && <h2>{title}</h2>}
            {subtitle && <p>{subtitle}</p>}
          </div>
        )}
        {children}
      </div>
    </motion.section>
  )
}

// ════════════════════════════════════════════════════════
// SKELETON LOADER
// ════════════════════════════════════════════════════════
export function SkeletonBox({ width = '100%', height = '1rem', className = '' }) {
  return (
    <div
      className={`skeleton-box ${className}`}
      style={{ width, height }}
    />
  )
}

// ════════════════════════════════════════════════════════
// SCROLL REVEAL ANIMATION
// ════════════════════════════════════════════════════════
export function ScrollReveal({ children, className = '', ...props }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '0px' }}
      transition={{ duration: 0.6 }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════
// STAGGER CONTAINER
// ════════════════════════════════════════════════════════
export function StaggerContainer({ children, staggerDelay = 0.1, className = '' }) {
  return (
    <motion.div
      className={className}
      initial="initial"
      whileInView="animate"
      viewport={{ once: true, margin: '-20px' }}
      variants={{
        animate: {
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
    >
      {children}
    </motion.div>
  )
}

// ════════════════════════════════════════════════════════
// STAGGER ITEM
// ════════════════════════════════════════════════════════
export function StaggerItem({ children, className = '', style }) {
  return (
    <motion.div
      className={className}
      style={style}
      variants={{
        initial: { opacity: 0, y: 20 },
        animate: { opacity: 1, y: 0 },
      }}
      transition={{ duration: 0.4 }}
    >
      {children}
    </motion.div>
  )
}
