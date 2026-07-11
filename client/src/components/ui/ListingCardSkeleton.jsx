export function ListingCardSkeleton() {
  return (
    <article className="listing-card-liquid pointer-events-none select-none animate-pulse" aria-hidden="true">
      <div className="card-hit-area">
        <div className="card-media relative overflow-hidden">
          <div className="absolute inset-0 bg-gray-200 dark:bg-slate-800" />
          <div className="media-vignette opacity-40" />
          <div className="media-top">
            <div className="h-7 w-20 rounded-full bg-gray-200 dark:bg-slate-800" />
            <div className="h-9 w-9 rounded-full bg-gray-200 dark:bg-slate-800" />
          </div>
          <div className="price-glass">
            <div className="h-5 w-16 rounded bg-gray-200 dark:bg-slate-800" />
            <div className="mt-2 h-3 w-10 rounded bg-gray-200 dark:bg-slate-800" />
          </div>
        </div>

        <div className="card-body">
          <div className="location-row">
            <span className="location-icon !bg-gray-200 !text-transparent dark:!bg-slate-800" />
            <span className="h-3.5 flex-1 rounded-full bg-gray-200 dark:bg-slate-800" />
            <span className="rating-pill h-6 w-14 !bg-gray-200 !text-transparent dark:!bg-slate-800" />
          </div>

          <div className="title-row">
            <div className="h-5 w-[88%] rounded-md bg-gray-200 dark:bg-slate-800" />
            <div className="mt-2 h-5 w-[72%] rounded-md bg-gray-200 dark:bg-slate-800" />
          </div>

          <div className="metrics-row">
            <div className="h-8 rounded-xl bg-gray-200 dark:bg-slate-800" />
            <div className="h-8 rounded-xl bg-gray-200 dark:bg-slate-800" />
            <div className="h-8 rounded-xl bg-gray-200 dark:bg-slate-800" />
          </div>

          <div className="amenity-strip">
            <span className="!bg-gray-200 dark:!bg-slate-800" />
            <span className="!bg-gray-200 dark:!bg-slate-800" />
            <span className="!bg-gray-200 dark:!bg-slate-800" />
            <span className="!bg-gray-200 dark:!bg-slate-800" />
          </div>

          <div className="card-footer">
            <div className="owner-cluster flex items-center gap-3">
              <span className="h-10 w-10 rounded-full bg-gray-200 dark:bg-slate-800" />
              <span className="flex flex-col gap-2">
                <span className="h-4 w-24 rounded-full bg-gray-200 dark:bg-slate-800" />
                <span className="h-3 w-16 rounded-full bg-gray-200 dark:bg-slate-800" />
              </span>
            </div>
            <span className="verified-mark h-8 w-8 rounded-full !bg-gray-200 dark:!bg-slate-800" />
          </div>

          <div className="card-contact-actions">
            <span className="h-9 rounded-xl bg-gray-200 dark:bg-slate-800" />
            <span className="h-9 rounded-xl bg-gray-200 dark:bg-slate-800" />
          </div>
        </div>
      </div>
    </article>
  )
}