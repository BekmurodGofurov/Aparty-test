import { Component } from 'react'

// Catches a page that fails to render — most commonly a lazy-loaded page whose JS chunk failed to
// download (a slow or dropped connection, or a new deploy invalidating a chunk a tab still has
// open). Without this, an error anywhere below here would unmount the whole app to a blank page,
// including the navbar; with it, only this page's area shows a retry and everything else survives.
export class RouteErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
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
        style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem',
          padding: '4rem 1.5rem', textAlign: 'center', color: 'var(--color-text)',
        }}
      >
        <p style={{ color: 'var(--color-muted)', maxWidth: '32rem' }}>
          Sahifani ochib bo'lmadi. Internet aloqasi uzilgan yoki sahifa yangilangan bo'lishi mumkin.
        </p>
        <button
          type="button"
          onClick={() => window.location.reload()}
          style={{
            padding: '0.6rem 1.5rem', borderRadius: '999px', border: '1px solid var(--color-border)',
            background: 'var(--color-primary)', color: '#fff', fontWeight: 700, cursor: 'pointer',
          }}
        >
          Qayta yuklash
        </button>
      </div>
    )
  }
}
