/**
 * Page « Qui m’a liké ».
 *
 * Principes métier conservés :
 * - l’identité reste masquée selon l’offre décidée côté serveur ;
 * - l’utilisateur peut répondre à chaque intérêt reçu ;
 * - un like réciproque peut créer un match ;
 * - la pagination et les états d’erreur restent gérés côté client.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
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

import "./ReceivedLikesPage.css";


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

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
  }).format(date);
}


export function ReceivedLikesPage() {
  const navigate = useNavigate();

  const [status, setStatus] =
    useState<ReceivedLikesStatus>("loading");

  const [items, setItems] =
    useState<ReceivedLikeItem[]>([]);

  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const [pendingIds, setPendingIds] =
    useState<Set<string>>(new Set());

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null);

  const [matchMessage, setMatchMessage] =
    useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [kind, setKind] = useState("all");
  const [sort, setSort] = useState("recent");
  const [refreshing, setRefreshing] = useState(false);
  const fetching = useRef(false);
  const deciding = useRef(false);
  const restartPagination = useRef(false);
  const visibleItems = useMemo(() => {
    const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr");
    const query = normalize(search.trim());
    return items.filter(item =>
      (kind === "all" || (kind === "super" ? item.is_super_like : item.is_identity_revealed)) &&
      normalize(`${item.city} ${item.age_range} ${item.dating_intent} ${item.is_identity_revealed ? item.display_name ?? "" : ""}`).includes(query),
    ).sort((a, b) => {
      const difference = (Date.parse(b.received_at) || 0) - (Date.parse(a.received_at) || 0);
      return sort === "oldest" ? -difference : difference;
    });
  }, [items, search, kind, sort]);
  function resetFilters() { setSearch(""); setKind("all"); setSort("recent"); }
  const pendingCount = visibleItems.length;

  const loadFirstPage = useCallback(async (): Promise<void> => {
    if (fetching.current) return;
    fetching.current = true;
    setRefreshing(true);
    setErrorMessage(null);

    try {
      const response = await getReceivedLikes(1, 12);

      setItems(response.results);
      setTotalCount(response.count);
      setCurrentPage(1);
      restartPagination.current = false;
      setHasNextPage(response.next !== null);
      setStatus(response.results.length > 0 ? "success" : "empty");
    } catch (error: unknown) {
      const normalized = normalizeApiError(error);
      setErrorMessage(normalized.message);
      setStatus(current => current === "loading" ? "error" : current);
    } finally {
      fetching.current = false;
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadFirstPage();
  }, [loadFirstPage]);

  async function handleLoadMore(): Promise<void> {
    if (fetching.current || deciding.current || !hasNextPage) {
      return;
    }

    if (restartPagination.current) { await loadFirstPage(); return; }
    fetching.current = true;
    setIsLoadingMore(true);
    setErrorMessage(null);

    const nextPage = currentPage + 1;

    try {
      const response = await getReceivedLikes(nextPage, 12);

      setItems((currentItems) => {
        const knownIds = new Set(
          currentItems.map((item) => item.interaction_id),
        );

        return [
          ...currentItems,
          ...response.results.filter(
            (item) => !knownIds.has(item.interaction_id),
          ),
        ];
      });

      setCurrentPage(nextPage);
      setTotalCount(response.count);
      setHasNextPage(response.next !== null);
    } catch (error: unknown) {
      const normalized = normalizeApiError(error);
      setErrorMessage(normalized.message);
    } finally {
      fetching.current = false;
      setIsLoadingMore(false);
    }
  }

  async function handleDecision(
    item: ReceivedLikeItem,
    decision: InteractionDecision,
  ): Promise<void> {
    if (deciding.current || fetching.current) {
      return;
    }

    deciding.current = true;
    setPendingIds((currentIds) => {
      const nextIds = new Set(currentIds);
      nextIds.add(item.interaction_id);
      return nextIds;
    });

    setErrorMessage(null);

    try {
      const response = await respondToReceivedLike(
        item.interaction_id,
        { decision },
      );

      setItems((currentItems) =>
        currentItems.filter(
          (currentItem) =>
            currentItem.interaction_id !== item.interaction_id,
        ),
      );

      setTotalCount((currentCount) => Math.max(0, currentCount - 1));
      restartPagination.current = true;

      if (response.matched && response.revealed_profile) {
        setMatchMessage(
          `Nouveau match avec ${response.revealed_profile.display_name}.`,
        );
      }

      if (hasNextPage || currentPage > 1) {
        await loadFirstPage();
      } else if (items.length === 1) {
        setStatus("empty");
      }
    } catch (error: unknown) {
      const normalized = normalizeApiError(error);
      setErrorMessage(normalized.message);
    } finally {
      deciding.current = false;
      setPendingIds((currentIds) => {
        const nextIds = new Set(currentIds);
        nextIds.delete(item.interaction_id);
        return nextIds;
      });
    }
  }

  return (
    <main className="received-likes-page">
      <section className="received-likes-hero">
        <div className="received-likes-hero__copy">
          <p className="received-likes-eyebrow">Intérêts reçus</p>
          <h1>Qui m’a liké</h1>
          <p className="received-likes-hero__lead">
            Découvre les personnes qui ont manifesté leur intérêt.
            L’identité affichée dépend toujours des droits accordés à
            ton offre, contrôlés côté serveur.
          </p>

          <div className="received-likes-hero__actions">
            <button
              type="button"
              className="received-likes-primary-link"
              onClick={() => navigate("/premium")}
            >
              Voir les offres Mbolo
              <span aria-hidden="true">→</span>
            </button>

            <button
              type="button"
              className="received-likes-secondary-link"
              onClick={() => navigate("/discovery")}
            >
              Continuer à découvrir
            </button>
          </div>
        </div>

        <aside className="received-likes-hero__counter" aria-label="Likes en attente">
          <span className="received-likes-hero__counter-icon" aria-hidden="true">♡</span>
          <strong>{totalCount > 99 ? "99+" : totalCount}</strong>
          <span>like{totalCount > 1 ? "s" : ""} en attente</span>
        </aside>
      </section>

      <section className="received-likes-trust-note">
        <div className="received-likes-trust-note__icon" aria-hidden="true">◇</div>
        <div>
          <strong>Révélation contrôlée par ton offre</strong>
          <p>
            Avec Mbolo Gratuit, les indices restent protégés. Plus et
            Prestige peuvent révéler l’identité lorsque le serveur
            confirme que ton abonnement l’autorise.
          </p>
        </div>
        <span className="received-likes-trust-note__badge">
          Contrôle côté serveur
        </span>
      </section>

      <section className="received-likes-explorer" aria-label="Organiser les intérêts reçus">
        <label>Rechercher les informations visibles
          <input type="search" value={search} onChange={event => setSearch(event.target.value)} />
        </label>
        <label>Filtrer les intérêts
          <select value={kind} onChange={event => setKind(event.target.value)}>
            <option value="all">Tous les intérêts</option>
            <option value="super">Super Likes</option>
            <option value="revealed">Identités révélées</option>
          </select>
        </label>
        <label>Trier les intérêts
          <select value={sort} onChange={event => setSort(event.target.value)}>
            <option value="recent">Plus récents</option><option value="oldest">Plus anciens</option>
          </select>
        </label>
        <button type="button" onClick={resetFilters}>Réinitialiser les filtres</button>
        <button type="button" disabled={refreshing || isLoadingMore || pendingIds.size > 0} onClick={() => void loadFirstPage()}>
          {refreshing ? "Actualisation…" : "Actualiser les intérêts"}
        </button>
        <p>Recherche et filtres sur les {items.length} intérêts chargés. Les identités protégées restent masquées.</p>
      </section>

      {matchMessage ? (
        <section className="received-likes-match-alert" role="status">
          <div>
            <span className="received-likes-match-alert__icon" aria-hidden="true">✓</span>
            <div>
              <strong>{matchMessage}</strong>
              <span>La conversation est maintenant disponible dans Mes matchs.</span>
            </div>
          </div>
          <button type="button" onClick={() => navigate("/matches")}>Voir mes matchs</button>
        </section>
      ) : null}

      {errorMessage ? (
        <div className="received-likes-page__error" role="alert">
          {errorMessage}
        </div>
      ) : null}

      {status === "loading" ? (
        <section className="received-likes-state received-likes-state--loading">
          <div className="received-likes-state__symbol" aria-hidden="true">◇</div>
          <p className="received-likes-eyebrow">Synchronisation</p>
          <h2>Chargement des intérêts reçus…</h2>
          <p>Nous récupérons ta sélection depuis le serveur.</p>
        </section>
      ) : status === "error" ? (
        <section className="received-likes-state received-likes-state--error">
          <div className="received-likes-state__symbol" aria-hidden="true">!</div>
          <p className="received-likes-eyebrow">Connexion interrompue</p>
          <h2>Impossible de charger cette page.</h2>
          <p>Réessaie dans quelques instants sans perdre tes données.</p>
          <button type="button" onClick={() => void loadFirstPage()}>Réessayer</button>
        </section>
      ) : status === "empty" ? (
        <section className="received-likes-state received-likes-state--empty">
          <div className="received-likes-state__symbol received-likes-state__symbol--success" aria-hidden="true">✓</div>
          <p className="received-likes-eyebrow">Sélection à jour</p>
          <h2>Aucun like en attente</h2>
          <p>
            Actualise cette liste pour consulter les prochains intérêts.
            Continue à explorer les profils pour créer de nouvelles connexions.
          </p>
          <div className="received-likes-state__actions">
            <button type="button" onClick={() => navigate("/discovery")}>Continuer à découvrir</button>
            <button type="button" className="received-likes-state__secondary" onClick={() => navigate("/account")}>Retour à mon espace</button>
          </div>
          <small>Cette liste est privée et visible uniquement depuis ton compte authentifié.</small>
        </section>
      ) : (
        <>
          <section className="received-likes-list-heading">
            <div>
              <p className="received-likes-eyebrow">Connexions potentielles</p>
              <h2>Des personnes souhaitent te découvrir.</h2>
            </div>
            <p>{pendingCount} carte{pendingCount > 1 ? "s" : ""} actuellement affichée{pendingCount > 1 ? "s" : ""}.</p>
          </section>

          <section className="received-likes-grid">
            {visibleItems.length === 0 ? <p role="status">Aucun intérêt ne correspond aux filtres.</p> : null}
            {visibleItems.map((item, index) => {
              const isPending = pendingIds.has(item.interaction_id);

              return (
                <article key={item.interaction_id} className="received-like-card">
                  <div className="received-like-card__visual">
                    {item.is_identity_revealed && item.image_url ? (
                      <img
                        src={item.image_url}
                        alt={`Photo de ${item.display_name ?? "ce membre"}`}
                      />
                    ) : (
                      <div className="received-like-card__masked" aria-label="Identité protégée">
                        <span aria-hidden="true">{item.has_photo ? "●" : "◇"}</span>
                        <small>Identité protégée</small>
                      </div>
                    )}

                    <div className="received-like-card__visual-topline">
                      <span>Profil {String(index + 1).padStart(2, "0")}</span>
                      <span>{item.is_identity_revealed ? "Révélé" : "Protégé"}</span>
                      {item.is_super_like ? <span>Super Like</span> : null}
                    </div>
                  </div>

                  <div className="received-like-card__content">
                    <div className="received-like-card__meta">
                      <span>{item.city}</span>
                      <time dateTime={item.received_at}>{formatReceivedDate(item.received_at)}</time>
                    </div>

                    <h3>
                      {item.is_identity_revealed && item.display_name
                        ? item.display_name
                        : "Quelqu’un s’intéresse à toi"}
                    </h3>

                    <dl>
                      <div><dt>Âge</dt><dd>{item.age_range}</dd></div>
                      <div><dt>Recherche</dt><dd>{item.dating_intent}</dd></div>
                      <div><dt>Photo</dt><dd>{item.has_photo ? "Profil avec photo" : "Silhouette protégée"}</dd></div>
                    </dl>

                    <div className="received-like-card__actions">
                      <button
                        type="button"
                        className="received-like-card__pass"
                        disabled={pendingIds.size > 0 || refreshing || isLoadingMore}
                        onClick={() => void handleDecision(item, "pass")}
                      >
                        Passer
                      </button>

                      <button
                        type="button"
                        className="received-like-card__like"
                        disabled={pendingIds.size > 0 || refreshing || isLoadingMore}
                        onClick={() => void handleDecision(item, "like")}
                      >
                        {isPending ? "Traitement…" : "Ça m’intéresse"}
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </section>

          {hasNextPage ? (
            <div className="received-likes-pagination">
              <button
                type="button"
                disabled={isLoadingMore || refreshing || pendingIds.size > 0}
                onClick={() => void handleLoadMore()}
              >
                {isLoadingMore ? "Chargement…" : "Charger plus"}
              </button>
            </div>
          ) : null}
        </>
      )}
    </main>
  );
}
