import { FloatingToolsBackground } from '../ui/FloatingToolsBackground';

export function GlobalLayout({ children }) {
  return (
    <div className="aparty-global-wrapper">
      <FloatingToolsBackground />

      <div className="aparty-global-content">
        {children}
      </div>
    </div>
  );
}
