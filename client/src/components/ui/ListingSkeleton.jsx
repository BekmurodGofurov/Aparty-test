import React from 'react';
import './Skeleton.scss';

export const ListingSkeleton = () => {
  return (
    <main className="listing-page page skeleton-page">
      <section className="left-col">
        <div className="gallery">
          <div className="skeleton-image" style={{ height: '450px', borderRadius: '24px' }} />
          <div className="thumbs" style={{ marginTop: '1rem', display: 'flex', gap: '10px' }}>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton" style={{ width: '80px', height: '60px', borderRadius: '12px' }} />
            ))}
          </div>
        </div>
        
        <div className="info" style={{ marginTop: '2rem' }}>
          <div className="price-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="skeleton-title" style={{ width: '40%', height: '40px' }} />
            <div className="skeleton" style={{ width: '120px', height: '44px', borderRadius: '12px' }} />
          </div>
          <div className="skeleton-line medium" style={{ marginTop: '1rem' }} />
          <div className="skeleton-line full" />
          <div className="skeleton-line short" />
        </div>

        <div className="amenities-grid" style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px' }}>
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div key={i} className="skeleton" style={{ height: '30px', borderRadius: '8px' }} />
          ))}
        </div>
      </section>

      <aside className="right-col">
        <div className="contact-card glass-card" style={{ padding: '2rem' }}>
          <div className="skeleton-badge" />
          <div className="skeleton-title" style={{ width: '100%', marginBottom: '1rem' }} />
          <div className="skeleton-line short" />
          <div className="skeleton" style={{ height: '50px', width: '100%', borderRadius: '14px', marginBottom: '1rem' }} />
          <div className="skeleton" style={{ height: '50px', width: '100%', borderRadius: '14px' }} />
        </div>
      </aside>
    </main>
  );
};
