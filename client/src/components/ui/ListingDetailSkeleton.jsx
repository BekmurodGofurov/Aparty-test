export function ListingDetailSkeleton() {
  return (
    <main className="listing-page page skeleton-page pointer-events-none select-none" aria-hidden="true">
      <div className="listing-two-col animate-pulse">
        <div className="listing-left">
          <section className="listing-hero-shell">
            <div className="listing-gallery">
              <div className="gallery-main overflow-hidden">
                <div className="absolute inset-0 !bg-gray-200 dark:!bg-slate-800" />
                <div className="gallery-topbar">
                  <div className="hero-chips">
                    <span className="h-8 w-20 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <span className="h-8 w-14 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <span className="h-8 w-16 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                  </div>
                  <div className="hero-actions">
                    <span className="h-9 w-9 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <span className="h-9 w-9 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <span className="h-9 w-9 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                  </div>
                </div>
                <div className="hero-copy left-6 right-6 bottom-6 space-y-4">
                  <span className="block h-5 w-44 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                  <div className="space-y-3">
                    <span className="block h-8 w-[82%] rounded-xl !bg-gray-200 dark:!bg-slate-800" />
                    <span className="block h-5 w-[68%] rounded-xl !bg-gray-200 dark:!bg-slate-800" />
                  </div>
                </div>
              </div>

              <div className="gallery-thumbs">
                <div className="h-full rounded-2xl !bg-gray-200 dark:!bg-slate-800" />
                <div className="h-full rounded-2xl !bg-gray-200 dark:!bg-slate-800" />
              </div>
            </div>
          </section>

          <div className="left-col space-y-5">
            <section className="overview-panel">
              <div className="overview-metrics">
                {Array.from({ length: 4 }).map((_, index) => (
                  <div key={index} className="space-y-2 rounded-2xl !bg-gray-200 px-4 py-4 dark:!bg-slate-800">
                    <span className="block h-4 w-8 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                    <span className="block h-6 w-12 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                    <span className="block h-3 w-14 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                  </div>
                ))}
              </div>

              <div className="address-card rounded-2xl !bg-gray-200 px-5 py-5 dark:!bg-slate-800">
                <div className="h-11 w-11 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <div className="flex-1 space-y-3">
                  <div className="h-5 w-2/3 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                  <div className="h-4 w-full rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                  <div className="h-4 w-1/2 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                </div>
              </div>

              <div className="shared-note rounded-2xl !bg-gray-200 px-5 py-4 dark:!bg-slate-800">
                <div className="h-5 w-5 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <div className="h-4 flex-1 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              </div>
            </section>

            <section className="desc panel-card rounded-3xl !bg-gray-200 px-6 py-6 dark:!bg-slate-800">
              <div className="section-heading space-y-3">
                <span className="block h-3 w-20 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <span className="block h-6 w-44 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              </div>
              <div className="mt-5 space-y-3">
                <span className="block h-4 w-full rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <span className="block h-4 w-[92%] rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <span className="block h-4 w-[78%] rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              </div>
            </section>

            <section className="amenities-panel panel-card rounded-3xl !bg-gray-200 px-6 py-6 dark:!bg-slate-800">
              <div className="section-heading space-y-3">
                <span className="block h-3 w-20 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <span className="block h-6 w-40 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              </div>
              <div className="amenities-grid mt-5">
                {Array.from({ length: 8 }).map((_, index) => (
                  <div key={index} className="space-y-3 rounded-2xl !bg-gray-200 px-4 py-4 dark:!bg-slate-700/70">
                    <span className="block h-5 w-5 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <span className="block h-4 w-20 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <span className="block h-3 w-16 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                  </div>
                ))}
              </div>
            </section>

            <section className="location-section panel-card rounded-3xl !bg-gray-200 px-6 py-6 dark:!bg-slate-800">
              <div className="section-heading space-y-3">
                <span className="block h-3 w-20 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <span className="block h-6 w-36 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              </div>
              <div className="mt-5 h-64 rounded-3xl !bg-gray-200 dark:!bg-slate-700/70" />
            </section>

            <section className="rounded-3xl !bg-gray-200 px-6 py-6 dark:!bg-slate-800">
              <div className="space-y-3">
                <span className="block h-3 w-20 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
                <span className="block h-6 w-40 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              </div>
              <div className="mt-5 space-y-4">
                {Array.from({ length: 3 }).map((_, index) => (
                  <div key={index} className="flex items-center gap-4 rounded-2xl !bg-gray-200 px-4 py-4 dark:!bg-slate-700/70">
                    <span className="h-12 w-12 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    <div className="flex-1 space-y-3">
                      <span className="block h-4 w-1/2 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                      <span className="block h-3 w-[86%] rounded-full !bg-gray-200 dark:!bg-slate-800" />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </div>

        <aside className="right-col">
          <div className="booking-card sticky-booking space-y-5 rounded-[28px] !bg-gray-200 px-6 py-6 dark:!bg-slate-800">
            <div className="space-y-3 border-b border-transparent pb-5">
              <span className="block h-10 w-32 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              <span className="block h-4 w-24 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
            </div>

            <div className="flex items-center gap-4 rounded-2xl !bg-gray-200 px-4 py-4 dark:!bg-slate-700/70">
              <span className="h-12 w-12 rounded-full !bg-gray-200 dark:!bg-slate-800" />
              <div className="flex-1 space-y-3">
                <span className="block h-4 w-28 rounded-full !bg-gray-200 dark:!bg-slate-800" />
                <span className="block h-3 w-36 rounded-full !bg-gray-200 dark:!bg-slate-800" />
              </div>
              <span className="h-5 w-5 rounded-full !bg-gray-200 dark:!bg-slate-800" />
            </div>

            <div className="flex flex-wrap gap-2">
              <span className="h-8 w-16 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              <span className="h-8 w-16 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
              <span className="h-8 w-20 rounded-full !bg-gray-200 dark:!bg-slate-700/70" />
            </div>

            <div className="space-y-3 rounded-2xl !bg-gray-200 px-4 py-4 dark:!bg-slate-700/70">
              <span className="block h-4 w-2/3 rounded-full !bg-gray-200 dark:!bg-slate-800" />
              <span className="block h-4 w-[86%] rounded-full !bg-gray-200 dark:!bg-slate-800" />
            </div>

            <div className="space-y-3">
              <span className="block h-24 rounded-2xl !bg-gray-200 dark:!bg-slate-700/70" />
              <span className="block h-12 rounded-2xl !bg-gray-200 dark:!bg-slate-700/70" />
              <span className="block h-12 rounded-2xl !bg-gray-200 dark:!bg-slate-700/70" />
            </div>
          </div>
        </aside>
      </div>
    </main>
  )
}