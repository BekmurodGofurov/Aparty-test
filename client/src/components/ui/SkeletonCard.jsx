import './Skeleton.scss'

export const SkeletonCard = () => (
  <div className="skeleton-card">
    <div className="skeleton-image" />
    <div className="skeleton-body">
      <div className="skeleton-badge" />
      <div className="skeleton-title" />
      <div className="skeleton-line full" />
      <div className="skeleton-line medium" />
      <div className="skeleton-line short" />
    </div>
  </div>
)
