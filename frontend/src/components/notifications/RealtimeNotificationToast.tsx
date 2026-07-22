/** Notification globale reçue depuis le canal WebSocket du compte. */

import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

import { useNotification } from "../../context/NotificationContext";

function getInitial(displayName: string): string {
  return displayName.trim().charAt(0).toUpperCase() || "M";
}

export function RealtimeNotificationToast() {
  const navigate = useNavigate();
  const { notification, dismissNotification } = useNotification();

  const openConversation = useCallback(() => {
    if (notification === null) {
      return;
    }

    const conversationPath =
      `/messages/${encodeURIComponent(notification.conversationId)}`;

    dismissNotification();
    navigate(conversationPath);
  }, [dismissNotification, navigate, notification]);

  if (notification === null) {
    return null;
  }

  return (
    <aside
      className="realtime-notification"
      role="status"
      aria-live="polite"
      aria-label={`Nouveau message de ${notification.senderDisplayName}`}
    >
      <button
        type="button"
        className="realtime-notification__content"
        onClick={openConversation}
      >
        <span
          className="realtime-notification__avatar"
          aria-hidden="true"
        >
          {getInitial(notification.senderDisplayName)}
        </span>

        <span className="realtime-notification__text">
          <strong>{notification.senderDisplayName}</strong>
          <span>t’a envoyé un message</span>
          <small>{notification.bodyPreview}</small>
        </span>

        <span
          className="realtime-notification__arrow"
          aria-hidden="true"
        >
          →
        </span>
      </button>

      <button
        type="button"
        className="realtime-notification__close"
        aria-label="Fermer la notification"
        onClick={dismissNotification}
      >
        ×
      </button>
    </aside>
  );
}
