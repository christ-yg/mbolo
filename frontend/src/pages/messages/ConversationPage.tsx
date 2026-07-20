/**
 * Écran d'une conversation privée.
 *
 * Route :
 *
 *     /messages/:conversationId
 */

import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Link,
  useParams,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  DEFAULT_MESSAGES_PAGE_SIZE,
  getConversationMessages,
  sendConversationMessage,
} from "../../api/messagingService";
import { MessageBubble } from "../../components/messaging/MessageBubble";

import type {
  MessageItem,
  MessagesPaginatedResponse,
} from "../../types/messaging";


const MAX_MESSAGE_LENGTH = 2000;


type ConversationStatus =
  | "loading"
  | "success"
  | "error";


export function ConversationPage() {
  const { conversationId } =
    useParams<{ conversationId: string }>();

  const [status, setStatus] =
    useState<ConversationStatus>("loading");

  const [messagesData, setMessagesData] =
    useState<MessagesPaginatedResponse | null>(
      null,
    );

  const [messageBody, setMessageBody] =
    useState("");

  const [errorMessage, setErrorMessage] =
    useState("");

  const [sendError, setSendError] =
    useState("");

  const [isSending, setIsSending] =
    useState(false);

  const bottomRef =
    useRef<HTMLDivElement | null>(null);


  const loadMessages = useCallback(
    async (): Promise<void> => {
      if (!conversationId) {
        setErrorMessage(
          "L’identifiant de conversation est absent.",
        );
        setStatus("error");
        return;
      }

      setStatus("loading");
      setErrorMessage("");

      try {
        const result =
          await getConversationMessages(
            conversationId,
            {
              page: 1,
              pageSize:
                DEFAULT_MESSAGES_PAGE_SIZE,
            },
          );

        setMessagesData(result);
        setStatus("success");
      } catch (error: unknown) {
        const normalizedError =
          normalizeApiError(error);

        setErrorMessage(normalizedError.message);
        setStatus("error");
      }
    },
    [conversationId],
  );


  useEffect(() => {
    void loadMessages();
  }, [loadMessages]);


  useEffect(() => {
    if (status === "success") {
      bottomRef.current?.scrollIntoView({
        behavior: "smooth",
      });
    }
  }, [
    status,
    messagesData?.results.length,
  ]);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (!conversationId || isSending) {
      return;
    }

    const normalizedBody =
      messageBody.trim();

    if (!normalizedBody) {
      setSendError(
        "Écris un message avant de l’envoyer.",
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

      setMessagesData((currentData) => {
        if (!currentData) {
          return {
            count: 1,
            next: null,
            previous: null,
            results: [createdMessage],
          };
        }

        return {
          ...currentData,
          count: currentData.count + 1,
          results: [
            ...currentData.results,
            createdMessage,
          ],
        };
      });

      setMessageBody("");
    } catch (error: unknown) {
      const normalizedError =
        normalizeApiError(error);

      setSendError(normalizedError.message);
    } finally {
      setIsSending(false);
    }
  }


  if (status === "loading") {
    return (
      <main className="conversation-page">
        <section
          className="messaging-state-card"
          role="status"
        >
          <div
            className="auth-loading-card__spinner"
            aria-hidden="true"
          />

          <h2>Chargement des messages</h2>
        </section>
      </main>
    );
  }


  if (status === "error") {
    return (
      <main className="conversation-page">
        <Link
          className="conversation-page__back"
          to="/messages"
        >
          ← Retour aux conversations
        </Link>

        <section
          className="messaging-state-card messaging-state-card--error"
          role="alert"
        >
          <div
            className="messaging-state-card__symbol"
            aria-hidden="true"
          >
            !
          </div>

          <h2>Conversation inaccessible</h2>

          <p>{errorMessage}</p>

          <button
            type="button"
            onClick={() => {
              void loadMessages();
            }}
          >
            Réessayer
          </button>
        </section>
      </main>
    );
  }


  const messages: MessageItem[] =
    messagesData?.results ?? [];


  return (
    <main className="conversation-page">
      <header className="conversation-page__header">
        <Link
          className="conversation-page__back"
          to="/messages"
        >
          ← Mes messages
        </Link>

        <div>
          <p className="section-heading__eyebrow">
            Conversation privée
          </p>

          <h1>Discussion sécurisée</h1>
        </div>

        <button
          type="button"
          onClick={() => {
            void loadMessages();
          }}
        >
          Actualiser
        </button>
      </header>

      <section
        className="conversation-thread"
        aria-label="Historique de la conversation"
        aria-live="polite"
      >
        {messages.length === 0 ? (
          <div className="conversation-thread__empty">
            <span aria-hidden="true">✉</span>

            <h2>Commence la conversation</h2>

            <p>
              Écris un premier message respectueux
              et authentique.
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

        <div ref={bottomRef} />
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
            {sendError}
          </div>
        ) : null}

        <div className="message-composer__controls">
          <label
            className="sr-only"
            htmlFor="message-body"
          >
            Votre message
          </label>

          <textarea
            id="message-body"
            value={messageBody}
            maxLength={MAX_MESSAGE_LENGTH}
            placeholder="Écris ton message…"
            rows={3}
            disabled={isSending}
            onChange={(event) => {
              setMessageBody(
                event.target.value,
              );
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
          </button>
        </div>

        <div className="message-composer__footer">
          <span>
            Les messages sont accessibles uniquement
            aux deux participants du match.
          </span>

          <strong>
            {messageBody.length}/{MAX_MESSAGE_LENGTH}
          </strong>
        </div>
      </form>
    </main>
  );
}
