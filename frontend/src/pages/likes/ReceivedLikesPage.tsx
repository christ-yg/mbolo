
/**
 * Page « Qui m’a liké ».
 *
 * La version gratuite conserve l’identité de l’auteur masquée.
 * L’utilisateur peut néanmoins répondre au like :
 *
 * - « Ça m’intéresse » peut créer un match ;
 * - « Passer » retire la carte de la liste en attente.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  getReceivedLikes,
  respondToReceivedLike,
} from "../../api/interactionService";

import type {
  InteractionDecision,
  ReceivedLikeItem,
} from "../../types/interactions";


type ReceivedLikesStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";


function formatReceivedDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "medium",
    },
  ).format(date);
}


export function ReceivedLikesPage() {
  const navigate = useNavigate();

  const [status, setStatus] =
    useState<ReceivedLikesStatus>("loading");

  const [items, setItems] =
    useState<ReceivedLikeItem[]>([]);

  const [totalCount, setTotalCount] =
    useState(0);

  const [currentPage, setCurrentPage] =
    useState(1);

  const [hasNextPage, setHasNextPage] =
    useState(false);

  const [isLoadingMore, setIsLoadingMore] =
    useState(false);

  const [pendingIds, setPendingIds] =
    useState<Set<string>>(new Set());

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [matchMessage, setMatchMessage] =
    useState<string | null>(null);

  const pendingCount = useMemo(
    () => items.length,
    [items],
  );

  const loadFirstPage =
    useCallback(async (): Promise<void> => {
      setStatus("loading");
      setErrorMessage(null);

      try {
        const response =
          await getReceivedLikes(1, 12);

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
        const normalized =
          normalizeApiError(error);

        setErrorMessage(normalized.message);
        setStatus("error");
      }
    }, []);

  useEffect(() => {
    void loadFirstPage();
  }, [loadFirstPage]);

  async function handleLoadMore(): Promise<void> {
    if (
      isLoadingMore ||
      !hasNextPage
    ) {
      return;
    }

    setIsLoadingMore(true);
    setErrorMessage(null);

    const nextPage = currentPage + 1;

    try {
      const response =
        await getReceivedLikes(nextPage, 12);

      setItems((currentItems) => {
        const knownIds =
          new Set(
            currentItems.map(
              (item) => item.interaction_id,
            ),
          );

        return [
          ...currentItems,
          ...response.results.filter(
            (item) =>
              !knownIds.has(item.interaction_id),
          ),
        ];
      });

      setCurrentPage(nextPage);
      setTotalCount(response.count);
      setHasNextPage(response.next !== null);
    } catch (error: unknown) {
      const normalized =
        normalizeApiError(error);

      setErrorMessage(normalized.message);
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function handleDecision(
    item: ReceivedLikeItem,
    decision: InteractionDecision,
  ): Promise<void> {
    if (pendingIds.has(item.interaction_id)) {
      return;
    }

    setPendingIds((currentIds) => {
      const nextIds = new Set(currentIds);
      nextIds.add(item.interaction_id);
      return nextIds;
    });

    setErrorMessage(null);

    try {
      const response =
        await respondToReceivedLike(
          item.interaction_id,
          { decision },
        );

      setItems((currentItems) =>
        currentItems.filter(
          (currentItem) =>
            currentItem.interaction_id !==
            item.interaction_id,
        ),
      );

      setTotalCount((currentCount) =>
        Math.max(0, currentCount - 1),
      );

      if (
        response.matched &&
        response.revealed_profile
      ) {
        setMatchMessage(
          `Nouveau match avec ${response.revealed_profile.display_name}.`,
        );
      }

      if (
        items.length === 1 &&
        !hasNextPage
      ) {
        setStatus("empty");
      }
    } catch (error: unknown) {
      const normalized =
        normalizeApiError(error);

      setErrorMessage(normalized.message);
    } finally {
      setPendingIds((currentIds) => {
        const nextIds = new Set(currentIds);
        nextIds.delete(item.interaction_id);
        return nextIds;
      });
    }
  }

  return (
    <main className="received-likes-page">
      <section className="received-likes-page__header">
        <div>
          <p className="section-heading__eyebrow">
            Intérêt reçu
          </p>

          <h1>Qui m’a liké</h1>

          <p>
            Découvre les indices essentiels sans compromettre
            la confidentialité des membres.
          </p>
        </div>

        <div className="received-likes-page__counter">
          <strong>
            {totalCount > 99 ? "99+" : totalCount}
          </strong>

          <span>
            like{totalCount > 1 ? "s" : ""} en attente
          </span>
        </div>
      </section>

      <section className="received-likes-premium-note">
        <span aria-hidden="true">◇</span>

        <div>
          <strong>Identité protégée</strong>

          <p>
            Dans cette version, le nom et la photo ne sont
            révélés qu’après un like réciproque.
          </p>
        </div>

        <small>Compatible avec une future offre Premium</small>
      </section>

      {matchMessage ? (
        <section
          className="received-likes-match-alert"
          role="status"
        >
          <div>
            <strong>{matchMessage}</strong>
            <span>
              Vous pouvez maintenant discuter dans Mes matchs.
            </span>
          </div>

          <button
            type="button"
            onClick={() => {
              navigate("/matches");
            }}
          >
            Voir mes matchs
          </button>
        </section>
      ) : null}

      {errorMessage ? (
        <div
          className="received-likes-page__error"
          role="alert"
        >
          {errorMessage}
        </div>
      ) : null}

      {status === "loading" ? (
        <section className="received-likes-state">
          Chargement des likes reçus…
        </section>
      ) : status === "error" ? (
        <section className="received-likes-state">
          <h2>Impossible de charger cette page.</h2>

          <button
            type="button"
            onClick={() => {
              void loadFirstPage();
            }}
          >
            Réessayer
          </button>
        </section>
      ) : status === "empty" ? (
        <section className="received-likes-state">
          <span aria-hidden="true">♡</span>

          <h2>Aucun like en attente</h2>

          <p>
            Les nouveaux likes apparaîtront ici automatiquement
            après une prochaine visite.
          </p>

          <button
            type="button"
            onClick={() => {
              navigate("/discovery");
            }}
          >
            Continuer à découvrir
          </button>
        </section>
      ) : (
        <>
          <section className="received-likes-grid">
            {items.map((item, index) => {
              const isPending =
                pendingIds.has(item.interaction_id);

              return (
                <article
                  key={item.interaction_id}
                  className="received-like-card"
                >
                  <div className="received-like-card__visual">
                    <span aria-hidden="true">
                      {item.has_photo ? "●" : "◇"}
                    </span>

                    <small>
                      Profil {String(index + 1).padStart(2, "0")}
                    </small>
                  </div>

                  <div className="received-like-card__content">
                    <div className="received-like-card__meta">
                      <span>{item.city}</span>

                      <time dateTime={item.received_at}>
                        {formatReceivedDate(
                          item.received_at,
                        )}
                      </time>
                    </div>

                    <h2>Quelqu’un s’intéresse à toi</h2>

                    <dl>
                      <div>
                        <dt>Âge</dt>
                        <dd>{item.age_range}</dd>
                      </div>

                      <div>
                        <dt>Recherche</dt>
                        <dd>{item.dating_intent}</dd>
                      </div>

                      <div>
                        <dt>Photo</dt>
                        <dd>
                          {item.has_photo
                            ? "Profil avec photo"
                            : "Silhouette protégée"}
                        </dd>
                      </div>
                    </dl>

                    <div className="received-like-card__actions">
                      <button
                        type="button"
                        className="received-like-card__pass"
                        disabled={isPending}
                        onClick={() => {
                          void handleDecision(
                            item,
                            "pass",
                          );
                        }}
                      >
                        Passer
                      </button>

                      <button
                        type="button"
                        className="received-like-card__like"
                        disabled={isPending}
                        onClick={() => {
                          void handleDecision(
                            item,
                            "like",
                          );
                        }}
                      >
                        {isPending
                          ? "Traitement…"
                          : "Ça m’intéresse"}
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </section>

          <p className="received-likes-page__visible-count">
            {pendingCount} carte
            {pendingCount > 1 ? "s" : ""} affichée
            {pendingCount > 1 ? "s" : ""}
          </p>

          {hasNextPage ? (
            <div className="received-likes-pagination">
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
        </>
      )}
    </main>
  );
}
