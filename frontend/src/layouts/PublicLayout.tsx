/** Structure commune de toutes les pages publiques et privées. */

import { Link, Outlet } from "react-router-dom";

import { RealtimeNotificationToast } from
  "../components/notifications/RealtimeNotificationToast";
import { PublicHeader } from "../components/navigation/PublicHeader";
import { NotificationProvider } from "../context/NotificationContext";

export function PublicLayout() {
  return (
    <NotificationProvider>
      <div className="public-layout">
        <PublicHeader />
        <RealtimeNotificationToast />
        <Outlet />

        <footer className="public-footer">
          <p>© 2026 Mbolo · Rencontres adultes, respectueuses et sécurisées.</p>
          <nav aria-label="Informations Mbolo">
            <Link to="/about">À propos</Link>
            <Link to="/how-it-works">Comment ça marche</Link>
            <Link to="/help">Aide</Link>
            <Link to="/contact">Contact</Link>
            <Link to="/accessibility">Accessibilité</Link>
            <Link to="/legal/notice">Mentions légales</Link>
            <Link to="/legal/terms">Conditions</Link>
            <Link to="/legal/privacy">Confidentialité</Link>
            <Link to="/legal/cookies">Cookies</Link>
            <Link to="/legal/community">Communauté</Link>
          </nav>
        </footer>
      </div>
    </NotificationProvider>
  );
}
