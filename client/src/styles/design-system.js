/**
 * APARTY.UZ - PREMIUM DESIGN SYSTEM
 * Liquid Glass Architecture
 */

export const DESIGN_TOKENS = {
  colors: {
    dark: {
      bg: { 
        base: '#020617',     // Deeper Navy
        elevated: '#0f172a', // Slate 900
        card: 'rgba(15, 23, 42, 0.3)' 
      },
      glass: {
        bg: 'rgba(255, 255, 255, 0.03)',
        border: 'rgba(255, 255, 255, 0.08)',
        hover: 'rgba(255, 255, 255, 0.06)',
        blur: 'blur(16px) saturate(180%)',
        shadow: '0 20px 50px rgba(0, 0, 0, 0.5)',
        shadowHover: '0 30px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(59, 130, 246, 0.15)'
      },
      text: { 
        primary: '#F8FAFC',   // Slate 50
        secondary: '#94A3B8', // Slate 400
        muted: '#64748B',    // Slate 500
        subtle: '#334155'     // Slate 700
      },
      accent: {
        primary: '#3b82f6',   // Blue 500
        primaryLight: '#60a5fa', 
        primaryGlow: 'rgba(59, 130, 246, 0.25)',
        secondary: '#8b5cf6', // Violet 500
        success: '#10b981',   // Emerald 500
        warning: '#f59e0b',   // Amber 500
        error: '#ef4444',     // Red 500
      },
      gradient: {
        primary: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
        surface: 'linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%)'
      }
    },
    light: {
      bg: { base: '#F8FAFF', elevated: '#FFFFFF', card: '#FFFFFF' },
      glass: {
        bg: 'rgba(255, 255, 255, 0.7)',
        border: 'rgba(255, 255, 255, 0.8)',
        hover: 'rgba(255, 255, 255, 0.9)',
        blur: 'blur(30px) saturate(250%) brightness(1.05)',
        shadow: '0 8px 32px rgba(37, 99, 235, 0.08)',
        shadowHover: '0 15px 45px rgba(37, 99, 235, 0.15), 0 0 25px rgba(59, 130, 246, 0.1)'
      },
      text: { primary: '#0F172A', secondary: '#334155', muted: '#64748B', subtle: '#94A3B8' },
      accent: {
        primary: '#2563EB',
        primaryLight: '#3B82F6',
        primaryGlow: 'rgba(37, 99, 235, 0.2)',
        secondary: '#0891B2',
        success: '#059669',
        warning: '#D97706',
        error: '#DC2626',
      }
    },
  },
  radius: { 
    sm: '12px', 
    md: '16px', 
    lg: '24px', 
    xl: '32px', 
    full: '9999px' 
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    huge: '80px'
  }
}

export const getCSSVariables = (isDark) => {
  const colors = isDark ? DESIGN_TOKENS.colors.dark : DESIGN_TOKENS.colors.light

  return {
    '--bg-base': colors.bg.base,
    '--bg-elevated': colors.bg.elevated,
    '--bg-card': colors.bg.card,
    '--glass-bg': colors.glass.bg,
    '--glass-border': colors.glass.border,
    '--glass-hover': colors.glass.hover,
    '--glass-blur': colors.glass.blur,
    '--glass-shadow': colors.glass.shadow,
    '--shadow-hover': colors.glass.shadowHover,
    '--color-text': colors.text.primary,
    '--color-secondary': colors.text.secondary,
    '--color-muted': colors.text.muted,
    '--color-subtle': colors.text.subtle,
    '--color-primary': colors.accent.primary,
    '--color-primary-light': colors.accent.primaryLight,
    '--color-primary-glow': colors.accent.primaryGlow,
    '--color-accent': colors.accent.secondary,
    '--color-success': colors.accent.success,
    '--color-warning': colors.accent.warning,
    '--color-error': colors.accent.error,
    '--gradient-primary': colors.gradient?.primary || colors.accent.primary,
    '--gradient-surface': colors.gradient?.surface || 'none',
    '--radius-lg': DESIGN_TOKENS.radius.lg,
    '--radius-xl': DESIGN_TOKENS.radius.xl,
  }
}

export const ANIMATIONS = {
  fadeInUp: { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -20 } },
  // ... other animations
}
