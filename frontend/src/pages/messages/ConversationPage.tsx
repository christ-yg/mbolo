/**
 * Écran d'une conversation privée Mbolo.
 *
 * Route :
 *
 *     /messages/:conversationId
 *
 * Responsabilités :
 *
 * - vérifier l'identifiant de la conversation ;
 * - récupérer les informations publiques de l'autre profil ;
 * - charger l'historique des messages ;
 * - actualiser périodiquement la conversation ;
 * - envoyer un nouveau message ;
 * - faire défiler l'interface vers le dernier message.
 */

import {
  type FormEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Link,
  useParams,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  DEFAULT_CONVERSATIONS_PAGE_SIZE,
  DEFAULT_MESSAGES_PAGE_SIZE,
  getConversationMessages,
  getConversationTypingStatus,
  getConversations,
  markConversationAsRead,
  sendConversationMessage,
  setConversationTypingStatus,
} from "../../api/messagingService";
import { MessageBubble } from "../../components/messaging/MessageBubble";
import { useConversationRealtime } from "../../hooks/useConversationRealtime";

import type {
  ConversationItem,
  MessageItem,
} from "../../types/messaging";

import "../../styles/conversation.css";

const MAX_MESSAGE_LENGTH = 2000;
const REFRESH_INTERVAL_MILLISECONDS = 5000;
const TYPING_POLL_INTERVAL_MILLISECONDS = 2000;
const TYPING_DEBOUNCE_MILLISECONDS = 350;

type ConversationStatus =
  | "loading"
  | "success"
  | "error";

function sortMessagesByDate(
  messages: MessageItem[],
): MessageItem[] {
  return [...messages].sort((firstMessage, secondMessage) => {
    return (
      new Date(firstMessage.created_at).getTime() -
      new Date(secondMessage.created_at).getTime()
    );
  });
}

function getProfileInitial(
  displayName: string,
): string {
  const normalizedName = displayName.trim();

  if (normalizedName.length === 0) {
    return "M";
  }

  return normalizedName.charAt(0).toUpperCase();
}

function getProfileMetadata(
  conversation: ConversationItem | null,
): string {
  if (conversation === null) {
    return "";
  }

  const metadata: string[] = [];

  if (conversation.other_profile.age) {
    metadata.push(`${conversation.other_profile.age} ans`);
  }

  if (conversation.other_profile.city) {
    metadata.push(conversation.other_profile.city);
  }

  return metadata.join(" · ");
}


function formatPresenceLabel(
  isOnline: boolean,
  lastSeenAt: string | null,
): string {
  if (isOnline) {
    return "En ligne";
  }

  if (!lastSeenAt) {
    return "Hors ligne";
  }

  const date = new Date(lastSeenAt);
  if (Number.isNaN(date.getTime())) {
    return "Hors ligne";
  }

  return `Dernière connexion ${new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)}`;
}

export function ConversationPage() {
  const {
    conversationId,
  } = useParams<{
    conversationId: string;
  }>();

  const [status, setStatus] =
    useState<ConversationStatus>("loading");

  const [conversation, setConversation] =
    useState<ConversationItem | null>(null);

  const [messages, setMessages] =
    useState<MessageItem[]>([]);

  const [messageBody, setMessageBody] =
    useState("");

  const [pageError, setPageError] =
    useState("");

  const [sendError, setSendError] =
    useState("");

  const [isSending, setIsSending] =
    useState(false);

  const [isRefreshing, setIsRefreshing] =
    useState(false);

  const [otherIsTyping, setOtherIsTyping] =
    useState(false);

  const messagesEndReference =
    useRef<HTMLDivElement | null>(null);

  const previousMessageCountReference =
    useRef(0);

  const isInitialLoadReference =
    useRef(true);

  const typingDebounceReference =
    useRef<number | null>(null);

  const typingWasPublishedReference =
    useRef(false);

  const realtime = useConversationRealtime(
    conversationId,
    {
      onMessageCreated: (incomingMessage) => {
        setMessages((currentMessages) => {
          if (currentMessages.some((message) => message.id === incomingMessage.id)) {
            return currentMessages;
          }
          return sortMessagesByDate([...currentMessages, incomingMessage]);
        });

        if (!incomingMessage.is_mine && !incomingMessage.is_read) {
          window.dispatchEvent(new CustomEvent("mbolo:unread-count-changed"));
        }
      },
      onOtherTypingChanged: setOtherIsTyping,
      onMessagesRead: (readAt) => {
        setMessages((currentMessages) =>
          currentMessages.map((message) =>
            message.is_mine && !message.is_read
              ? { ...message, is_read: true, read_at: readAt }
              : message,
          ),
        );
      },
    },
  );

  const profileMetadata = useMemo(
    () => getProfileMetadata(conversation),
    [conversation],
  );

  const scrollToLatestMessage = useCallback(
    (behavior: ScrollBehavior = "smooth") => {
      messagesEndReference.current?.scrollIntoView({
        behavior,
        block: "end",
      });
    },
    [],
  );

  /**
   * Recherche la conversation dans la liste sécurisée du compte.
   *
   * Le backend ne possède pas encore d'endpoint GET dédié à une
   * conversation précise. Nous utilisons donc la liste des
   * conversations accessibles au compte connecté.
   */
  const loadConversationMetadata =
    useCallback(async (): Promise<ConversationItem | null> => {
      if (!conversationId) {
        return null;
      }

      const result = await getConversations({
        page: 1,
        pageSize: DEFAULT_CONVERSATIONS_PAGE_SIZE,
      });

      return (
        result.results.find(
          (candidateConversation) =>
            candidateConversation.id === conversationId,
        ) ?? null
      );
    }, [conversationId, realtime]);

  const markReceivedMessagesAsRead =
    useCallback(
      async (
        loadedMessages: MessageItem[],
      ): Promise<MessageItem[]> => {
        if (!conversationId) {
          return loadedMessages;
        }

        const hasUnreadReceivedMessage =
          loadedMessages.some(
            (message) =>
              !message.is_mine &&
              !message.is_read,
          );

        if (!hasUnreadReceivedMessage) {
          return loadedMessages;
        }

        try {
          const result =
            await markConversationAsRead(
              conversationId,
            );

          window.dispatchEvent(
            new CustomEvent(
              "mbolo:unread-count-changed",
            ),
          );

          realtime.publishRead();

          return loadedMessages.map((message) => {
            if (
              message.is_mine ||
              message.is_read
            ) {
              return message;
            }

            return {
              ...message,
              is_read: true,
              read_at:
                message.read_at ??
                result.read_at,
            };
          });
        } catch {
          /**
           * Un échec du marquage comme lu ne doit pas
           * empêcher l'affichage de la conversation.
           */
          return loadedMessages;
        }
      },
      [conversationId, realtime],
    );

  /**
   * Charge les messages.
   *
   * silent = true :
   * - utilisé par l'actualisation automatique ;
   * - n'efface pas l'écran ;
   * - ne montre pas le grand état de chargement.
   */
  const loadMessages = useCallback(
    async ({
      silent = false,
    }: {
      silent?: boolean;
    } = {}): Promise<void> => {
      if (!conversationId) {
        setPageError(
          "L'identifiant de la conversation est absent.",
        );
        setStatus("error");
        return;
      }

      if (silent) {
        setIsRefreshing(true);
      }

      try {
        const result =
          await getConversationMessages(
            conversationId,
            {
              page: 1,
              pageSize: DEFAULT_MESSAGES_PAGE_SIZE,
            },
          );

        const sortedMessages =
          sortMessagesByDate(result.results);

        const readableMessages =
          await markReceivedMessagesAsRead(
            sortedMessages,
          );

        setMessages(readableMessages);

        if (!silent) {
          setPageError("");
        }
      } catch (error: unknown) {
        const normalizedError =
          normalizeApiError(error);

        if (!silent) {
          setPageError(normalizedError.message);
          setStatus("error");
        }
      } finally {
        if (silent) {
          setIsRefreshing(false);
        }
      }
    },
    [
      conversationId,
      markReceivedMessagesAsRead,
    ],
  );

  /**
   * Chargement initial de l'écran.
   */
  useEffect(() => {
    let isComponentMounted = true;

    async function initializeConversation(): Promise<void> {
      if (!conversationId) {
        if (isComponentMounted) {
          setPageError(
            "Cette conversation ne peut pas être ouverte.",
          );
          setStatus("error");
        }

        return;
      }

      setStatus("loading");
      setPageError("");

      try {
        const [
          loadedConversation,
          loadedMessages,
        ] = await Promise.all([
          loadConversationMetadata(),
          getConversationMessages(
            conversationId,
            {
              page: 1,
              pageSize: DEFAULT_MESSAGES_PAGE_SIZE,
            },
          ),
        ]);

        if (!isComponentMounted) {
          return;
        }

        if (loadedConversation === null) {
          setPageError(
            "Cette conversation est introuvable ou n'est plus accessible.",
          );
          setStatus("error");
          return;
        }

        const sortedMessages =
          sortMessagesByDate(
            loadedMessages.results,
          );

        const readableMessages =
          await markReceivedMessagesAsRead(
            sortedMessages,
          );

        if (!isComponentMounted) {
          return;
        }

        setConversation({
          ...loadedConversation,
          unread_count: 0,
        });
        setMessages(readableMessages);
        setStatus("success");
      } catch (error: unknown) {
        if (!isComponentMounted) {
          return;
        }

        const normalizedError =
          normalizeApiError(error);

        setPageError(normalizedError.message);
        setStatus("error");
      }
    }

    void initializeConversation();

    return () => {
      isComponentMounted = false;
    };
  }, [
    conversationId,
    loadConversationMetadata,
    markReceivedMessagesAsRead,
  ]);

  /**
   * Actualisation automatique.
   *
   * Toutes les cinq secondes, le frontend redemande les messages
   * au backend. Cette solution convient au développement actuel.
   *
   * Plus tard, nous pourrons la remplacer par WebSocket/Django
   * Channels pour recevoir les messages en temps réel.
   */
  useEffect(() => {
    if (
      status !== "success" ||
      !conversationId ||
      realtime.isConnected
    ) {
      return undefined;
    }

    const intervalIdentifier =
      window.setInterval(() => {
        void loadMessages({
          silent: true,
        });
      }, REFRESH_INTERVAL_MILLISECONDS);

    return () => {
      window.clearInterval(
        intervalIdentifier,
      );
    };
  }, [
    conversationId,
    loadMessages,
    status,
    realtime.isConnected,
  ]);

  /**
   * Interroge régulièrement le backend pour savoir si
   * l'autre participant est en train d'écrire.
   */
  useEffect(() => {
    if (
      status !== "success" ||
      !conversationId ||
      realtime.isConnected
    ) {
      return undefined;
    }

    let isMounted = true;

    const refreshTypingStatus = async (): Promise<void> => {
      try {
        const result = await getConversationTypingStatus(conversationId);
        if (isMounted) {
          setOtherIsTyping(result.other_is_typing);
        }
      } catch {
        if (isMounted) {
          setOtherIsTyping(false);
        }
      }
    };

    void refreshTypingStatus();
    const intervalIdentifier = window.setInterval(
      () => { void refreshTypingStatus(); },
      TYPING_POLL_INTERVAL_MILLISECONDS,
    );

    return () => {
      isMounted = false;
      window.clearInterval(intervalIdentifier);
    };
  }, [conversationId, status, realtime.isConnected]);

  const publishTypingStatus = useCallback((isTyping: boolean): void => {
    if (!conversationId) {
      return;
    }

    if (realtime.publishTyping(isTyping)) {
      typingWasPublishedReference.current = isTyping;
      return;
    }

    if (typingDebounceReference.current !== null) {
      window.clearTimeout(typingDebounceReference.current);
    }

    typingDebounceReference.current = window.setTimeout(() => {
      if (!isTyping && !typingWasPublishedReference.current) {
        return;
      }

      typingWasPublishedReference.current = isTyping;
      void setConversationTypingStatus(conversationId, {
        is_typing: isTyping,
      }).catch(() => {
        typingWasPublishedReference.current = false;
      });
    }, isTyping ? TYPING_DEBOUNCE_MILLISECONDS : 0);
  }, [conversationId]);

  useEffect(() => {
    return () => {
      if (typingDebounceReference.current !== null) {
        window.clearTimeout(typingDebounceReference.current);
      }
      if (typingWasPublishedReference.current && conversationId) {
        void setConversationTypingStatus(conversationId, {
          is_typing: false,
        });
      }
    };
  }, [conversationId]);

  /**
   * Descend automatiquement vers le message le plus récent.
   */
  useEffect(() => {
    if (status !== "success") {
      return;
    }

    const messageCountChanged =
      previousMessageCountReference.current !==
      messages.length;

    if (!messageCountChanged) {
      return;
    }

    previousMessageCountReference.current =
      messages.length;

    const behavior: ScrollBehavior =
      isInitialLoadReference.current
        ? "auto"
        : "smooth";

    isInitialLoadReference.current = false;

    window.setTimeout(() => {
      scrollToLatestMessage(behavior);
    }, 30);
  }, [
    messages.length,
    scrollToLatestMessage,
    status,
  ]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (
      !conversationId ||
      isSending
    ) {
      return;
    }

    const normalizedBody =
      messageBody.trim();

    if (normalizedBody.length === 0) {
      setSendError(
        "Écris un message avant de l'envoyer.",
      );
      return;
    }

    if (
      normalizedBody.length >
      MAX_MESSAGE_LENGTH
    ) {
      setSendError(
        `Le message ne peut pas dépasser ${MAX_MESSAGE_LENGTH} caractères.`,
      );
      return;
    }

    setIsSending(true);
    setSendError("");

    try {
      const createdMessage =
        await sendConversationMessage(
          conversationId,
          {
            body: normalizedBody,
          },
        );

      setMessages((currentMessages) => {
        const messageAlreadyExists =
          currentMessages.some(
            (message) =>
              message.id ===
              createdMessage.id,
          );

        if (messageAlreadyExists) {
          return currentMessages;
        }

        return sortMessagesByDate([
          ...currentMessages,
          createdMessage,
        ]);
      });

      publishTypingStatus(false);
      setMessageBody("");

      window.setTimeout(() => {
        scrollToLatestMessage("smooth");
      }, 30);
    } catch (error: unknown) {
      const normalizedError =
        normalizeApiError(error);

      setSendError(normalizedError.message);
    } finally {
      setIsSending(false);
    }
  }

  function handleTextareaKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ): void {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      if (
        !isSending &&
        messageBody.trim().length > 0
      ) {
        event.currentTarget.form?.requestSubmit();
      }
    }
  }

  if (status === "loading") {
    return (
      <main className="conversation-page">
        <section
          className="conversation-state-card"
          role="status"
          aria-live="polite"
        >
          <div
            className="conversation-loading-spinner"
            aria-hidden="true"
          />

          <h1>Ouverture de la conversation</h1>

          <p>
            Mbolo vérifie l’accès à cette discussion privée.
          </p>
        </section>
      </main>
    );
  }

  if (
    status === "error" ||
    conversation === null
  ) {
    return (
      <main className="conversation-page">
        <section
          className="conversation-state-card conversation-state-card--error"
          role="alert"
        >
          <span
            className="conversation-state-card__symbol"
            aria-hidden="true"
          >
            !
          </span>

          <h1>Conversation indisponible</h1>

          <p>
            {pageError ||
              "Cette conversation ne peut pas être affichée."}
          </p>

          <Link
            className="conversation-state-card__link"
            to="/messages"
          >
            Retourner à mes messages
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="conversation-page">
      <section className="conversation-shell">
        <header className="conversation-header">
          <Link
            className="conversation-header__back-link"
            to="/messages"
          >
            <span aria-hidden="true">←</span>
            Mes messages
          </Link>

          <div className="conversation-contact">
            <div
              className="conversation-contact__avatar"
              aria-hidden="true"
            >
              {getProfileInitial(
                conversation.other_profile.display_name,
              )}
            </div>

            <div className="conversation-contact__identity">
              <p className="conversation-contact__eyebrow">
                Conversation privée
              </p>

              <div className="conversation-contact__name-row">
                <h1>
                  {
                    conversation.other_profile
                      .display_name
                  }
                </h1>

                {conversation.other_profile.is_verified ? (
                  <span
                    className="conversation-contact__verified"
                    title="Profil vérifié"
                    aria-label="Profil vérifié"
                  >
                    ✓
                  </span>
                ) : null}
              </div>

              {profileMetadata ? (
                <p className="conversation-contact__metadata">
                  {profileMetadata}
                </p>
              ) : null}

              <p
                className={
                  conversation.other_presence.is_online
                    ? "conversation-contact__presence conversation-contact__presence--online"
                    : "conversation-contact__presence"
                }
              >
                <span aria-hidden="true" />
                {formatPresenceLabel(
                  conversation.other_presence.is_online,
                  conversation.other_presence.last_seen_at,
                )}
              </p>
            </div>
          </div>

          <button
            type="button"
            className="conversation-header__refresh-button"
            disabled={isRefreshing}
            onClick={() => {
              void loadMessages({
                silent: true,
              });
            }}
          >
            {isRefreshing
              ? "Actualisation…"
              : "Actualiser"}
          </button>
        </header>

        <section
          className="conversation-messages"
          aria-label={`Conversation avec ${conversation.other_profile.display_name}`}
          aria-live="polite"
        >
          {messages.length === 0 ? (
            <div className="conversation-empty-state">
              <span aria-hidden="true">♡</span>

              <h2>Commence la conversation</h2>

              <p>
                Vous avez un match. Tu peux maintenant envoyer
                ton premier message en toute confidentialité.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
              />
            ))
          )}


          {otherIsTyping ? (
            <div
              className="conversation-typing-indicator"
              role="status"
              aria-live="polite"
            >
              <span aria-hidden="true"><i /><i /><i /></span>
              {conversation.other_profile.display_name} écrit…
            </div>
          ) : null}

          <div
            ref={messagesEndReference}
            className="conversation-messages__end"
            aria-hidden="true"
          />
        </section>

        <form
          className="message-composer"
          onSubmit={(event) => {
            void handleSubmit(event);
          }}
        >
          {sendError ? (
            <div
              className="message-composer__error"
              role="alert"
            >
              <span aria-hidden="true">!</span>

              <p>{sendError}</p>

              <button
                type="button"
                aria-label="Fermer le message d'erreur"
                onClick={() => {
                  setSendError("");
                }}
              >
                ×
              </button>
            </div>
          ) : null}

          <label
            className="message-composer__label"
            htmlFor="message-body"
          >
            Ton message
          </label>

          <div className="message-composer__controls">
            <textarea
              id="message-body"
              value={messageBody}
              maxLength={MAX_MESSAGE_LENGTH}
              placeholder={`Écris à ${conversation.other_profile.display_name}…`}
              rows={3}
              disabled={isSending}
              onKeyDown={handleTextareaKeyDown}
              onChange={(event) => {
                const nextValue = event.target.value;
                setMessageBody(nextValue);
                publishTypingStatus(nextValue.trim().length > 0);
                setSendError("");
              }}
            />

            <button
              type="submit"
              disabled={
                isSending ||
                messageBody.trim().length === 0
              }
            >
              {isSending
                ? "Envoi…"
                : "Envoyer"}
              <span aria-hidden="true">→</span>
            </button>
          </div>

          <div className="message-composer__footer">
            <span>
              Entrée pour envoyer · Maj + Entrée pour aller à la
              ligne
            </span>

            <strong
              className={
                messageBody.length >=
                MAX_MESSAGE_LENGTH
                  ? "message-composer__counter message-composer__counter--limit"
                  : "message-composer__counter"
              }
            >
              {messageBody.length}/{MAX_MESSAGE_LENGTH}
            </strong>
          </div>
        </form>
      </section>
    </main>
  );
}
