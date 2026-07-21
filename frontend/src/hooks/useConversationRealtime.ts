/** Hook React de synchronisation temps réel d'une conversation. */

import { useCallback, useEffect, useRef, useState } from "react";

import {
  ConversationSocket,
  type ConversationSocketEvent,
  type ConversationSocketState,
} from "../api/conversationSocket";
import type { MessageItem } from "../types/messaging";

interface RealtimeCallbacks {
  onMessageCreated: (message: MessageItem) => void;
  onOtherTypingChanged: (isTyping: boolean) => void;
  onMessagesRead: (readAt: string) => void;
}

export function useConversationRealtime(
  conversationId: string | undefined,
  callbacks: RealtimeCallbacks,
) {
  const [state, setState] = useState<ConversationSocketState>("closed");
  const socketReference = useRef<ConversationSocket | null>(null);
  const callbacksReference = useRef(callbacks);
  callbacksReference.current = callbacks;

  useEffect(() => {
    if (!conversationId) {
      return undefined;
    }

    const socket = new ConversationSocket(
      conversationId,
      (event: ConversationSocketEvent) => {
        if (event.event === "message.created" && event.message) {
          callbacksReference.current.onMessageCreated(event.message as MessageItem);
        }
        if (event.event === "typing.updated") {
          callbacksReference.current.onOtherTypingChanged(Boolean(event.other_is_typing));
        }
        if (event.event === "conversation.read" && event.read_by_other && event.read_at) {
          callbacksReference.current.onMessagesRead(String(event.read_at));
        }
      },
      setState,
    );

    socketReference.current = socket;
    socket.connect();

    const pingTimer = window.setInterval(() => {
      socket.send({ event: "ping" });
    }, 45_000);

    return () => {
      window.clearInterval(pingTimer);
      socket.close();
      socketReference.current = null;
    };
  }, [conversationId]);

  const publishTyping = useCallback((isTyping: boolean): boolean => {
    return socketReference.current?.send({
      event: "typing.set",
      is_typing: isTyping,
    }) ?? false;
  }, []);

  const publishRead = useCallback((): boolean => {
    return socketReference.current?.send({ event: "conversation.read" }) ?? false;
  }, []);

  return {
    state,
    isConnected: state === "open",
    publishTyping,
    publishRead,
  };
}
