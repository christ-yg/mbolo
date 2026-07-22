/**
 * Structure commune des pages Mbolo.
 *
 * Outlet représente la page correspondant à la route courante.
 */

import { Outlet } from "react-router-dom";

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
      </div>
    </NotificationProvider>
  );
}
