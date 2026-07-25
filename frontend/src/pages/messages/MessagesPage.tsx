/**
 * Page principale de la messagerie Mbolo.
 *
 * Route : /messages
 *
 * Cette page conserve la logique métier existante :
 * - récupération paginée des conversations côté serveur ;
 * - actualisation après événement WebSocket ;
 * - affichage uniquement des conversations autorisées par l'API ;
 * - aucun contrôle d'accès sensible n'est décidé dans le navigateur.
 */

import {
  useCallback,
  useEffect,
  useMemo,
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

import "./MessagesPage.css";


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
    useState<ConversationsPaginatedResponse | null>(null);

  const [errorMessage, setErrorMessage] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState("");


  const loadConversations = useCallback(
    async (page: number): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");

      try {
        const result = await getConversations({
          page,
          pageSize: DEFAULT_CONVERSATIONS_PAGE_SIZE,
        });

        setData(result);
        setCurrentPage(page);
        setStatus(
          result.results.length === 0 ? "empty" : "success",
        );
      } catch (error: unknown) {
        const normalizedError = normalizeApiError(error);

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


  const conversations: ConversationItem[] = data?.results ?? [];

  const filteredConversations = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLocaleLowerCase("fr-FR");

    if (!normalizedSearch) {
      return conversations;
    }

    return conversations.filter((conversation) => {
      const profile = conversation.other_profile;
      const lastMessage = conversation.last_message?.body ?? "";
      const searchableText = [
        profile.display_name,
        profile.city,
        String(profile.age ?? ""),
        lastMessage,
      ]
        .join(" ")
        .toLocaleLowerCase("fr-FR");

      return searchableText.includes(normalizedSearch);
    });
  }, [conversations, searchTerm]);


  const unreadMessageCount = conversations.reduce(
    (total, conversation) => total + conversation.unread_count,
    0,
  );

  const onlineCount = conversations.filter(
    (conversation) => conversation.other_presence.is_online,
  ).length;


  if (status === "loading") {
    return (
      <main className="messages-page messages-page--state">
        <section className="messages-state-card" role="status" aria-live="polite">
          <div className="messages-state-card__spinner" aria-hidden="true" />
          <p className="messages-page__eyebrow">Messagerie privée</p>
          <h1>Chargement de tes conversations</h1>
          <p>
            Mbolo récupère uniquement les échanges liés à tes matchs actifs.
          </p>
        </section>
      </main>
    );
  }


  if (status === "error") {
    return (
      <main className="messages-page messages-page--state">
        <section className="messages-state-card messages-state-card--error" role="alert">
          <div className="messages-state-card__icon" aria-hidden="true">!</div>
          <p className="messages-page__eyebrow">Messagerie privée</p>
          <h1>Impossible de charger tes conversations</h1>
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
      <main className="messages-page messages-page--state">
        <section className="messages-empty-card">
          <div className="messages-empty-card__visual" aria-hidden="true">
            <span>♡</span>
            <span>✉</span>
          </div>

          <div className="messages-empty-card__copy">
            <p className="messages-page__eyebrow">Conversations privées</p>
            <h1>Une vraie conversation commence après un match.</h1>
            <p>
              Dès que l’intérêt devient réciproque, un espace de discussion privé
              et protégé s’ouvre automatiquement.
            </p>

            <div className="messages-empty-card__actions">
              <Link className="messages-button messages-button--primary" to="/discovery">
                Découvrir des profils →
              </Link>
              <Link className="messages-button messages-button--secondary" to="/matches">
                Voir mes matchs
              </Link>
            </div>
          </div>
        </section>
      </main>
    );
  }


  return (
    <main className="messages-page">
      <section className="messages-hero">
        <div className="messages-hero__copy">
          <p className="messages-page__eyebrow">Échanges après réciprocité</p>
          <h1>Mes messages</h1>
          <p>
            Retrouve tes conversations privées, réponds à tes matchs et poursuis
            les connexions qui comptent vraiment.
          </p>

          <div className="messages-hero__trust">
            <span>✓ Messagerie après match</span>
            <span>✓ Accès contrôlé côté serveur</span>
            <span>✓ Conversations privées</span>
          </div>
        </div>

        <div className="messages-hero__summary" aria-label="Résumé de la messagerie">
          <div>
            <strong>{data?.count ?? 0}</strong>
            <span>{(data?.count ?? 0) > 1 ? "conversations" : "conversation"}</span>
          </div>
          <div>
            <strong>{unreadMessageCount}</strong>
            <span>non lu{unreadMessageCount > 1 ? "s" : ""}</span>
          </div>
          <div>
            <strong>{onlineCount}</strong>
            <span>en ligne</span>
          </div>
        </div>
      </section>

      <section className="messages-workspace" aria-label="Espace de messagerie">
        <div className="messages-workspace__topbar">
          <div>
            <p className="messages-page__eyebrow">Tes conversations</p>
            <h2>Continue là où vous vous êtes arrêtés.</h2>
          </div>

          <label className="messages-search">
            <span aria-hidden="true">⌕</span>
            <span className="sr-only">Rechercher une conversation</span>
            <input
              type="search"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Rechercher un prénom, une ville…"
            />
          </label>
        </div>

        {filteredConversations.length > 0 ? (
          <div className="conversations-grid" aria-label="Liste des conversations">
            {filteredConversations.map((conversation) => (
              <div
                key={conversation.id}
                className={
                  conversation.unread_count > 0
                    ? "conversation-list-item conversation-list-item--unread"
                    : "conversation-list-item"
                }
              >
                <ConversationCard conversation={conversation} />

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
                    : formatLastSeen(conversation.other_presence.last_seen_at)}
                </span>

                {conversation.unread_count > 0 ? (
                  <span
                    className="conversation-list-item__unread-badge"
                    aria-label={`${conversation.unread_count} message${conversation.unread_count > 1 ? "s" : ""} non lu${conversation.unread_count > 1 ? "s" : ""}`}
                  >
                    {conversation.unread_count > 99 ? "99+" : conversation.unread_count}
                  </span>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <div className="messages-search-empty" role="status">
            <div aria-hidden="true">⌕</div>
            <h3>Aucune conversation trouvée</h3>
            <p>Essaie un autre prénom, une autre ville ou efface la recherche.</p>
            <button type="button" onClick={() => setSearchTerm("")}>
              Effacer la recherche
            </button>
          </div>
        )}
      </section>

      {data?.previous || data?.next ? (
        <nav className="messages-pagination" aria-label="Pagination des conversations">
          <button
            type="button"
            disabled={!data.previous}
            onClick={() => {
              void loadConversations(Math.max(currentPage - 1, 1));
            }}
          >
            ← Précédente
          </button>

          <span>Page {currentPage}</span>

          <button
            type="button"
            disabled={!data.next}
            onClick={() => {
              void loadConversations(currentPage + 1);
            }}
          >
            Suivante →
          </button>
        </nav>
      ) : null}
    </main>
  );
}
