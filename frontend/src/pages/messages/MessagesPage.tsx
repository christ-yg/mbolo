/**
 * Page principale de la messagerie.
 *
 * Route :
 *
 *     /messages
 */

import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  DEFAULT_CONVERSATIONS_PAGE_SIZE,
  getConversations,
} from "../../api/messagingService";
import { ConversationCard } from "../../components/messaging/ConversationCard";
import { useAccountRealtime } from "../../hooks/useAccountRealtime";

import type {
  ConversationItem,
  ConversationsPaginatedResponse,
} from "../../types/messaging";


type ConversationsStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";



function formatLastSeen(lastSeenAt: string | null): string {
  if (!lastSeenAt) {
    return "Hors ligne";
  }

  const date = new Date(lastSeenAt);
  if (Number.isNaN(date.getTime())) {
    return "Hors ligne";
  }

  return `Vu ${new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)}`;
}

export function MessagesPage() {
  const { lastEvent, revision } = useAccountRealtime();

  const [status, setStatus] =
    useState<ConversationsStatus>("loading");

  const [data, setData] =
    useState<ConversationsPaginatedResponse | null>(
      null,
    );

  const [errorMessage, setErrorMessage] =
    useState("");

  const [currentPage, setCurrentPage] =
    useState(1);


  const loadConversations = useCallback(
    async (page: number): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");

      try {
        const result = await getConversations({
          page,
          pageSize:
            DEFAULT_CONVERSATIONS_PAGE_SIZE,
        });

        setData(result);
        setCurrentPage(page);

        setStatus(
          result.results.length === 0
            ? "empty"
            : "success",
        );
      } catch (error: unknown) {
        const normalizedError =
          normalizeApiError(error);

        setData(null);
        setErrorMessage(normalizedError.message);
        setStatus("error");
      }
    },
    [],
  );


  useEffect(() => {
    void loadConversations(1);
  }, [loadConversations]);

  useEffect(() => {
    if (revision === 0 || lastEvent === null) {
      return;
    }

    if (
      lastEvent.event === "message.notification" ||
      lastEvent.event === "conversation.updated" ||
      lastEvent.event === "unread.count.changed"
    ) {
      void loadConversations(currentPage);
    }
  }, [currentPage, lastEvent, loadConversations, revision]);


  const conversations: ConversationItem[] =
    data?.results ?? [];

  const unreadMessageCount =
    conversations.reduce(
      (total, conversation) =>
        total + conversation.unread_count,
      0,
    );


  if (status === "loading") {
    return (
      <main className="messages-page">
        <section className="messages-page__heading">
          <p className="section-heading__eyebrow">
            Conversations privées
          </p>

          <h1>Chargement de tes messages.</h1>

          <p>
            Seules les conversations liées à tes matchs
            actifs sont récupérées.
          </p>
        </section>

        <section
          className="messaging-state-card"
          role="status"
          aria-live="polite"
        >
          <div
            className="auth-loading-card__spinner"
            aria-hidden="true"
          />

          <h2>Chargement en cours</h2>
        </section>
      </main>
    );
  }


  if (status === "error") {
    return (
      <main className="messages-page">
        <section className="messages-page__heading">
          <p className="section-heading__eyebrow">
            Messagerie privée
          </p>

          <h1>Impossible de charger les conversations.</h1>
        </section>

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

          <h2>Une erreur est survenue</h2>

          <p>{errorMessage}</p>

          <button
            type="button"
            onClick={() => {
              void loadConversations(currentPage);
            }}
          >
            Réessayer
          </button>
        </section>
      </main>
    );
  }


  if (status === "empty") {
    return (
      <main className="messages-page">
        <section className="messages-page__heading">
          <p className="section-heading__eyebrow">
            Conversations privées
          </p>

          <h1>Mes messages</h1>

          <p>
            Une conversation devient disponible après
            la création d’un match réciproque.
          </p>
        </section>

        <section className="messaging-state-card">
          <div
            className="messaging-state-card__symbol"
            aria-hidden="true"
          >
            ✉
          </div>

          <h2>Aucune conversation</h2>

          <p>
            Commence par découvrir de nouveaux profils
            et créer une connexion réciproque.
          </p>

          <Link to="/discovery">
            Continuer la découverte →
          </Link>
        </section>
      </main>
    );
  }


  return (
    <main className="messages-page">
      <section className="messages-page__heading">
        <div>
          <p className="section-heading__eyebrow">
            Conversations privées
          </p>

          <h1>Mes messages</h1>

          <p>
            Discute uniquement avec les personnes avec
            lesquelles tu possèdes un match actif.
          </p>
        </div>

        <div className="messages-page__summary">
          <span>{data?.count ?? 0}</span>

          <p>
            {(data?.count ?? 0) > 1
              ? "conversations"
              : "conversation"}
          </p>

          {unreadMessageCount > 0 ? (
            <small>
              {unreadMessageCount} non lu
              {unreadMessageCount > 1 ? "s" : ""}
            </small>
          ) : null}
        </div>
      </section>

      <section
        className="conversations-list"
        aria-label="Liste des conversations"
      >
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={
              conversation.unread_count > 0
                ? "conversation-list-item conversation-list-item--unread"
                : "conversation-list-item"
            }
          >
            <ConversationCard
              conversation={conversation}
            />

            <span
              className={
                conversation.other_presence.is_online
                  ? "conversation-presence conversation-presence--online"
                  : "conversation-presence"
              }
            >
              <span aria-hidden="true" />
              {conversation.other_presence.is_online
                ? "En ligne"
                : formatLastSeen(
                    conversation.other_presence.last_seen_at,
                  )}
            </span>

            {conversation.unread_count > 0 ? (
              <span
                className="conversation-list-item__unread-badge"
                aria-label={`${conversation.unread_count} message${conversation.unread_count > 1 ? "s" : ""} non lu${conversation.unread_count > 1 ? "s" : ""}`}
              >
                {conversation.unread_count > 99
                  ? "99+"
                  : conversation.unread_count}
              </span>
            ) : null}
          </div>
        ))}
      </section>

      {data?.previous || data?.next ? (
        <nav
          className="messages-pagination"
          aria-label="Pagination des conversations"
        >
          <button
            type="button"
            disabled={!data.previous}
            onClick={() => {
              void loadConversations(
                Math.max(currentPage - 1, 1),
              );
            }}
          >
            ← Précédente
          </button>

          <span>Page {currentPage}</span>

          <button
            type="button"
            disabled={!data.next}
            onClick={() => {
              void loadConversations(
                currentPage + 1,
              );
            }}
          >
            Suivante →
          </button>
        </nav>
      ) : null}
    </main>
  );
}
