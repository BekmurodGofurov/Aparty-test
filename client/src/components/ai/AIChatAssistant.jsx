import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useLocation } from 'react-router-dom';
import { ChefHat, Droplets, Flame, Home, MapPin, Maximize2, MessageSquare, Minimize2, Refrigerator, Send, Snowflake, Sparkles, Tv, User, WashingMachine, Wifi, X } from 'lucide-react';
import { api } from '../../services/api';
import './AIChatAssistant.scss';

export const AIChatAssistant = () => {
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: "Salom! Qanday uy qidiryapsiz? Hudud, budjet va xonalar sonini yozing.", sender: 'ai' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages, isTyping]);
  
  // Listen for global open events
  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener('open-ai-chat', handleOpen);
    return () => window.removeEventListener('open-ai-chat', handleOpen);
  }, []);

  const closeChat = () => {
    setIsOpen(false);
    setIsExpanded(false);
  };

  const getAmenityIcon = (amenity) => {
    if (amenity === 'wifi') return <Wifi size={12} />;
    if (amenity === 'ac') return <Snowflake size={12} />;
    if (amenity === 'gas') return <Flame size={12} />;
    if (amenity === 'water') return <Droplets size={12} />;
    if (amenity === 'washer') return <WashingMachine size={12} />;
    if (amenity === 'fridge') return <Refrigerator size={12} />;
    if (amenity === 'kitchenware') return <ChefHat size={12} />;
    if (amenity === 'tv') return <Tv size={12} />;
    return <Home size={12} />;
  };

  const handleSend = async (text) => {
    const userText = text || input;
    if (!userText.trim()) return;

    // Add user message
    const newUserMsg = { id: Date.now(), text: userText, sender: 'user' };
    setMessages(prev => [...prev, newUserMsg]);
    setInput('');
    setIsTyping(true);

    try {
      // Prepare history for Gemini format if needed
      // Gemini expects: { role: 'user'|'model', parts: [{ text: '...' }] }
      const history = messages.slice(1).map(m => ({
        role: m.sender === 'ai' ? 'model' : 'user',
        parts: [{ text: m.text }]
      }));

      const { data } = await api.post('/ai/chat', {
        message: userText,
        history: history
      });

      if (data.success) {
        setMessages(prev => [
          ...prev,
          {
            id: Date.now() + 1,
            text: data.response,
            sender: 'ai',
            listings: Array.isArray(data.listings) ? data.listings : [],
          }
        ]);
      } else {
        const errorMsg = typeof data.error === 'string' 
          ? data.error 
          : "Kechirasiz, xatolik yuz berdi."
        setMessages(prev => [...prev, { id: Date.now() + 1, text: errorMsg, sender: 'ai' }]);
      }
    } catch (error) {
      console.error('AI Chat error:', error);
      
      // Extract error message properly
      let errorText = "Server bilan bog'lanishda xatolik."
      if (error?.response?.data?.detail) {
        const detail = error.response.data.detail
        if (Array.isArray(detail)) {
          errorText = detail[0]?.msg || detail[0] || errorText
        } else if (typeof detail === 'string') {
          errorText = detail
        }
      }
      
      setMessages(prev => [...prev, { id: Date.now() + 1, text: errorText, sender: 'ai' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="ai-chat-wrapper">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className={`ai-chat-window liquid-glass ${isExpanded ? 'expanded' : ''}`}
          >
            <div className="chat-header">
              <div className="header-info">
                <div className="avatar-wrapper">
                  <div className="avatar">
                    <Sparkles size={18} />
                  </div>
                  <span className="status-dot"></span>
                </div>
                <div>
                  <h3>Aparty AI</h3>
                  <p>Onlayn - yordam berishga tayyor</p>
                </div>
              </div>
              <div className="chat-window-actions">
                <button
                  onClick={() => setIsExpanded((value) => !value)}
                  className="window-action-btn"
                  aria-label={isExpanded ? 'Kichik oynaga qaytarish' : "To'liq oynada ochish"}
                  title={isExpanded ? 'Kichik oynaga qaytarish' : "To'liq oynada ochish"}
                >
                  {isExpanded ? <Minimize2 size={19} /> : <Maximize2 size={19} />}
                </button>
                <button onClick={closeChat} className="window-action-btn close-btn" aria-label="Chatni yopish" title="Chatni yopish">
                  <X size={20} />
                </button>
              </div>
            </div>

            <div className="chat-messages">
              {messages.map(msg => (
                <div key={msg.id} className={`message-row ${msg.sender} ${msg.listings?.length ? 'has-listings-row' : ''}`}>
                  <div className="avatar">
                    {msg.sender === 'ai' ? <Sparkles size={16} /> : <User size={16} />}
                  </div>
                  <div className={`message-bubble ${msg.listings?.length ? 'has-listings' : ''}`}>
                    <div>{msg.text}</div>
                    {msg.listings?.length > 0 && (
                      <div className="ai-listing-cards">
                        {msg.listings.map((listing) => (
                          <Link
                            to={listing.url || `/listing/${listing.id}`}
                            className="ai-listing-card"
                            key={listing.id}
                            onClick={closeChat}
                          >
                            <div className="listing-card-top">
                              <span className="listing-price">{listing.price}</span>
                              <span className="listing-rooms">{listing.rooms} xona</span>
                            </div>
                            <div className="listing-address">
                              <MapPin size={13} />
                              <span>{listing.address}</span>
                            </div>
                            {(listing.distance_text || listing.available_spaces) && (
                              <div className="listing-match-meta">
                                {listing.distance_text && <span>{listing.distance_text}</span>}
                                {listing.available_spaces > 0 && <span>{listing.available_spaces} ta bo'sh joy</span>}
                              </div>
                            )}
                            {listing.description && (
                              <p className="listing-description">{listing.description}</p>
                            )}
                            {listing.amenities?.length > 0 && (
                              <div className="listing-amenities">
                                {listing.amenities.slice(0, 4).map((amenity) => (
                                  <span key={amenity}>
                                    {getAmenityIcon(amenity)}
                                    {amenity === 'ac' ? 'AC' : amenity}
                                  </span>
                                ))}
                              </div>
                            )}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div className="message-row ai">
                  <div className="avatar"><Sparkles size={16} /></div>
                  <div className="message-bubble typing-indicator">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="quick-prompts">
              <button onClick={() => handleSend("300$ gacha kvartira")}>300$ gacha</button>
              <button onClick={() => handleSend("Universitetga yaqin")}>Universitetga yaqin</button>
              <button onClick={() => handleSend("Roommate kerak")}>Roommate kerak</button>
            </div>

            <div className="chat-input-area">
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Xabaringizni yozing..." 
              />
              <button onClick={() => handleSend()} disabled={!input.trim()} className="send-btn">
                <Send size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!isOpen && (
        <motion.button
          className="chat-toggle-btn"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setIsOpen(true)}
        >
          {document.documentElement.getAttribute('data-theme') === 'light' ? <Sparkles size={24} /> : <MessageSquare size={24} />}
          <span className="btn-label">AI Yordamchi</span>
          <div className="btn-glow-effect"></div>
        </motion.button>
      )}
    </div>
  );
};
