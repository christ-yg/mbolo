/**
 * Contexte global des notifications visuelles Mbolo.
 *
 * Il transforme les événements du WebSocket personnel `/ws/account/`
 * en notifications visibles dans toute l'application authentifiée.
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
import { useLocation } from "react-router-dom";

import { useAccountRealtime } from "../hooks/useAccountRealtime";

export interface RealtimeMessageNotification {
  id: string;
  conversationId: string;
  messageId: string;
  senderDisplayName: string;
  bodyPreview: string;
  createdAt: string;
}

interface NotificationContextValue {
  notification: RealtimeMessageNotification | null;
  dismissNotification: () => void;
}

const NotificationContext =
  createContext<NotificationContextValue | undefined>(undefined);

const MAX_SEEN_MESSAGE_IDS = 200;

function readString(
  value: unknown,
): string | null {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : null;
}

function normalizeMessageNotification(
  event: Record<string, unknown>,
): RealtimeMessageNotification | null {
  if (event.event !== "message.notification") {
    return null;
  }

  const conversationId = readString(event.conversation_id);
  const messageId = readString(event.message_id);
  const senderDisplayName = readString(event.sender_display_name);
  const bodyPreview = readString(event.body_preview);
  const createdAt = readString(event.created_at);

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

export function NotificationProvider({
  children,
}: PropsWithChildren) {
  const location = useLocation();
  const { lastEvent, revision } = useAccountRealtime();
  const [notification, setNotification] =
    useState<RealtimeMessageNotification | null>(null);

  const seenMessageIdsReference = useRef(new Set<string>());
  const seenMessageOrderReference = useRef<string[]>([]);

  const dismissNotification = useCallback(() => {
    setNotification(null);
  }, []);

  useEffect(() => {
    if (lastEvent === null) {
      return;
    }

    const normalizedNotification = normalizeMessageNotification(lastEvent);

    if (normalizedNotification === null) {
      return;
    }

    if (seenMessageIdsReference.current.has(normalizedNotification.messageId)) {
      return;
    }

    seenMessageIdsReference.current.add(normalizedNotification.messageId);
    seenMessageOrderReference.current.push(normalizedNotification.messageId);

    if (seenMessageOrderReference.current.length > MAX_SEEN_MESSAGE_IDS) {
      const oldestMessageId = seenMessageOrderReference.current.shift();

      if (oldestMessageId !== undefined) {
        seenMessageIdsReference.current.delete(oldestMessageId);
      }
    }

    const currentConversationPath =
      `/messages/${encodeURIComponent(normalizedNotification.conversationId)}`;

    /**
     * Si l'utilisateur regarde déjà cette discussion, le message apparaît
     * directement dans le fil. Afficher aussi un toast serait redondant.
     */
    if (location.pathname === currentConversationPath) {
      return;
    }

    setNotification(normalizedNotification);
  }, [lastEvent, location.pathname, revision]);

  useEffect(() => {
    if (notification === null) {
      return undefined;
    }

    const timeoutIdentifier = window.setTimeout(() => {
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

  const contextValue = useMemo<NotificationContextValue>(
    () => ({
      notification,
      dismissNotification,
    }),
    [dismissNotification, notification],
  );

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotification(): NotificationContextValue {
  const context = useContext(NotificationContext);

  if (context === undefined) {
    throw new Error(
      "useNotification doit être utilisé dans NotificationProvider.",
    );
  }

  return context;
}
