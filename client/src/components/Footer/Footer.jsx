import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, Phone, MapPin, Send } from 'lucide-react';
import './Footer.scss';

const InstagramIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="20" height="20" x="2" y="2" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" x2="17.51" y1="6.5" y2="6.5"></line></svg>
);

const FacebookIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>
);

const TwitterIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"></path></svg>
);

export function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="footer">
      <div className="footer-glow" />
      <div className="footer-inner page">
        <div className="footer-grid">
          {/* Brand Section */}
          <div className="footer-brand">
            <Link to="/" className="brand">
              Aparty<span>.uz</span>
            </Link>
            <p className="brand-desc">
              Andijondagi eng ishonchli va zamonaviy ijara platformasi. Talabalar va yosh oilalar uchun eng yaxshi variantlar.
            </p>
            <div className="social-links">
              <a href="#" className="social-btn"><InstagramIcon /></a>
              <a href="#" className="social-btn"><FacebookIcon /></a>
              <a href="#" className="social-btn"><TwitterIcon /></a>
              <a href="#" className="social-btn"><Send size={20} /></a>
            </div>
          </div>

          {/* Quick Links */}
          <div className="footer-links">
            <h4>{t('footer.quick_links')}</h4>
            <ul>
              <li><Link to="/search">Uylarni qidirish</Link></li>
              <li><Link to="/search?student=true">Talabalar uchun</Link></li>
              <li><Link to="/register">E'lon berish</Link></li>
              <li><Link to="/help">Yordam markazi</Link></li>
            </ul>
          </div>

          {/* Categories */}
          <div className="footer-links">
            <h4>Kategoriyalar</h4>
            <ul>
              <li><Link to="/search?type=apartment">Kvartiralar</Link></li>
              <li><Link to="/search?type=house">Hovli uylar</Link></li>
              <li><Link to="/search?type=room">Xonalar</Link></li>
              <li><Link to="/search?type=dorm">Yotoqxonalar</Link></li>
            </ul>
          </div>

          {/* Contact Info */}
          <div className="footer-contact">
            <h4>{t('footer.contact')}</h4>
            <div className="contact-item">
              <Phone size={18} />
              <span>+998 90 123 45 67</span>
            </div>
            <div className="contact-item">
              <Mail size={18} />
              <span>info@aparty.uz</span>
            </div>
            <div className="contact-item">
              <MapPin size={18} />
              <span>Andijon sh., Navoiy shoh ko'chasi</span>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} Aparty.uz. Barcha huquqlar himoyalangan.</p>
          <div className="bottom-links">
            <Link to="/privacy">Maxfiylik siyosati</Link>
            <Link to="/terms">Foydalanish shartlari</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
