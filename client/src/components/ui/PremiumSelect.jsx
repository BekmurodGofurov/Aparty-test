import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './PremiumSelect.scss';

export function PremiumSelect({ value, onChange, options, placeholder, disabled }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (val) => {
    onChange(val);
    setIsOpen(false);
  };

  const selectedOption = options.find(opt => opt.value === value) || options.find(opt => opt === value);
  const displayValue = selectedOption?.label || selectedOption || placeholder;

  return (
    <div className={`premium-select-container ${disabled ? 'disabled' : ''}`} ref={containerRef}>
      <button 
        type="button"
        className={`select-trigger ${isOpen ? 'active' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
      >
        <span className="current-value">{displayValue}</span>
        <ChevronDown size={16} className={`chevron ${isOpen ? 'rotated' : ''}`} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            className="select-menu"
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="menu-inner">
              {options.map((opt, index) => {
                const val = opt.value !== undefined ? opt.value : opt;
                const lab = opt.label !== undefined ? opt.label : opt;
                const isSelected = val === value;

                return (
                  <button
                    key={index}
                    type="button"
                    className={`select-option ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelect(val)}
                  >
                    {lab}
                    {isSelected && <motion.div layoutId="active-bg" className="active-indicator" />}
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
