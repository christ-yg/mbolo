
/**
 * Centre de notifications durable de Mbolo.
 *
 * La page charge l'historique depuis PostgreSQL, puis se resynchronise
 * lorsqu'un événement arrive par le WebSocket global du compte.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  deleteNotification,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "../../api/notificationService";
import { useAccountRealtime } from "../../hooks/useAccountRealtime";
import type {
  NotificationItem,
  NotificationKind,
} from "../../types/notifications";


function formatNotificationDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


function getKindLabel(kind: NotificationKind): string {
  switch (kind) {
    case "message":
      return "Message";
    case "match":
      return "Nouveau match";
    case "like":
      return "Like";
    case "super_like":
      return "Super Like";
    case "security":
      return "Sécurité";
    case "system":
      return "Mbolo";
  }
}


function getKindSymbol(kind: NotificationKind): string {
  switch (kind) {
    case "message":
      return "✉";
    case "match":
      return "♥";
    case "like":
      return "♡";
    case "super_like":
      return "★";
    case "security":
      return "!";
    case "system":
      return "M";
  }
}


export function NotificationsPage() {
  const navigate = useNavigate();

  const {
    revision,
    lastEvent,
  } = useAccountRealtime();

  const [
    notifications,
    setNotifications,
  ] = useState<NotificationItem[]>([]);

  const [totalCount, setTotalCount] =
    useState(0);

  const [currentPage, setCurrentPage] =
    useState(1);

  const [hasNextPage, setHasNextPage] =
    useState(false);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isLoadingMore, setIsLoadingMore] =
    useState(false);

  const [isMarkingAll, setIsMarkingAll] =
    useState(false);

  const [pendingIds, setPendingIds] =
    useState<Set<string>>(new Set());

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const unreadCount = useMemo(
    () =>
      notifications.filter(
        (notification) => !notification.is_read,
      ).length,
    [notifications],
  );

  const loadFirstPage =
    useCallback(async (): Promise<void> => {
      setErrorMessage(null);

      try {
        const response = await getNotifications(1, 20);

        setNotifications(response.results);
        setTotalCount(response.count);
        setCurrentPage(1);
        setHasNextPage(response.next !== null);
      } catch (error: unknown) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Impossible de charger les notifications.",
        );
      } finally {
        setIsLoading(false);
      }
    }, []);

  useEffect(() => {
    void loadFirstPage();
  }, [loadFirstPage]);

  /**
   * Seuls les événements susceptibles de modifier le centre
   * déclenchent une resynchronisation.
   */
  useEffect(() => {
    const eventName = lastEvent?.event;

    if (
      eventName === "message.notification" ||
      eventName === "like.notification" ||
      eventName === "match.notification" ||
      eventName === "notification.unread.changed"
    ) {
      void loadFirstPage();
    }
  }, [
    lastEvent,
    loadFirstPage,
    revision,
  ]);

  async function handleLoadMore(): Promise<void> {
    if (
      isLoadingMore ||
      !hasNextPage
    ) {
      return;
    }

    const nextPage = currentPage + 1;

    setIsLoadingMore(true);
    setErrorMessage(null);

    try {
      const response =
        await getNotifications(nextPage, 20);

      setNotifications((currentItems) => {
        const knownIds =
          new Set(currentItems.map((item) => item.id));

        return [
          ...currentItems,
          ...response.results.filter(
            (item) => !knownIds.has(item.id),
          ),
        ];
      });

      setTotalCount(response.count);
      setCurrentPage(nextPage);
      setHasNextPage(response.next !== null);
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Impossible de charger la page suivante.",
      );
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function handleOpenNotification(
    notification: NotificationItem,
  ): Promise<void> {
    if (pendingIds.has(notification.id)) {
      return;
    }

    if (!notification.is_read) {
      setPendingIds((currentIds) => {
        const nextIds = new Set(currentIds);
        nextIds.add(notification.id);
        return nextIds;
      });

      try {
        const updated =
          await markNotificationRead(notification.id);

        setNotifications((currentItems) =>
          currentItems.map((item) =>
            item.id === updated.id
              ? updated
              : item,
          ),
        );
      } catch (error: unknown) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "La notification n’a pas pu être marquée comme lue.",
        );
      } finally {
        setPendingIds((currentIds) => {
          const nextIds = new Set(currentIds);
          nextIds.delete(notification.id);
          return nextIds;
        });
      }
    }

    if (
      notification.target_path.startsWith("/")
    ) {
      navigate(notification.target_path);
    }
  }

  async function handleMarkAllRead(): Promise<void> {
    if (
      isMarkingAll ||
      unreadCount === 0
    ) {
      return;
    }

    setIsMarkingAll(true);
    setErrorMessage(null);

    try {
      const response =
        await markAllNotificationsRead();

      setNotifications((currentItems) =>
        currentItems.map((item) => ({
          ...item,
          is_read: true,
          read_at: item.read_at ?? response.read_at,
        })),
      );
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Impossible de tout marquer comme lu.",
      );
    } finally {
      setIsMarkingAll(false);
    }
  }

  async function handleDelete(
    notificationId: string,
  ): Promise<void> {
    if (pendingIds.has(notificationId)) {
      return;
    }

    setPendingIds((currentIds) => {
      const nextIds = new Set(currentIds);
      nextIds.add(notificationId);
      return nextIds;
    });

    try {
      await deleteNotification(notificationId);

      setNotifications((currentItems) =>
        currentItems.filter(
          (item) => item.id !== notificationId,
        ),
      );

      setTotalCount((currentCount) =>
        Math.max(0, currentCount - 1),
      );
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Impossible de supprimer la notification.",
      );
    } finally {
      setPendingIds((currentIds) => {
        const nextIds = new Set(currentIds);
        nextIds.delete(notificationId);
        return nextIds;
      });
    }
  }

  return (
    <main className="notification-center">
      <section className="notification-center__header">
        <div>
          <p className="section-heading__eyebrow">
            Activité du compte
          </p>

          <h1>Notifications</h1>

          <p>
            Retrouve ici les messages et les futurs événements
            importants liés à ton compte Mbolo.
          </p>
        </div>

        <div className="notification-center__summary">
          <span>
            {unreadCount > 99
              ? "99+"
              : unreadCount}
          </span>

          <div>
            <strong>Non lues</strong>
            <small>{totalCount} notification(s)</small>
          </div>

          <button
            type="button"
            disabled={
              unreadCount === 0 ||
              isMarkingAll
            }
            onClick={() => {
              void handleMarkAllRead();
            }}
          >
            {isMarkingAll
              ? "Traitement…"
              : "Tout marquer comme lu"}
          </button>
        </div>
      </section>

      {errorMessage ? (
        <div
          className="notification-center__error"
          role="alert"
        >
          {errorMessage}
        </div>
      ) : null}

      <section
        className="notification-center__list"
        aria-busy={isLoading}
      >
        {isLoading ? (
          <div className="notification-center__state">
            Chargement des notifications…
          </div>
        ) : notifications.length === 0 ? (
          <div className="notification-center__empty">
            <span aria-hidden="true">✓</span>
            <h2>Tout est à jour</h2>
            <p>
              Les nouveaux messages, matchs et événements
              importants apparaîtront ici.
            </p>
          </div>
        ) : (
          notifications.map((notification) => {
            const isPending =
              pendingIds.has(notification.id);

            return (
              <article
                key={notification.id}
                className={
                  notification.is_read
                    ? "notification-card"
                    : (
                        "notification-card " +
                        "notification-card--unread"
                      )
                }
              >
                <button
                  type="button"
                  className="notification-card__main"
                  disabled={isPending}
                  onClick={() => {
                    void handleOpenNotification(
                      notification,
                    );
                  }}
                >
                  <span
                    className={
                      `notification-card__symbol ` +
                      `notification-card__symbol--${notification.kind}`
                    }
                    aria-hidden="true"
                  >
                    {getKindSymbol(notification.kind)}
                  </span>

                  <span className="notification-card__content">
                    <span className="notification-card__meta">
                      <strong>
                        {getKindLabel(notification.kind)}
                      </strong>

                      <time
                        dateTime={notification.created_at}
                      >
                        {formatNotificationDate(
                          notification.created_at,
                        )}
                      </time>
                    </span>

                    <span className="notification-card__title">
                      {notification.title}
                    </span>

                    {notification.body ? (
                      <span className="notification-card__body">
                        {notification.body}
                      </span>
                    ) : null}
                  </span>

                  {!notification.is_read ? (
                    <span
                      className="notification-card__unread-dot"
                      aria-label="Non lue"
                    />
                  ) : null}

                  <span
                    className="notification-card__arrow"
                    aria-hidden="true"
                  >
                    →
                  </span>
                </button>

                <button
                  type="button"
                  className="notification-card__delete"
                  aria-label="Supprimer la notification"
                  disabled={isPending}
                  onClick={() => {
                    void handleDelete(notification.id);
                  }}
                >
                  ×
                </button>
              </article>
            );
          })
        )}
      </section>

      {hasNextPage ? (
        <div className="notification-center__pagination">
          <button
            type="button"
            disabled={isLoadingMore}
            onClick={() => {
              void handleLoadMore();
            }}
          >
            {isLoadingMore
              ? "Chargement…"
              : "Charger plus"}
          </button>
        </div>
      ) : null}
    </main>
  );
}
