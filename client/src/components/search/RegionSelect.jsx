import { ChevronDown } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import './RegionSelect.scss'

export function RegionSelect({
  regions,
  selectedRegion,
  selectedDistrict,
  onRegionChange,
  onDistrictChange,
  regionPlaceholder = 'Viloyatni tanlang',
  districtPlaceholder = 'Tumanni tanlang',
}) {
  const [regionOpen, setRegionOpen] = useState(false)
  const [districtOpen, setDistrictOpen] = useState(false)
  const regionRef = useRef(null)
  const districtRef = useRef(null)

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (regionRef.current && !regionRef.current.contains(e.target)) setRegionOpen(false)
      if (districtRef.current && !districtRef.current.contains(e.target)) setDistrictOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const districts = selectedRegion ? regions[selectedRegion] || [] : []

  return (
    <div className="region-select-wrapper">
      <div className="region-select" ref={regionRef}>
        <button
          type="button"
          className={`select-trigger ${regionOpen ? 'open' : ''}`}
          onClick={() => setRegionOpen(!regionOpen)}
        >
          <span>{selectedRegion || regionPlaceholder}</span>
          <ChevronDown size={18} />
        </button>
        {regionOpen && (
          <div className="select-dropdown">
            {Object.keys(regions).map((region) => (
              <button
                key={region}
                type="button"
                className={`select-option ${selectedRegion === region ? 'selected' : ''}`}
                onClick={() => {
                  onRegionChange(region)
                  onDistrictChange('') // Reset district
                  setRegionOpen(false)
                }}
              >
                {region}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="region-select" ref={districtRef}>
        <button
          type="button"
          className={`select-trigger ${districtOpen ? 'open' : ''} ${!selectedRegion ? 'disabled' : ''}`}
          onClick={() => selectedRegion && setDistrictOpen(!districtOpen)}
          disabled={!selectedRegion}
        >
          <span>{selectedDistrict || districtPlaceholder}</span>
          <ChevronDown size={18} />
        </button>
        {districtOpen && districts.length > 0 && (
          <div className="select-dropdown">
            {districts.map((district) => (
              <button
                key={district}
                type="button"
                className={`select-option ${selectedDistrict === district ? 'selected' : ''}`}
                onClick={() => {
                  onDistrictChange(district)
                  setDistrictOpen(false)
                }}
              >
                {district}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
