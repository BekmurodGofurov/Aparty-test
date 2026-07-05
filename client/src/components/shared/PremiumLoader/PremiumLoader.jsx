import React from 'react';
import './PremiumLoader.scss';

const PremiumLoader = ({ text = "Yuklanmoqda...", mini = false, fullscreen = false }) => {
  return (
    <div className={`premium-loader-container ${mini ? 'mini' : ''} ${fullscreen ? 'fullscreen' : ''}`}>
      {fullscreen && <div className="loader-mesh-bg"></div>}
      <div className="loader-visual">
        <div className="loader-glass-orb">
          <div className="loader-ring-outer"></div>
          <div className="loader-ring-inner"></div>
          <div className="loader-core">
            <div className="core-shimmer"></div>
          </div>
        </div>
      </div>
      {!mini && (
        <div className="loader-text-wrapper">
          <span className="loader-text">{text}</span>
          <div className="loader-progress-bar">
            <div className="progress-fill"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PremiumLoader;
