import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import './EmptyState.scss'

const SUGGESTION_CHIPS = [
  'Chilonzor', 'Sharda yaqinida', '150$ gacha', '2 xonali', 'WiFi bor',
]

export function EmptyState({ icon = '🔍', title, desc, action }) {
  const { t } = useTranslation()

  return (
    <div className="empty-state">
      <div className="empty-glow" />
      <div className="empty-icon-wrap">
        <span className="empty-icon">{icon}</span>
      </div>
      <h3 className="empty-title">{title || t('search.nothing_found')}</h3>
      <p className="empty-desc">{desc || t('search.nothing_found_desc')}</p>

      {action && (
        <button className="button-primary empty-action" onClick={action.onClick} type="button">
          {action.label}
        </button>
      )}

      <div className="empty-chips">
        <p className="chips-label">Mashhur qidiruvlar:</p>
        <div className="chips-row">
          {SUGGESTION_CHIPS.map((chip) => (
            <Link
              key={chip}
              to={`/search?q=${encodeURIComponent(chip)}`}
              className="suggestion-chip"
            >
              {chip}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
