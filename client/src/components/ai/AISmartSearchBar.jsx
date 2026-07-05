import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './AISmartSearchBar.scss';

export const AISmartSearchBar = () => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const navigate = useNavigate();

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      // TODO: Connect to backend API
      // await new Promise(r => setTimeout(r, 1500)); // Simulate network request for now
      
      // For now we will mock the parsing:
      setTimeout(() => {
        setIsSearching(false);
        // Let's redirect to search with a generic search param
        navigate(`/search?q=${encodeURIComponent(query)}`);
      }, 1500);

    } catch (error) {
      console.error("AI Search Error:", error);
      setIsSearching(false);
    }
  };

  const handleSuggestion = (text) => {
    setQuery(text);
  };

  return (
    <div className="ai-smart-search">
      <form onSubmit={handleSearch} className="ai-search-form">
        <div className="icon-left">
          <motion.div
            animate={{ rotate: isSearching ? 360 : 0, scale: isSearching ? 1.2 : 1 }}
            transition={{ duration: 2, repeat: isSearching ? Infinity : 0, ease: "linear" }}
          >
            <Sparkles size={24} className="sparkle-icon" />
          </motion.div>
        </div>
        
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="O'zingizga kerakli uyni ta'riflang (masalan: Chilonzorda 300$ gacha...)"
          className="search-input"
          disabled={isSearching}
        />
        
        <button
          type="submit"
          disabled={isSearching || !query.trim()}
          className="search-btn"
        >
          <AnimatePresence mode="wait">
            {isSearching ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.5 }}
                className="loading-spinner"
              />
            ) : (
              <motion.div
                key="search"
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.5 }}
              >
                <Search size={20} />
              </motion.div>
            )}
          </AnimatePresence>
        </button>
      </form>
      
      <div className="search-suggestions">
        <span>Sinab ko'ring:</span>
        <button type="button" onClick={() => handleSuggestion("Talabalar uchun yotoqxona, arzon narxda")}>
          "Talabalar uchun yotoqxona, arzon narxda"
        </button>
        <button type="button" onClick={() => handleSuggestion("Metroga yaqin, 400$ gacha kvartira")}>
          "Metroga yaqin, 400$ gacha kvartira"
        </button>
      </div>
    </div>
  );
};
