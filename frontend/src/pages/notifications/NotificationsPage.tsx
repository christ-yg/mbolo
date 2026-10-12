/**
 * Centre de notifications premium de Mbolo.
 *
 * Principes conservés :
 * - historique chargé depuis l'API Django ;
 * - resynchronisation après les événements WebSocket du compte ;
 * - mutations protégées par la session et le jeton CSRF ;
 * - navigation limitée aux routes internes de l'application.
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
  getNotificationPreferences,
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  updateNotificationPreferences,
} from "../../api/notificationService";
import { useAccountRealtime } from "../../hooks/useAccountRealtime";
import type {
  NotificationItem,
  NotificationKind,
  NotificationPreferences,
} from "../../types/notifications";
import "./NotificationsPage.css";


type NotificationGroupKey =
  | "today"
  | "yesterday"
  | "older";

interface NotificationGroup {
  key: NotificationGroupKey;
  label: string;
  items: NotificationItem[];
}

type NotificationFilter =
  | "all"
  | "unread"
  | "messages"
  | "matches"
  | "likes"
  | "security";

const notificationFilters: ReadonlyArray<{
  key: NotificationFilter;
  label: string;
  symbol: string;
}> = [
  {key: "all", label: "Tout", symbol: "◇"},
  {key: "unread", label: "Non lues", symbol: "●"},
  {key: "messages", label: "Messages", symbol: "✉"},
  {key: "matches", label: "Matchs", symbol: "♥"},
  {key: "likes", label: "Likes", symbol: "★"},
  {key: "security", label: "Sécurité", symbol: "◆"},
];

function matchesNotificationFilter(
  notification: NotificationItem,
  filter: NotificationFilter,
): boolean {
  switch (filter) {
    case "all":
      return true;
    case "unread":
      return !notification.is_read;
    case "messages":
      return notification.kind === "message";
    case "matches":
      return notification.kind === "match";
    case "likes":
      return notification.kind === "like" || notification.kind === "super_like";
    case "security":
      return notification.kind === "security" || notification.kind === "system";
  }
}


function parseDate(value: string): Date | null {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}


function startOfDay(date: Date): Date {
  const result = new Date(date);
  result.setHours(0, 0, 0, 0);
  return result;
}


function getGroupKey(value: string): NotificationGroupKey {
  const date = parseDate(value);

  if (!date) {
    return "older";
  }

  const today = startOfDay(new Date());
  const notificationDay = startOfDay(date);
  const difference = today.getTime() - notificationDay.getTime();
  const oneDay = 24 * 60 * 60 * 1000;

  if (difference === 0) {
    return "today";
  }

  if (difference === oneDay) {
    return "yesterday";
  }

  return "older";
}


function formatNotificationDate(value: string): string {
  const date = parseDate(value);

  if (!date) {
    return "";
  }

  const group = getGroupKey(value);

  if (group === "today") {
    return new Intl.DateTimeFormat("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  if (group === "yesterday") {
    return `Hier, ${new Intl.DateTimeFormat("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date)}`;
  }

  return new Intl.DateTimeFormat("fr-FR", {
    day: "2-digit",
    month: "short",
    year: date.getFullYear() === new Date().getFullYear()
      ? undefined
      : "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}


function getKindLabel(kind: NotificationKind): string {
  switch (kind) {
    case "message":
      return "Message";
    case "match":
      return "Nouveau match";
    case "like":
      return "Nouvel intérêt";
    case "super_like":
      return "Super Like";
    case "security":
      return "Sécurité";
    case "system":
      return "Information Mbolo";
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


function isSafeInternalPath(path: string): boolean {
  if (!path.startsWith("/") || path.startsWith("//")) {
    return false;
  }

  try {
    const url = new URL(path, window.location.origin);
    return url.origin === window.location.origin;
  } catch {
    return false;
  }
}


function groupNotifications(
  notifications: NotificationItem[],
): NotificationGroup[] {
  const grouped: Record<NotificationGroupKey, NotificationItem[]> = {
    today: [],
    yesterday: [],
    older: [],
  };

  for (const notification of notifications) {
    grouped[getGroupKey(notification.created_at)].push(notification);
  }

  const groups: NotificationGroup[] = [
    {
      key: "today",
      label: "Aujourd’hui",
      items: grouped.today,
    },
    {
      key: "yesterday",
      label: "Hier",
      items: grouped.yesterday,
    },
    {
      key: "older",
      label: "Plus ancien",
      items: grouped.older,
    },
  ];

  return groups.filter((group) => group.items.length > 0);
}


export function NotificationsPage() {
  const navigate = useNavigate();
  const { revision, lastEvent } = useAccountRealtime();

  const [notifications, setNotifications] =
    useState<NotificationItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [preferences, setPreferences] =
    useState<NotificationPreferences | null>(null);
  const [preferencesOpen, setPreferencesOpen] = useState(false);
  const [preferencesLoading, setPreferencesLoading] = useState(false);
  const [preferencesSaving, setPreferencesSaving] = useState(false);
  const [preferencesError, setPreferencesError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] =
    useState<NotificationFilter>("all");

  const unreadCount = useMemo(
    () => notifications.filter((item) => !item.is_read).length,
    [notifications],
  );

  const filteredNotifications = useMemo(
    () => notifications.filter((notification) =>
      matchesNotificationFilter(notification, activeFilter)),
    [activeFilter, notifications],
  );

  const groupedNotifications = useMemo(
    () => groupNotifications(filteredNotifications),
    [filteredNotifications],
  );

  const filterCounts = useMemo(() => {
    const counts = new Map<NotificationFilter, number>();
    for (const filter of notificationFilters) {
      counts.set(
        filter.key,
        notifications.filter((notification) =>
          matchesNotificationFilter(notification, filter.key)).length,
      );
    }
    return counts;
  }, [notifications]);

  const readCount = Math.max(0, totalCount - unreadCount);

  const loadFirstPage = useCallback(async (): Promise<void> => {
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

  useEffect(() => {
    const eventName = lastEvent?.event;

    if (
      eventName === "message.notification" ||
      eventName === "like.notification" ||
      eventName === "match.notification" ||
      eventName === "report.notification" ||
      eventName === "security.notification" ||
      eventName === "notification.unread.changed"
    ) {
      void loadFirstPage();
    }
  }, [lastEvent, loadFirstPage, revision]);

  async function handleLoadMore(): Promise<void> {
    if (isLoadingMore || !hasNextPage) {
      return;
    }

    const nextPage = currentPage + 1;
    setIsLoadingMore(true);
    setErrorMessage(null);

    try {
      const response = await getNotifications(nextPage, 20);

      setNotifications((currentItems) => {
        const knownIds = new Set(currentItems.map((item) => item.id));

        return [
          ...currentItems,
          ...response.results.filter((item) => !knownIds.has(item.id)),
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
        const updated = await markNotificationRead(notification.id);
        setNotifications((currentItems) =>
          currentItems.map((item) =>
            item.id === updated.id ? updated : item,
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

    if (isSafeInternalPath(notification.target_path)) {
      navigate(notification.target_path);
    }
  }

  async function handleMarkAllRead(): Promise<void> {
    if (isMarkingAll || unreadCount === 0) {
      return;
    }

    setIsMarkingAll(true);
    setErrorMessage(null);

    try {
      const response = await markAllNotificationsRead();

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

  async function handleDelete(notificationId: string): Promise<void> {
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
        currentItems.filter((item) => item.id !== notificationId),
      );
      setTotalCount((currentCount) => Math.max(0, currentCount - 1));
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

  async function handleOpenPreferences(): Promise<void> {
    setPreferencesOpen(true);
    setPreferencesLoading(true);
    setPreferencesError(null);
    try {
      setPreferences(await getNotificationPreferences());
    } catch (error: unknown) {
      setPreferencesError(
        error instanceof Error
          ? error.message
          : "Impossible de charger les préférences.",
      );
    } finally {
      setPreferencesLoading(false);
    }
  }

  function updatePreference(
    key: keyof NotificationPreferences,
    value: boolean | string,
  ): void {
    setPreferences((current) => current === null
      ? null
      : {...current, [key]: value});
  }

  async function handleSavePreferences(): Promise<void> {
    if (preferences === null || preferencesSaving) {
      return;
    }
    if (preferences.quiet_start === preferences.quiet_end) {
      setPreferencesError(
        "Le début et la fin des heures silencieuses doivent différer.",
      );
      return;
    }
    setPreferencesSaving(true);
    setPreferencesError(null);
    try {
      const saved = await updateNotificationPreferences({
        notifications_enabled: preferences.notifications_enabled,
        messages_enabled: preferences.messages_enabled,
        matches_enabled: preferences.matches_enabled,
        likes_enabled: preferences.likes_enabled,
        quiet_hours_enabled: preferences.quiet_hours_enabled,
        quiet_start: preferences.quiet_start,
        quiet_end: preferences.quiet_end,
        timezone_offset_minutes: -new Date().getTimezoneOffset(),
      });
      setPreferences(saved);
      setPreferencesOpen(false);
    } catch (error: unknown) {
      setPreferencesError(
        error instanceof Error
          ? error.message
          : "Impossible d’enregistrer les préférences.",
      );
    } finally {
      setPreferencesSaving(false);
    }
  }

  return (
    <main className="notifications-page">
      <section className="notifications-hero">
        <div className="notifications-hero__copy">
          <p className="notifications-eyebrow">Activité de ton compte</p>
          <h1>Notifications</h1>
          <p className="notifications-hero__intro">
            Retrouve les nouveaux messages, les matchs, les intérêts reçus
            et les alertes importantes dans un espace clair et privé.
          </p>

          <div className="notifications-hero__trust" aria-label="Garanties">
            <span>✓ Événements contrôlés côté serveur</span>
            <span>✓ Accès réservé à ton compte</span>
            <span>✓ Navigation interne sécurisée</span>
          </div>
        </div>

        <aside className="notifications-summary" aria-label="Résumé">
          <div className="notifications-summary__icon" aria-hidden="true">◇</div>
          <div className="notifications-summary__numbers">
            <div>
              <strong>{unreadCount > 99 ? "99+" : unreadCount}</strong>
              <span>non lue{unreadCount > 1 ? "s" : ""}</span>
            </div>
            <div>
              <strong>{readCount}</strong>
              <span>déjà consultée{readCount > 1 ? "s" : ""}</span>
            </div>
          </div>
          <button
            type="button"
            className="notifications-summary__action"
            disabled={unreadCount === 0 || isMarkingAll}
            onClick={() => void handleMarkAllRead()}
          >
            {isMarkingAll ? "Traitement…" : "Tout marquer comme lu"}
          </button>
          <button
            type="button"
            className="notifications-summary__preferences"
            onClick={() => void handleOpenPreferences()}
          >
            Régler mes notifications
          </button>
        </aside>
      </section>

      <section className="notifications-content">
        <header className="notifications-content__header">
          <div>
            <p className="notifications-eyebrow">Ton activité récente</p>
            <h2>Reste au courant, sans bruit inutile.</h2>
          </div>
          <p>
            {totalCount === 0
              ? "Aucune notification enregistrée"
              : `${totalCount} notification${totalCount > 1 ? "s" : ""} au total`}
          </p>
        </header>

        {errorMessage ? (
          <div className="notifications-error" role="alert">
            <span aria-hidden="true">!</span>
            <p>{errorMessage}</p>
            <button type="button" onClick={() => void loadFirstPage()}>
              Réessayer
            </button>
          </div>
        ) : null}

        <div className="notifications-filters" aria-label="Filtrer les notifications">
          <div className="notifications-filters__heading">
            <strong>Filtrer l’activité</strong>
            <span>Résultats chargés sur cet appareil</span>
          </div>
          <div className="notifications-filters__scroller" role="toolbar">
            {notificationFilters.map((filter) => (
              <button
                key={filter.key}
                type="button"
                className={activeFilter === filter.key
                  ? "notifications-filter notifications-filter--active"
                  : "notifications-filter"}
                aria-pressed={activeFilter === filter.key}
                onClick={() => setActiveFilter(filter.key)}
              >
                <span aria-hidden="true">{filter.symbol}</span>
                {filter.label}
                <strong>{filterCounts.get(filter.key) ?? 0}</strong>
              </button>
            ))}
          </div>
        </div>

        <div className="notifications-list" aria-busy={isLoading}>
          {isLoading ? (
            <div className="notifications-state">
              <span className="notifications-state__loader" aria-hidden="true" />
              <h3>Chargement de ton activité…</h3>
              <p>Les notifications sont récupérées depuis ton compte Mbolo.</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="notifications-state notifications-state--empty">
              <span className="notifications-state__success" aria-hidden="true">✓</span>
              <p className="notifications-eyebrow">Tout est à jour</p>
              <h3>Aucune notification en attente</h3>
              <p>
                Les nouveaux messages, matchs et événements importants
                apparaîtront automatiquement ici.
              </p>
              <button type="button" onClick={() => navigate("/discover")}>
                Continuer à découvrir →
              </button>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="notifications-state notifications-state--empty">
              <span className="notifications-state__success" aria-hidden="true">◇</span>
              <p className="notifications-eyebrow">Filtre actif</p>
              <h3>Aucune activité dans cette catégorie</h3>
              <p>
                Les prochaines notifications correspondantes apparaîtront ici.
              </p>
              <button type="button" onClick={() => setActiveFilter("all")}>
                Voir toute l’activité
              </button>
            </div>
          ) : (
            groupedNotifications.map((group) => (
              <section className="notifications-group" key={group.key}>
                <div className="notifications-group__heading">
                  <h3>{group.label}</h3>
                  <span>{group.items.length}</span>
                </div>

                <div className="notifications-group__items">
                  {group.items.map((notification) => {
                    const isPending = pendingIds.has(notification.id);
                    const hasTarget = isSafeInternalPath(notification.target_path);

                    return (
                      <article
                        key={notification.id}
                        className={
                          notification.is_read
                            ? "notification-item"
                            : "notification-item notification-item--unread"
                        }
                      >
                        <button
                          type="button"
                          className="notification-item__main"
                          disabled={isPending}
                          onClick={() => void handleOpenNotification(notification)}
                        >
                          <span
                            className={`notification-item__symbol notification-item__symbol--${notification.kind}`}
                            aria-hidden="true"
                          >
                            {getKindSymbol(notification.kind)}
                          </span>

                          <span className="notification-item__content">
                            <span className="notification-item__meta">
                              <strong>{getKindLabel(notification.kind)}</strong>
                              <time dateTime={notification.created_at}>
                                {formatNotificationDate(notification.created_at)}
                              </time>
                            </span>

                            <span className="notification-item__title">
                              {notification.title}
                            </span>

                            {notification.body ? (
                              <span className="notification-item__body">
                                {notification.body}
                              </span>
                            ) : null}
                          </span>

                          <span className="notification-item__status">
                            {!notification.is_read ? (
                              <span className="notification-item__unread">
                                <i aria-hidden="true" />
                                Nouveau
                              </span>
                            ) : (
                              <span className="notification-item__read">Consultée</span>
                            )}

                            {hasTarget ? (
                              <span className="notification-item__open">Ouvrir →</span>
                            ) : null}
                          </span>
                        </button>

                        <button
                          type="button"
                          className="notification-item__delete"
                          aria-label={`Supprimer la notification : ${notification.title}`}
                          disabled={isPending}
                          onClick={() => void handleDelete(notification.id)}
                        >
                          ×
                        </button>
                      </article>
                    );
                  })}
                </div>
              </section>
            ))
          )}
        </div>

        {hasNextPage ? (
          <div className="notifications-pagination">
            <button
              type="button"
              disabled={isLoadingMore}
              onClick={() => void handleLoadMore()}
            >
              {isLoadingMore ? "Chargement…" : "Afficher plus de notifications"}
            </button>
          </div>
        ) : null}
      </section>

      {preferencesOpen ? (
        <div
          className="notification-preferences-overlay"
          role="presentation"
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) {
              setPreferencesOpen(false);
            }
          }}
        >
          <section
            className="notification-preferences-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="notification-preferences-title"
          >
            <header>
              <div>
                <p className="notifications-eyebrow">Expérience maîtrisée</p>
                <h2 id="notification-preferences-title">
                  Préférences de notifications
                </h2>
              </div>
              <button
                type="button"
                className="notification-preferences-panel__close"
                aria-label="Fermer les préférences"
                onClick={() => setPreferencesOpen(false)}
              >
                ×
              </button>
            </header>

            {preferencesLoading ? (
              <div className="notification-preferences-panel__loading">
                Chargement des préférences…
              </div>
            ) : preferences === null ? (
              <div className="notifications-error" role="alert">
                <span aria-hidden="true">!</span>
                <p>{preferencesError ?? "Préférences indisponibles."}</p>
                <button type="button" onClick={() => void handleOpenPreferences()}>
                  Réessayer
                </button>
              </div>
            ) : (
              <>
                <div className="notification-preferences-list">
                  <label className="notification-preference-row">
                    <span><strong>Notifications MBOLO</strong><small>Activer les alertes personnalisées</small></span>
                    <input
                      type="checkbox"
                      checked={preferences.notifications_enabled}
                      onChange={(event) => updatePreference("notifications_enabled", event.target.checked)}
                    />
                  </label>
                  {([
                    ["messages_enabled", "Messages", "Nouveaux messages et réactions"],
                    ["matches_enabled", "Matchs", "Nouvelles connexions réciproques"],
                    ["likes_enabled", "Likes et Super Likes", "Activité reçue sur ton profil"],
                  ] as const).map(([key, title, description]) => (
                    <label className="notification-preference-row" key={key}>
                      <span><strong>{title}</strong><small>{description}</small></span>
                      <input
                        type="checkbox"
                        checked={preferences[key]}
                        disabled={!preferences.notifications_enabled}
                        onChange={(event) => updatePreference(key, event.target.checked)}
                      />
                    </label>
                  ))}
                  <label className="notification-preference-row notification-preference-row--locked">
                    <span><strong>Sécurité du compte</strong><small>Toujours active pour protéger ton compte</small></span>
                    <input type="checkbox" checked disabled aria-label="Sécurité toujours active" />
                  </label>
                  <label className="notification-preference-row">
                    <span><strong>Heures silencieuses</strong><small>Suspendre les alertes non urgentes pendant ton repos</small></span>
                    <input
                      type="checkbox"
                      checked={preferences.quiet_hours_enabled}
                      disabled={!preferences.notifications_enabled}
                      onChange={(event) => updatePreference("quiet_hours_enabled", event.target.checked)}
                    />
                  </label>
                </div>

                {preferences.quiet_hours_enabled ? (
                  <div className="notification-preferences-times">
                    <label>Début<input type="time" value={preferences.quiet_start} onChange={(event) => updatePreference("quiet_start", event.target.value)} /></label>
                    <label>Fin<input type="time" value={preferences.quiet_end} onChange={(event) => updatePreference("quiet_end", event.target.value)} /></label>
                  </div>
                ) : null}

                {preferencesError ? (
                  <p className="notification-preferences-panel__error" role="alert">
                    {preferencesError}
                  </p>
                ) : null}

                <footer>
                  <button type="button" onClick={() => setPreferencesOpen(false)}>
                    Annuler
                  </button>
                  <button
                    type="button"
                    disabled={preferencesSaving}
                    onClick={() => void handleSavePreferences()}
                  >
                    {preferencesSaving ? "Enregistrement…" : "Enregistrer"}
                  </button>
                </footer>
              </>
            )}
          </section>
        </div>
      ) : null}
    </main>
  );
}
