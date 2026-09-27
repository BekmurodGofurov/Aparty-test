import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Mail, Phone, MapPin } from 'lucide-react';
import './Footer.scss';

const CONTACTS = [
  { Icon: Phone, value: import.meta.env.VITE_CONTACT_PHONE },
  { Icon: Mail, value: import.meta.env.VITE_CONTACT_EMAIL },
  { Icon: MapPin, value: import.meta.env.VITE_CONTACT_ADDRESS },
].filter(({ value }) => value)

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
            </p>          </div>

          {/* Quick Links */}
          <div className="footer-links">
            <h4>{t('footer.quick_links')}</h4>
            <ul>
              <li><Link to="/search">Uylarni qidirish</Link></li>
              <li><Link to="/search?owner_role=student">Sherik izlayotganlar</Link></li>
              <li><Link to="/login">E'lon berish</Link></li>
            </ul>
          </div>

          {/* Categories */}
          <div className="footer-links">
            <h4>Kategoriyalar</h4>
            <ul>
              <li><Link to="/search?rental_type=full_unit">Butun kvartiralar</Link></li>
              <li><Link to="/search?rental_type=shared_room">Xonalar</Link></li>
            </ul>
          </div>

          {/* Contact Info: shown only for the details configured in the environment */}
          {CONTACTS.length > 0 && (
            <div className="footer-contact">
              <h4>{t('footer.contact')}</h4>
              {CONTACTS.map(({ Icon, value }) => (
                <div className="contact-item" key={value}>
                  <Icon size={18} />
                  <span>{value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="footer-bottom">
          <p>&copy; {new Date().getFullYear()} Aparty.uz. Barcha huquqlar himoyalangan.</p>
        </div>
      </div>
    </footer>
  );
}
