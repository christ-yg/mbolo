
/**
 * Toast global pour les messages, likes et nouveaux matchs.
 */

import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

import {
  useNotification,
} from "../../context/NotificationContext";


function getInitial(displayName: string): string {
  return (
    displayName.trim().charAt(0).toUpperCase() ||
    "M"
  );
}


function getKindLabel(
  kind: "message" | "like" | "match",
): string {
  switch (kind) {
    case "message":
      return "Nouveau message";
    case "like":
      return "Nouveau like";
    case "match":
      return "Nouveau match";
  }
}


export function RealtimeNotificationToast() {
  const navigate = useNavigate();

  const {
    notification,
    dismissNotification,
  } = useNotification();

  const openDestination =
    useCallback((): void => {
      if (notification === null) {
        return;
      }

      dismissNotification();
      navigate(notification.targetPath);
    }, [
      dismissNotification,
      navigate,
      notification,
    ]);

  if (notification === null) {
    return null;
  }

  return (
    <aside
      className={
        "realtime-notification " +
        `realtime-notification--${notification.kind}`
      }
      role="status"
      aria-live="polite"
      aria-label={notification.title}
    >
      <button
        type="button"
        className="realtime-notification__content"
        onClick={openDestination}
      >
        <span
          className="realtime-notification__avatar"
          aria-hidden="true"
        >
          {getInitial(notification.displayName)}
        </span>

        <span className="realtime-notification__text">
          <strong>
            {getKindLabel(notification.kind)}
          </strong>

          <span>{notification.title}</span>

          {notification.body ? (
            <small>{notification.body}</small>
          ) : null}
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
