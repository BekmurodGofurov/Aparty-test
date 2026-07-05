import React, { useMemo } from 'react'
import { 
  Hammer, Settings, Wrench, Ruler, Paintbrush, Scissors, 
  Rocket, Shield, Zap, Home, Sparkles, Briefcase, Bot, Layout, 
  Compass, Layers, Box, Fingerprint
} from 'lucide-react'
import './FloatingToolsBackground.scss'

const ICONS = [
  Hammer, Settings, Wrench, Ruler, Paintbrush, Scissors, 
  Rocket, Shield, Zap, Home, Sparkles, Briefcase, Bot, Layout,
  Compass, Layers, Box, Fingerprint
]

export function FloatingToolsBackground() {
  const icons = useMemo(() => {
    const placements = [
      [5, 14, 24, -2.4, 0.74, 0.65],
      [14, 38, 32, 2.8, 0.98, 0.95],
      [8, 70, 22, 2.2, 0.7, 0.7],
      [22, 88, 26, -2.8, 0.76, 0.82],
      [26, 22, 28, -2.1, 0.78, 0.76],
      [34, 54, 36, 3, 1, 1],
      [42, 10, 20, -2.6, 0.58, 0.55],
      [46, 78, 30, 2.4, 0.82, 0.9],
      [56, 32, 23, -2, 0.66, 0.62],
      [62, 92, 22, 2.8, 0.56, 0.5],
      [68, 60, 33, -2.5, 0.92, 0.92],
      [73, 16, 34, 2.7, 0.86, 0.86],
      [80, 78, 21, -2.3, 0.62, 0.58],
      [86, 34, 32, 2.5, 0.9, 0.9],
      [93, 58, 24, -2.7, 0.68, 0.65],
      [96, 88, 20, 2.1, 0.5, 0.48],
      [18, 8, 18, 2.3, 0.5, 0.45],
      [38, 94, 18, -2.2, 0.48, 0.44],
      [52, 52, 19, 2.8, 0.5, 0.5],
      [92, 8, 18, -2.4, 0.48, 0.42],
    ]

    return placements.map(([left, top, size, rotate, opacityMod, depth], i) => ({
      id: `icon-${i}`,
      Icon: ICONS[i % ICONS.length],
      size,
      top: `${top}%`,
      left: `${left}%`,
      rotateAmt: rotate,
      blur: depth < 0.55 ? 1.1 : depth < 0.75 ? 0.45 : 0,
      opacityMod,
      depth,
    }))
  }, [])

  const particles = useMemo(() => {
    return Array.from({ length: 22 }).map((_, i) => ({
      id: `particle-${i}`,
      size: (i % 3) + 1,
      top: `${8 + ((i * 19) % 88)}%`,
      left: `${6 + ((i * 23) % 88)}%`,
    }))
  }, [])

  return (
    <div className="premium-saas-bg" aria-hidden="true">
      {/* Noise Texture for depth */}
      <div className="noise-overlay" />

      {/* Background radial glows will be handled in SCSS */}

      {/* Layer 1: Parallax Icons with Depth */}
      <div className="bg-layer icons-layer">
        {icons.map((item) => (
          <div
            key={item.id}
            className="floating-icon-wrapper"
            style={{ 
              top: item.top, 
              left: item.left,
              position: 'absolute',
              filter: `blur(${item.blur}px)`,
              pointerEvents: 'none',
              transform: `rotate(${item.rotateAmt}deg) scale(${0.96 + item.depth * 0.08})`,
            }}
          >
            {/* The icon styling handles opacity via CSS variable */}
            <item.Icon 
              className="floating-icon" 
              size={item.size} 
              strokeWidth={1.2} 
              style={{ '--opacity-mod': item.opacityMod }} 
            />
          </div>
        ))}
      </div>

      {/* Layer 2: Glowing Particles */}
      <div className="bg-layer particles-layer">
        {particles.map((p) => (
          <div
            key={p.id}
            className="floating-particle"
            style={{
              top: p.top,
              left: p.left,
              width: p.size,
              height: p.size,
            }}
          />
        ))}
      </div>
    </div>
  )
}
