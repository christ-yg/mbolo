/**
 * Page premium de gestion des profils bloqués.
 *
 * Cette page permet à l'utilisateur :
 * - de consulter uniquement les profils qu'il a lui-même bloqués ;
 * - de comprendre les conséquences d'un déblocage ;
 * - de débloquer un profil après une confirmation explicite ;
 * - de charger progressivement les résultats lorsque la liste est longue.
 *
 * La logique API existante est conservée. Cette refonte améliore surtout
 * la lisibilité, l'accessibilité, les états de chargement et la cohérence
 * visuelle avec le reste de Mbolo.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
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

import "./BlockedUsersPage.css";
import "./TrustHistoryControls.css";


type PageStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";


function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date indisponible";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "long",
    },
  ).format(date);
}


function getPhoto(item: BlockedUserItem): string | null {
  const photos = [...(item.blocked_profile?.photos ?? [])];

  photos.sort(
    (a, b) =>
      Number(b.is_primary) - Number(a.is_primary)
      || a.position - b.position,
  );

  return photos[0]?.image_url ?? null;
}


function getInitial(item: BlockedUserItem): string {
  return (
    item.blocked_profile?.display_name
      ?.trim()
      .charAt(0)
      .toUpperCase()
    || "?"
  );
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
  const [successMessage, setSuccessMessage] =
    useState("");


  const busy = useRef(false);
  const [query, setQuery] = useState("");
  const [oldestFirst, setOldestFirst] = useState(false);

  const counterLabel = useMemo(
    () => (
      totalCount === 1
        ? "profil bloqué"
        : "profils bloqués"
    ),
    [totalCount],
  );


  const loadFirstPage =
    useCallback(async (): Promise<void> => {
      if (busy.current) return;
      busy.current = true;
      setStatus("loading");
      setErrorMessage("");
      setSuccessMessage("");

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
      } finally {
        busy.current = false;
      }
    }, []);


  useEffect(() => {
    void loadFirstPage();
  }, [loadFirstPage]);


  async function loadMore(): Promise<void> {
    if (busy.current || isLoadingMore || !hasNextPage) {
      return;
    }

    busy.current = true;
    setIsLoadingMore(true);
    setErrorMessage("");

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
      busy.current = false;
      setIsLoadingMore(false);
    }
  }


  async function confirmUnblock(
    item: BlockedUserItem,
  ): Promise<void> {
    if (busy.current || pendingId !== null) {
      return;
    }

    busy.current = true;
    setPendingId(item.id);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await unblockUser(item.id);

      const displayName =
        item.blocked_profile?.display_name
        ?? "Ce profil";

      setItems((currentItems) =>
        currentItems.filter(
          (currentItem) => currentItem.id !== item.id,
        ),
      );

      setTotalCount((count) => Math.max(0, count - 1));
      setConfirmingItem(null);
      setSuccessMessage(
        `${displayName} a été débloqué. L’ancien match et l’ancienne conversation ne sont pas restaurés.`,
      );

      // Removing a row changes page offsets; restart before loading more.
      if (hasNextPage || currentPage > 1) {
        setStatus("loading");
        try {
          const response = await getBlockedUsers(1, 20);
          setItems(response.results);
          setCurrentPage(1);
          setTotalCount(response.count);
          setHasNextPage(response.next !== null);
          setStatus(response.results.length ? "success" : "empty");
        } catch {
          setStatus("error");
          setErrorMessage("Profil débloqué. Actualise la liste avant de poursuivre.");
        }
      } else if (items.length === 1) {
        setStatus("empty");
      }
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Le déblocage a échoué.",
      );
    } finally {
      busy.current = false;
      setPendingId(null);
    }
  }


  const filteredItems = items.filter((item) =>
    `${item.blocked_profile?.display_name ?? "Profil indisponible"} ${item.blocked_profile?.city_label ?? item.blocked_profile?.city ?? ""}`.toLocaleLowerCase("fr").includes(query.trim().toLocaleLowerCase("fr"))
  ).sort((a, b) => oldestFirst ? a.created_at.localeCompare(b.created_at) : b.created_at.localeCompare(a.created_at));

  return (
    <main className="blocked-users-page">
      <section
        className="blocked-users-hero"
        aria-labelledby="blocked-users-title"
      >
        <div className="blocked-users-hero__content">
          <p className="blocked-users-eyebrow">
            Confidentialité et contrôle
          </p>

          <h1 id="blocked-users-title">
            Profils bloqués
          </h1>

          <p className="blocked-users-hero__description">
            Retrouve ici les profils que tu as choisi de bloquer.
            Un déblocage ne restaure jamais automatiquement un ancien
            match ni une conversation.
          </p>

          <div className="blocked-users-hero__actions">
            <button
              type="button"
              className="blocked-users-link-button"
              onClick={() => navigate("/account/security")}
            >
              <span aria-hidden="true">←</span>
              Retour à la sécurité du compte
            </button>

            <button
              type="button"
              className="blocked-users-link-button blocked-users-link-button--secondary"
              onClick={() => navigate("/safety")}
            >
              Consulter les règles de sécurité
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>

        <aside className="blocked-users-counter">
          <span className="blocked-users-counter__icon" aria-hidden="true">
            ◇
          </span>

          <strong>{totalCount > 99 ? "99+" : totalCount}</strong>
          <span>{counterLabel}</span>
        </aside>
      </section>

      <section
        className="blocked-users-feedback"
        aria-live="polite"
        aria-atomic="true"
      >
        {successMessage ? (
          <div className="blocked-users-alert blocked-users-alert--success">
            <span aria-hidden="true">✓</span>
            <p>{successMessage}</p>
          </div>
        ) : null}

        {errorMessage ? (
          <div
            className="blocked-users-alert blocked-users-alert--error"
            role="alert"
          >
            <span aria-hidden="true">!</span>
            <p>{errorMessage}</p>
          </div>
        ) : null}
      </section>

      <section className="trust-history-controls" aria-label="Recherche et filtres">
        <label>Rechercher dans la liste
          <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} />
        </label>
        <label>Ordre chronologique
          <select aria-label="Ordre chronologique" value={oldestFirst ? "oldest" : "newest"} onChange={(event) => setOldestFirst(event.target.value === "oldest")}>
            <option value="newest">Plus récents d’abord</option><option value="oldest">Plus anciens d’abord</option>
          </select>
        </label>
        <button type="button" disabled={status === "loading" || isLoadingMore || pendingId !== null || confirmingItem !== null} onClick={() => void loadFirstPage()}>Actualiser la liste</button>
        <button type="button" onClick={() => { setQuery(""); setOldestFirst(false);  }}>Réinitialiser les filtres</button>
        <p role="status">{filteredItems.length} résultat(s) sur {items.length} entrée(s) chargée(s). Recherche et tri limités aux entrées chargées.</p>
        {status === "success" && filteredItems.length === 0 && <p>Aucun résultat pour ces filtres. Tu peux charger la suite si elle est disponible.</p>}
      </section>

      {status === "loading" ? (
        <section
          className="blocked-users-state blocked-users-state--loading"
          aria-busy="true"
        >
          <span className="blocked-users-loader" aria-hidden="true" />
          <h2>Chargement de tes profils bloqués</h2>
          <p>
            Mbolo vérifie les informations associées à ton compte.
          </p>
        </section>
      ) : status === "error" ? (
        <section className="blocked-users-state">
          <span className="blocked-users-state__icon blocked-users-state__icon--error">
            !
          </span>
          <p className="blocked-users-eyebrow">
            Chargement interrompu
          </p>
          <h2>Impossible d’afficher cette liste</h2>
          <p>
            Vérifie ta connexion puis réessaie. Aucun profil n’a été
            débloqué automatiquement.
          </p>
          <button
            type="button"
            className="blocked-users-button blocked-users-button--primary"
            onClick={() => void loadFirstPage()}
          >
            Réessayer
            <span aria-hidden="true">→</span>
          </button>
        </section>
      ) : status === "empty" ? (
        <section className="blocked-users-state blocked-users-state--empty">
          <span className="blocked-users-state__icon" aria-hidden="true">
            ✓
          </span>
          <p className="blocked-users-eyebrow">
            Espace sous contrôle
          </p>
          <h2>Aucun profil bloqué</h2>
          <p>
            Tu n’as actuellement aucun profil dans cette liste.
            Les futurs blocages apparaîtront ici et resteront privés.
          </p>

          <div className="blocked-users-state__actions">
            <button
              type="button"
              className="blocked-users-button blocked-users-button--primary"
              onClick={() => navigate("/discovery")}
            >
              Continuer à découvrir
              <span aria-hidden="true">→</span>
            </button>

            <button
              type="button"
              className="blocked-users-button blocked-users-button--secondary"
              onClick={() => navigate("/account/security")}
            >
              Retour à Sécurité
            </button>
          </div>

          <div className="blocked-users-privacy-note">
            <span aria-hidden="true">◇</span>
            <p>
              Cette liste est privée et accessible uniquement depuis ton
              compte authentifié.
            </p>
          </div>
        </section>
      ) : (
        <>
          <section className="blocked-users-list-heading">
            <div>
              <p className="blocked-users-eyebrow">Liste privée</p>
              <h2>Les profils que tu as écartés.</h2>
            </div>
            <p>
              Cette liste n’est visible que par toi. Débloquer une personne
              ne recrée ni match ni conversation.
            </p>
          </section>

          <section
            className="blocked-users-grid"
            aria-label="Liste des profils bloqués"
          >
            {filteredItems.map((item) => {
              const profile = item.blocked_profile;
              const photo = getPhoto(item);

              return (
                <article
                  key={item.id}
                  className="blocked-user-card"
                >
                  <div className="blocked-user-card__visual">
                    {photo ? (
                      <img
                        src={photo}
                        alt=""
                        loading="lazy"
                      />
                    ) : (
                      <span aria-hidden="true">
                        {getInitial(item)}
                      </span>
                    )}

                    <div className="blocked-user-card__badge">
                      Profil bloqué
                    </div>
                  </div>

                  <div className="blocked-user-card__content">
                    <p className="blocked-user-card__eyebrow">
                      Bloqué le {formatDate(item.created_at)}
                    </p>

                    <h2>
                      {profile?.display_name ?? "Profil indisponible"}
                    </h2>

                    <p className="blocked-user-card__meta">
                      {profile
                        ? `${profile.age ?? "Âge non précisé"} · ${
                            profile.city_label
                            ?? profile.city
                            ?? "Ville non précisée"
                          }`
                        : "Ce compte ne possède plus de profil public."}
                    </p>

                    <div className="blocked-user-card__notice">
                      <span aria-hidden="true">i</span>
                      <p>
                        Le déblocage autorise seulement ce profil à
                        réapparaître dans Découvrir s’il est encore visible.
                      </p>
                    </div>

                    <button
                      type="button"
                      className="blocked-users-button blocked-users-button--unblock"
                      disabled={pendingId !== null || isLoadingMore}
                      onClick={() => setConfirmingItem(item)}
                    >
                      Débloquer ce profil
                      <span aria-hidden="true">→</span>
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
                className="blocked-users-button blocked-users-button--secondary"
                disabled={isLoadingMore || pendingId !== null || confirmingItem !== null}
                onClick={() => void loadMore()}
              >
                {isLoadingMore
                  ? "Chargement…"
                  : "Charger plus de profils"}
              </button>
            </div>
          ) : null}
        </>
      )}

      {confirmingItem ? (
        <div
          className="blocked-users-dialog-layer"
          role="presentation"
        >
          <button
            type="button"
            className="blocked-users-dialog-backdrop"
            aria-label="Fermer la confirmation"
            disabled={pendingId !== null || isLoadingMore}
            onClick={() => setConfirmingItem(null)}
          />

          <section
            className="blocked-users-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="unblock-title"
          >
            <span
              className="blocked-users-dialog__icon"
              aria-hidden="true"
            >
              ↗
            </span>

            <p className="blocked-users-eyebrow">
              Confirmation
            </p>

            <h2 id="unblock-title">
              Débloquer{" "}
              {confirmingItem.blocked_profile?.display_name
                ?? "ce profil"} ?
            </h2>

            <p>
              Cette personne pourra réapparaître dans Découvrir si son
              profil est toujours visible. L’ancien match et l’ancienne
              conversation resteront désactivés.
            </p>

            <div className="blocked-users-dialog__summary">
              <span aria-hidden="true">i</span>
              <p>
                Tu pourras bloquer ce profil à nouveau depuis sa fiche
                publique si nécessaire.
              </p>
            </div>

            <div className="blocked-users-dialog__actions">
              <button
                type="button"
                className="blocked-users-button blocked-users-button--secondary"
                disabled={pendingId !== null || isLoadingMore}
                onClick={() => setConfirmingItem(null)}
              >
                Annuler
              </button>

              <button
                type="button"
                className="blocked-users-button blocked-users-button--primary"
                disabled={pendingId !== null || isLoadingMore}
                onClick={() => void confirmUnblock(confirmingItem)}
              >
                {pendingId === confirmingItem.id
                  ? "Déblocage…"
                  : "Confirmer le déblocage"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
