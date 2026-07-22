
import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import {
  getBlockedUsers,
  unblockUser,
} from "../../api/safetyService";
import type {
  BlockedUserItem,
} from "../../types/safety";

type PageStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {dateStyle: "medium"},
  ).format(date);
}

function getPhoto(item: BlockedUserItem): string | null {
  const photos = [...(item.blocked_profile?.photos ?? [])];

  photos.sort(
    (a, b) =>
      Number(b.is_primary) - Number(a.is_primary) ||
      a.position - b.position,
  );

  return photos[0]?.image_url ?? null;
}

export function BlockedUsersPage() {
  const navigate = useNavigate();

  const [status, setStatus] =
    useState<PageStatus>("loading");
  const [items, setItems] =
    useState<BlockedUserItem[]>([]);
  const [totalCount, setTotalCount] =
    useState(0);
  const [currentPage, setCurrentPage] =
    useState(1);
  const [hasNextPage, setHasNextPage] =
    useState(false);
  const [isLoadingMore, setIsLoadingMore] =
    useState(false);
  const [confirmingItem, setConfirmingItem] =
    useState<BlockedUserItem | null>(null);
  const [pendingId, setPendingId] =
    useState<string | null>(null);
  const [errorMessage, setErrorMessage] =
    useState("");

  const loadFirstPage =
    useCallback(async (): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");

      try {
        const response = await getBlockedUsers(1, 20);

        setItems(response.results);
        setTotalCount(response.count);
        setCurrentPage(1);
        setHasNextPage(response.next !== null);
        setStatus(
          response.results.length > 0
            ? "success"
            : "empty",
        );
      } catch (error: unknown) {
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Impossible de charger les profils bloqués.",
        );
        setStatus("error");
      }
    }, []);

  useEffect(() => {
    void loadFirstPage();
  }, [loadFirstPage]);

  async function loadMore(): Promise<void> {
    if (isLoadingMore || !hasNextPage) {
      return;
    }

    setIsLoadingMore(true);

    try {
      const nextPage = currentPage + 1;
      const response =
        await getBlockedUsers(nextPage, 20);

      setItems((currentItems) => [
        ...currentItems,
        ...response.results.filter(
          (item) =>
            !currentItems.some(
              (existing) => existing.id === item.id,
            ),
        ),
      ]);

      setCurrentPage(nextPage);
      setTotalCount(response.count);
      setHasNextPage(response.next !== null);
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Impossible de charger la suite.",
      );
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function confirmUnblock(
    item: BlockedUserItem,
  ): Promise<void> {
    if (pendingId !== null) {
      return;
    }

    setPendingId(item.id);
    setErrorMessage("");

    try {
      await unblockUser(item.id);

      setItems((currentItems) =>
        currentItems.filter(
          (currentItem) => currentItem.id !== item.id,
        ),
      );
      setTotalCount((count) => Math.max(0, count - 1));
      setConfirmingItem(null);

      if (items.length === 1 && !hasNextPage) {
        setStatus("empty");
      }
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Le déblocage a échoué.",
      );
    } finally {
      setPendingId(null);
    }
  }

  return (
    <main className="blocked-users-page">
      <section className="blocked-users-page__header">
        <div>
          <p className="section-heading__eyebrow">
            Confidentialité
          </p>
          <h1>Profils bloqués</h1>
          <p>
            Un déblocage ne restaure jamais automatiquement
            un ancien match ni une conversation.
          </p>
        </div>

        <div className="blocked-users-page__counter">
          <strong>{totalCount > 99 ? "99+" : totalCount}</strong>
          <span>profil(s) bloqué(s)</span>
        </div>
      </section>

      {errorMessage ? (
        <div className="blocked-users-page__error" role="alert">
          {errorMessage}
        </div>
      ) : null}

      {status === "loading" ? (
        <section className="blocked-users-state">
          Chargement des profils bloqués…
        </section>
      ) : status === "error" ? (
        <section className="blocked-users-state">
          <h2>Chargement impossible</h2>
          <button type="button" onClick={() => void loadFirstPage()}>
            Réessayer
          </button>
        </section>
      ) : status === "empty" ? (
        <section className="blocked-users-state">
          <span aria-hidden="true">✓</span>
          <h2>Aucun profil bloqué</h2>
          <p>
            Les profils bloqués apparaîtront ici.
          </p>
          <button type="button" onClick={() => navigate("/safety")}>
            Retour à Sécurité
          </button>
        </section>
      ) : (
        <>
          <section className="blocked-users-grid">
            {items.map((item) => {
              const profile = item.blocked_profile;
              const photo = getPhoto(item);

              return (
                <article key={item.id} className="blocked-user-card">
                  <div className="blocked-user-card__visual">
                    {photo ? (
                      <img src={photo} alt="" loading="lazy" />
                    ) : (
                      <span aria-hidden="true">
                        {profile?.display_name?.charAt(0).toUpperCase() ?? "?"}
                      </span>
                    )}
                  </div>

                  <div className="blocked-user-card__content">
                    <p className="blocked-user-card__eyebrow">
                      Bloqué le {formatDate(item.created_at)}
                    </p>
                    <h2>
                      {profile?.display_name ?? "Profil indisponible"}
                    </h2>
                    <p>
                      {profile
                        ? `${profile.age ?? "Âge non précisé"} · ${
                            profile.city_label ?? profile.city
                          }`
                        : "Ce compte ne possède plus de profil public."}
                    </p>
                    <button
                      type="button"
                      disabled={pendingId !== null}
                      onClick={() => setConfirmingItem(item)}
                    >
                      Débloquer
                    </button>
                  </div>
                </article>
              );
            })}
          </section>

          {hasNextPage ? (
            <div className="blocked-users-pagination">
              <button
                type="button"
                disabled={isLoadingMore}
                onClick={() => void loadMore()}
              >
                {isLoadingMore ? "Chargement…" : "Charger plus"}
              </button>
            </div>
          ) : null}
        </>
      )}

      {confirmingItem ? (
        <div className="blocked-users-dialog-backdrop">
          <section
            className="blocked-users-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="unblock-title"
          >
            <p className="section-heading__eyebrow">
              Confirmation
            </p>
            <h2 id="unblock-title">
              Débloquer{" "}
              {confirmingItem.blocked_profile?.display_name ??
                "ce profil"} ?
            </h2>
            <p>
              Cette personne pourra réapparaître dans Découvrir
              si son profil est encore visible. L’ancien match
              restera désactivé.
            </p>

            <div className="blocked-users-dialog__actions">
              <button
                type="button"
                disabled={pendingId !== null}
                onClick={() => setConfirmingItem(null)}
              >
                Annuler
              </button>
              <button
                type="button"
                disabled={pendingId !== null}
                onClick={() => void confirmUnblock(confirmingItem)}
              >
                {pendingId === confirmingItem.id
                  ? "Déblocage…"
                  : "Confirmer"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
