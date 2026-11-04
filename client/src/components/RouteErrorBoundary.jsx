import { Component } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, RotateCcw, Home } from 'lucide-react'

// Catches a page that fails to render — most commonly a lazy-loaded page whose JS chunk failed to
// download (a slow or dropped connection, or a new deploy invalidating a chunk a tab still has
// open) or an unexpected runtime error. Without this, an error anywhere below here would unmount
// the whole app to a blank page, including the navbar; with it, only this page's area shows a
// retry and everything else survives.
export class RouteErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Route render error caught by RouteErrorBoundary:', error, errorInfo)
  }

  componentDidUpdate(prevProps) {
    // A fresh navigation (a different route) deserves a fresh attempt, without needing a reload.
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div
        className="route-error-boundary"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: 'calc(80vh - 100px)',
          // Generous top padding ensures this is never covered by the floating header/navbar (height 64px + top 14px)
          padding: 'clamp(110px, 14vh, 160px) 1.5rem 5rem',
          textAlign: 'center',
          color: 'var(--color-text)',
        }}
      >
        <div
          style={{
            maxWidth: '460px',
            width: '100%',
            padding: '2.25rem 2rem',
            borderRadius: '24px',
            background: 'var(--ui-surface, rgba(17, 24, 39, 0.85))',
            border: '1px solid var(--color-border)',
            boxShadow: '0 20px 45px rgba(0, 0, 0, 0.25)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1.1rem',
          }}
        >
          <div
            style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ef4444',
            }}
          >
            <AlertCircle size={28} />
          </div>

          <h2
            style={{
              fontSize: '1.25rem',
              fontWeight: 700,
              margin: '0.2rem 0 0',
              color: 'var(--color-text)',
            }}
          >
            Sahifani ochib bo'lmadi
          </h2>

          <p
            style={{
              color: 'var(--color-muted)',
              fontSize: '0.92rem',
              lineHeight: 1.55,
              margin: 0,
            }}
          >
            Internet aloqasi uzilgan yoki sahifa yangilangan bo'lishi mumkin. Qaytadan urinib ko'ring yoki bosh sahifaga qayting.
          </p>

          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.75rem',
              marginTop: '0.5rem',
              width: '100%',
            }}
          >
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.4rem',
                borderRadius: '999px',
                border: '1px solid var(--color-border)',
                background: 'var(--color-primary)',
                color: '#fff',
                fontSize: '0.9rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              <RotateCcw size={16} />
              Qayta yuklash
            </button>

            <Link
              to="/"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.4rem',
                borderRadius: '999px',
                border: '1px solid var(--color-border)',
                background: 'transparent',
                color: 'var(--color-text)',
                fontSize: '0.9rem',
                fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              <Home size={16} />
              Bosh sahifa
            </Link>
          </div>
        </div>
      </div>
    )
  }
}
