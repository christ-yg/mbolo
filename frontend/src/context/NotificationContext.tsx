
/**
 * Contexte global des notifications temps réel Mbolo.
 *
 * Il reçoit trois familles d'événements :
 *
 * - message.notification ;
 * - like.notification ;
 * - match.notification.
 *
 * Le toast interne peut afficher un aperçu autorisé.
 * La notification native reste plus discrète lorsque l'application
 * est en arrière-plan.
 */

import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAccountRealtime } from "../hooks/useAccountRealtime";


export interface RealtimeNotification {
  id: string;
  kind: "message" | "like" | "match";
  title: string;
  body: string;
  targetPath: string;
  displayName: string;
  createdAt: string;
}


export type BrowserNotificationPermission =
  | NotificationPermission
  | "unsupported";


interface NotificationContextValue {
  notification: RealtimeNotification | null;
  dismissNotification: () => void;
  browserNotificationsSupported: boolean;
  browserNotificationPermission:
    BrowserNotificationPermission;
  browserNotificationsEnabled: boolean;
  enableBrowserNotifications: () => Promise<boolean>;
  disableBrowserNotifications: () => void;
}


const NotificationContext =
  createContext<NotificationContextValue | undefined>(
    undefined,
  );


const MAX_SEEN_NOTIFICATION_IDS = 200;
const BROWSER_NOTIFICATION_PREFERENCE_KEY =
  "mbolo.browserNotifications.enabled";


function isNotificationApiSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "Notification" in window
  );
}


function readStoredBrowserNotificationPreference():
boolean {
  if (typeof window === "undefined") {
    return false;
  }

  try {
    return (
      window.localStorage.getItem(
        BROWSER_NOTIFICATION_PREFERENCE_KEY,
      ) === "true"
    );
  } catch {
    return false;
  }
}


function storeBrowserNotificationPreference(
  enabled: boolean,
): void {
  try {
    if (enabled) {
      window.localStorage.setItem(
        BROWSER_NOTIFICATION_PREFERENCE_KEY,
        "true",
      );
    } else {
      window.localStorage.removeItem(
        BROWSER_NOTIFICATION_PREFERENCE_KEY,
      );
    }
  } catch {
    // La préférence reste valable pour la session courante.
  }
}


function readString(
  value: unknown,
): string | null {
  return (
    typeof value === "string" &&
    value.trim().length > 0
  )
    ? value.trim()
    : null;
}


function readEmbeddedNotification(
  event: Record<string, unknown>,
): Record<string, unknown> | null {
  const notification = event.notification;

  if (
    typeof notification !== "object" ||
    notification === null ||
    Array.isArray(notification)
  ) {
    return null;
  }

  return notification as Record<string, unknown>;
}


function normalizeRealtimeNotification(
  event: Record<string, unknown>,
): RealtimeNotification | null {
  const eventName = readString(event.event);

  if (
    eventName !== "message.notification" &&
    eventName !== "like.notification" &&
    eventName !== "match.notification"
  ) {
    return null;
  }

  const embedded =
    readEmbeddedNotification(event);

  const notificationId =
    readString(embedded?.id) ??
    readString(event.message_id);

  const title =
    readString(embedded?.title);

  const body =
    readString(embedded?.body) ??
    readString(event.body_preview) ??
    "";

  const targetPath =
    readString(embedded?.target_path);

  const createdAt =
    readString(embedded?.created_at) ??
    readString(event.created_at) ??
    new Date().toISOString();

  if (
    notificationId === null ||
    title === null ||
    targetPath === null ||
    !targetPath.startsWith("/")
  ) {
    return null;
  }

  const kind =
    eventName === "message.notification"
      ? "message"
      : eventName === "like.notification"
        ? "like"
        : "match";

  const senderDisplayName =
    readString(event.sender_display_name);

  const otherDisplayName =
    readString(event.other_display_name);

  const displayName =
    senderDisplayName ??
    otherDisplayName ??
    (kind === "like" ? "Mbolo" : "Nouveau match");

  return {
    id: notificationId,
    kind,
    title,
    body,
    targetPath,
    displayName,
    createdAt,
  };
}


function getCurrentBrowserPermission():
BrowserNotificationPermission {
  if (!isNotificationApiSupported()) {
    return "unsupported";
  }

  return window.Notification.permission;
}


export function NotificationProvider({
  children,
}: PropsWithChildren) {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    lastEvent,
    revision,
  } = useAccountRealtime();

  const [notification, setNotification] =
    useState<RealtimeNotification | null>(null);

  const [
    browserNotificationPermission,
    setBrowserNotificationPermission,
  ] = useState<BrowserNotificationPermission>(
    getCurrentBrowserPermission,
  );

  const [
    browserNotificationPreference,
    setBrowserNotificationPreference,
  ] = useState<boolean>(
    readStoredBrowserNotificationPreference,
  );

  const seenIdsReference =
    useRef(new Set<string>());

  const seenOrderReference =
    useRef<string[]>([]);

  const browserNotificationsSupported =
    browserNotificationPermission !== "unsupported";

  const browserNotificationsEnabled =
    browserNotificationsSupported &&
    browserNotificationPermission === "granted" &&
    browserNotificationPreference;

  const dismissNotification =
    useCallback((): void => {
      setNotification(null);
    }, []);

  const enableBrowserNotifications =
    useCallback(async (): Promise<boolean> => {
      if (!isNotificationApiSupported()) {
        setBrowserNotificationPermission(
          "unsupported",
        );
        setBrowserNotificationPreference(false);
        storeBrowserNotificationPreference(false);
        return false;
      }

      try {
        const permission =
          await window.Notification.requestPermission();

        setBrowserNotificationPermission(permission);

        const enabled =
          permission === "granted";

        setBrowserNotificationPreference(enabled);
        storeBrowserNotificationPreference(enabled);

        return enabled;
      } catch {
        setBrowserNotificationPreference(false);
        storeBrowserNotificationPreference(false);
        return false;
      }
    }, []);

  const disableBrowserNotifications =
    useCallback((): void => {
      setBrowserNotificationPreference(false);
      storeBrowserNotificationPreference(false);
    }, []);

  useEffect(() => {
    function synchronizePermission(): void {
      const permission =
        getCurrentBrowserPermission();

      setBrowserNotificationPermission(permission);

      if (
        permission !== "granted" &&
        permission !== "unsupported"
      ) {
        setBrowserNotificationPreference(false);
        storeBrowserNotificationPreference(false);
      }
    }

    window.addEventListener(
      "focus",
      synchronizePermission,
    );

    document.addEventListener(
      "visibilitychange",
      synchronizePermission,
    );

    return () => {
      window.removeEventListener(
        "focus",
        synchronizePermission,
      );

      document.removeEventListener(
        "visibilitychange",
        synchronizePermission,
      );
    };
  }, []);

  useEffect(() => {
    if (lastEvent === null) {
      return;
    }

    const normalizedNotification =
      normalizeRealtimeNotification(lastEvent);

    if (normalizedNotification === null) {
      return;
    }

    if (
      seenIdsReference.current.has(
        normalizedNotification.id,
      )
    ) {
      return;
    }

    seenIdsReference.current.add(
      normalizedNotification.id,
    );

    seenOrderReference.current.push(
      normalizedNotification.id,
    );

    if (
      seenOrderReference.current.length >
      MAX_SEEN_NOTIFICATION_IDS
    ) {
      const oldestId =
        seenOrderReference.current.shift();

      if (oldestId !== undefined) {
        seenIdsReference.current.delete(oldestId);
      }
    }

    /**
     * Si l'utilisateur est déjà sur la destination exacte,
     * le contenu concerné est visible sans toast supplémentaire.
     */
    if (
      location.pathname ===
      normalizedNotification.targetPath
    ) {
      return;
    }

    setNotification(normalizedNotification);

    const applicationIsInBackground =
      document.visibilityState !== "visible" ||
      !document.hasFocus();

    if (
      !browserNotificationsEnabled ||
      !applicationIsInBackground ||
      !isNotificationApiSupported()
    ) {
      return;
    }

    try {
      const nativeNotification =
        new window.Notification(
          "Nouvelle activité sur Mbolo",
          {
            body: normalizedNotification.title,
            tag:
              `mbolo-${normalizedNotification.kind}-` +
              normalizedNotification.id,
            silent: false,
          },
        );

      nativeNotification.onclick = () => {
        window.focus();
        dismissNotification();
        navigate(
          normalizedNotification.targetPath,
        );
        nativeNotification.close();
      };
    } catch {
      // Le toast interne continue même si l'API native échoue.
    }
  }, [
    browserNotificationsEnabled,
    dismissNotification,
    lastEvent,
    location.pathname,
    navigate,
    revision,
  ]);

  useEffect(() => {
    if (notification === null) {
      return undefined;
    }

    const timeoutIdentifier =
      window.setTimeout(() => {
        setNotification(
          (currentNotification) =>
            currentNotification?.id ===
            notification.id
              ? null
              : currentNotification,
        );
      }, 8000);

    return () => {
      window.clearTimeout(timeoutIdentifier);
    };
  }, [notification]);

  const contextValue =
    useMemo<NotificationContextValue>(
      () => ({
        notification,
        dismissNotification,
        browserNotificationsSupported,
        browserNotificationPermission,
        browserNotificationsEnabled,
        enableBrowserNotifications,
        disableBrowserNotifications,
      }),
      [
        browserNotificationPermission,
        browserNotificationsEnabled,
        browserNotificationsSupported,
        disableBrowserNotifications,
        dismissNotification,
        enableBrowserNotifications,
        notification,
      ],
    );

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  );
}


export function useNotification():
NotificationContextValue {
  const context =
    useContext(NotificationContext);

  if (context === undefined) {
    throw new Error(
      "useNotification doit être utilisé dans NotificationProvider.",
    );
  }

  return context;
}
