/**
 * Contexte global des notifications Mbolo.
 *
 * Ce contexte gère deux niveaux complémentaires :
 *
 * 1. le toast interne affiché dans l'interface React ;
 * 2. la notification native du navigateur lorsque Mbolo est
 *    en arrière-plan.
 *
 * Les notifications natives restent volontairement
 * respectueuses de la confidentialité :
 *
 * - le texte complet du message n'est jamais affiché ;
 * - seul le nom public de l'expéditeur est utilisé ;
 * - l'utilisateur doit donner son autorisation explicite ;
 * - une préférence locale permet de les désactiver à tout moment.
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

export interface RealtimeMessageNotification {
  id: string;
  conversationId: string;
  messageId: string;
  senderDisplayName: string;
  bodyPreview: string;
  createdAt: string;
}

export type BrowserNotificationPermission =
  | NotificationPermission
  | "unsupported";

interface NotificationContextValue {
  notification: RealtimeMessageNotification | null;
  dismissNotification: () => void;

  /**
   * Indique si l'API Notification existe dans ce navigateur.
   */
  browserNotificationsSupported: boolean;

  /**
   * Autorisation actuellement accordée par le navigateur.
   */
  browserNotificationPermission: BrowserNotificationPermission;

  /**
   * Préférence Mbolo.
   *
   * Elle vaut true uniquement lorsque l'utilisateur a activé
   * la fonctionnalité et que le navigateur a accordé l'autorisation.
   */
  browserNotificationsEnabled: boolean;

  /**
   * Demande l'autorisation au navigateur à la suite
   * d'une action explicite de l'utilisateur.
   */
  enableBrowserNotifications: () => Promise<boolean>;

  /**
   * Désactive les notifications dans Mbolo.
   *
   * Cette action ne peut pas retirer l'autorisation enregistrée
   * dans les paramètres du navigateur.
   */
  disableBrowserNotifications: () => void;
}

const NotificationContext =
  createContext<NotificationContextValue | undefined>(undefined);

const MAX_SEEN_MESSAGE_IDS = 200;
const BROWSER_NOTIFICATION_PREFERENCE_KEY =
  "mbolo.browserNotifications.enabled";

function isNotificationApiSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    "Notification" in window
  );
}

function readStoredBrowserNotificationPreference(): boolean {
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
    /**
     * Certains modes privés ou politiques de navigateur peuvent
     * empêcher l'accès à localStorage.
     */
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
    /**
     * La préférence reste utilisable pour la session courante
     * même si le stockage local n'est pas disponible.
     */
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

function normalizeMessageNotification(
  event: Record<string, unknown>,
): RealtimeMessageNotification | null {
  if (event.event !== "message.notification") {
    return null;
  }

  const conversationId =
    readString(event.conversation_id);
  const messageId =
    readString(event.message_id);
  const senderDisplayName =
    readString(event.sender_display_name);
  const bodyPreview =
    readString(event.body_preview);
  const createdAt =
    readString(event.created_at);

  if (
    conversationId === null ||
    messageId === null ||
    senderDisplayName === null ||
    bodyPreview === null ||
    createdAt === null
  ) {
    return null;
  }

  return {
    id: messageId,
    conversationId,
    messageId,
    senderDisplayName,
    bodyPreview,
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
    useState<RealtimeMessageNotification | null>(null);

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

  const seenMessageIdsReference =
    useRef(new Set<string>());

  const seenMessageOrderReference =
    useRef<string[]>([]);

  const browserNotificationsSupported =
    browserNotificationPermission !== "unsupported";

  const browserNotificationsEnabled =
    browserNotificationsSupported &&
    browserNotificationPermission === "granted" &&
    browserNotificationPreference;

  const dismissNotification = useCallback(() => {
    setNotification(null);
  }, []);

  const enableBrowserNotifications =
    useCallback(async (): Promise<boolean> => {
      if (!isNotificationApiSupported()) {
        setBrowserNotificationPermission("unsupported");
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

  /**
   * Certains navigateurs permettent de modifier l'autorisation
   * directement depuis leurs paramètres.
   *
   * Nous resynchronisons donc l'état lorsque la fenêtre reprend
   * le focus ou lorsque la page redevient visible.
   */
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
      normalizeMessageNotification(lastEvent);

    if (normalizedNotification === null) {
      return;
    }

    if (
      seenMessageIdsReference.current.has(
        normalizedNotification.messageId,
      )
    ) {
      return;
    }

    seenMessageIdsReference.current.add(
      normalizedNotification.messageId,
    );

    seenMessageOrderReference.current.push(
      normalizedNotification.messageId,
    );

    if (
      seenMessageOrderReference.current.length >
      MAX_SEEN_MESSAGE_IDS
    ) {
      const oldestMessageId =
        seenMessageOrderReference.current.shift();

      if (oldestMessageId !== undefined) {
        seenMessageIdsReference.current.delete(
          oldestMessageId,
        );
      }
    }

    const currentConversationPath =
      `/messages/${encodeURIComponent(
        normalizedNotification.conversationId,
      )}`;

    /**
     * Si l'utilisateur regarde déjà cette conversation,
     * le message apparaît directement dans le fil.
     *
     * Nous n'affichons donc ni toast ni notification native.
     */
    if (location.pathname === currentConversationPath) {
      return;
    }

    setNotification(normalizedNotification);

    /**
     * La notification système est réservée aux situations où
     * Mbolo n'est pas réellement au premier plan.
     */
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
          "Nouveau message sur Mbolo",
          {
            body:
              `${normalizedNotification.senderDisplayName} ` +
              "t’a envoyé un nouveau message.",
            tag:
              `mbolo-message-${normalizedNotification.messageId}`,
            silent: false,
          },
        );

      nativeNotification.onclick = () => {
        window.focus();
        dismissNotification();
        navigate(currentConversationPath);
        nativeNotification.close();
      };
    } catch {
      /**
       * Une notification native ne doit jamais empêcher
       * le toast interne ou le reste de l'application.
       */
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
        setNotification((currentNotification) =>
          currentNotification?.id === notification.id
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
