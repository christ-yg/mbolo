/**
 * Structure commune des pages Mbolo.
 *
 * Outlet représente la page correspondant à la route courante.
 */

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
          <nav aria-label="Informations légales">
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
