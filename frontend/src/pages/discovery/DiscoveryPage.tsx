/**
 * Page principale du moteur de découverte Mbolo.
 *
 * Fonctionnalités :
 *
 * - chargement des profils compatibles depuis Django ;
 * - pagination ;
 * - enregistrement réel des likes et des pass ;
 * - protection CSRF ;
 * - blocage des doubles clics ;
 * - conservation de la carte en cas d'erreur ;
 * - détection et célébration d'un match réciproque.
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
  DEFAULT_DISCOVERY_PAGE_SIZE,
  getDiscoveryProfiles,
} from "../../api/discoveryService";
import {
  createInteraction,
  getRewindState,
  getSuperLikeState,
  rewindLastPass,
} from "../../api/interactionService";
import { openConversation } from "../../api/messagingService";
import { MatchModal } from "../../components/discovery/MatchModal";
import { ProfileCard } from "../../components/discovery/ProfileCard";
import { useAuth } from "../../hooks/useAuth";

import "./DiscoveryPage.css";

import type {
  DiscoveryPaginatedResponse,
  DiscoveryProfile,
} from "../../types/discovery";
import type {
  InteractionDecision,
  MatchCelebrationData,
  RewindState,
  SuperLikeState,
} from "../../types/interactions";

type DiscoveryStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";

export function DiscoveryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [status, setStatus] =
    useState<DiscoveryStatus>("loading");

  const [discoveryData, setDiscoveryData] =
    useState<DiscoveryPaginatedResponse | null>(null);

  const [currentPage, setCurrentPage] = useState(1);

  const [currentProfileIndex, setCurrentProfileIndex] =
    useState(0);

  const [errorMessage, setErrorMessage] = useState("");

  /**
   * Erreur spécifique à un like ou à un pass.
   *
   * Contrairement à une erreur de chargement global, cette erreur
   * ne supprime pas la carte actuellement affichée.
   */
  const [actionError, setActionError] =
    useState<string | null>(null);

  /**
   * Empêche les doubles clics et les requêtes concurrentes.
   */
  const [isActionPending, setIsActionPending] =
    useState(false);

  /**
   * Informations du match actuellement célébré.
   */
  const [matchCelebration, setMatchCelebration] =
    useState<MatchCelebrationData | null>(null);

  const [isOpeningConversation, setIsOpeningConversation] =
    useState(false);

  const [rewindState, setRewindState] = useState<RewindState>({
    entitled: false,
    available: false,
    reason: "premium_required",
  });

  const [isRewindPending, setIsRewindPending] = useState(false);
  const [superLikeState, setSuperLikeState] = useState<SuperLikeState>({
    entitled: false,
    daily_limit: 0,
    remaining_today: 0,
  });

  const profiles = useMemo<DiscoveryProfile[]>(
    () => discoveryData?.results ?? [],
    [discoveryData],
  );

  const currentProfile =
    profiles[currentProfileIndex] ?? null;

  /**
   * Charge une page depuis l'API de découverte.
   */
  const loadDiscoveryPage = useCallback(
    async (page: number): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");
      setActionError(null);
      setCurrentProfileIndex(0);

      try {
        const result = await getDiscoveryProfiles({
          page,
          pageSize: DEFAULT_DISCOVERY_PAGE_SIZE,
        });

        setDiscoveryData(result);
        setCurrentPage(page);

        if (result.results.length === 0) {
          setStatus("empty");
          return;
        }

        setStatus("success");
      } catch (error: unknown) {
        const normalizedError =
          normalizeApiError(error);

        setDiscoveryData(null);
        setStatus("error");
        setErrorMessage(normalizedError.message);
      }
    },
    [],
  );

  useEffect(() => {
    void loadDiscoveryPage(1);
    void getRewindState()
      .then(setRewindState)
      .catch(() => {
        // L'échec de ce bonus ne doit jamais bloquer Découvrir.
      });
    void getSuperLikeState()
      .then(setSuperLikeState)
      .catch(() => {
        // Le moteur principal reste disponible si cet état bonus échoue.
      });
  }, [loadDiscoveryPage]);

  /**
   * Affiche le profil suivant.
   *
   * Lorsque la page courante est terminée, la page backend suivante
   * est chargée uniquement si Django indique qu'elle existe.
   */
  async function moveToNextProfile(): Promise<void> {
    const nextIndex = currentProfileIndex + 1;

    if (nextIndex < profiles.length) {
      setCurrentProfileIndex(nextIndex);
      return;
    }

    if (discoveryData?.next) {
      await loadDiscoveryPage(currentPage + 1);
      return;
    }

    setCurrentProfileIndex(profiles.length);
    setStatus("empty");
  }

  /**
   * Enregistre réellement une interaction dans Django.
   *
   * Le profil suivant ne sera affiché qu'après une réponse valide
   * du backend.
   */
  async function submitInteraction(
    decision: InteractionDecision,
    isSuperLike = false,
  ): Promise<void> {
    if (
      isActionPending ||
      !currentProfile
    ) {
      return;
    }

    setIsActionPending(true);
    setActionError(null);

    try {
      const response = await createInteraction({
        target_profile_id: currentProfile.id,
        decision,
        is_super_like: isSuperLike,
      });

      if (response.is_super_like) {
        setSuperLikeState((current) => ({
          ...current,
          remaining_today: Math.max(current.remaining_today - 1, 0),
        }));
      }

      setRewindState((current) => ({
        ...current,
        available: decision === "pass" && current.entitled,
        reason:
          decision === "pass" && current.entitled
            ? "available"
            : current.entitled
              ? "no_pass_to_rewind"
              : "premium_required",
      }));

      /**
       * Un like réciproque crée ou réactive un match.
       *
       * Nous conservons la carte affichée derrière la fenêtre,
       * puis nous avançons après sa fermeture.
       */
      if (
        decision === "like" &&
        response.matched
      ) {
        setMatchCelebration({
          matchId: response.match_id,
          profileId: currentProfile.id,
          displayName: currentProfile.display_name,
        });

        return;
      }

      await moveToNextProfile();
    } catch (error: unknown) {
      const normalizedError =
        normalizeApiError(error);

      /**
       * La carte reste visible.
       *
       * L'utilisateur peut lire l'erreur puis réessayer.
       */
      setActionError(normalizedError.message);
    } finally {
      setIsActionPending(false);
    }
  }

  function handlePass(): void {
    void submitInteraction("pass");
  }

  function handleLike(): void {
    void submitInteraction("like");
  }

  function handleSuperLike(): void {
    if (!superLikeState.entitled) {
      navigate("/premium");
      return;
    }
    void submitInteraction("like", true);
  }

  async function handleRewind(): Promise<void> {
    if (!rewindState.entitled) {
      navigate("/premium");
      return;
    }

    if (!rewindState.available || isRewindPending) {
      return;
    }

    setIsRewindPending(true);
    setActionError(null);

    try {
      const response = await rewindLastPass();

      setDiscoveryData((current) => {
        if (current === null) {
          return {
            count: 1,
            next: null,
            previous: null,
            results: [response.profile],
          };
        }

        const results = [...current.results];
        results.splice(currentProfileIndex, 0, response.profile);
        return {
          ...current,
          results,
        };
      });

      setStatus("success");
      setRewindState({
        entitled: true,
        available: false,
        reason: "no_pass_to_rewind",
      });
    } catch (error: unknown) {
      setActionError(normalizeApiError(error).message);
    } finally {
      setIsRewindPending(false);
    }
  }

  /**
   * Ferme la célébration puis passe au profil suivant.
   */
  function handleMatchModalClose(): void {
    setMatchCelebration(null);
    void moveToNextProfile();
  }

  async function handleMatchConversation(): Promise<void> {
    const matchId = matchCelebration?.matchId;

    if (
      !matchId ||
      isOpeningConversation
    ) {
      return;
    }

    setIsOpeningConversation(true);
    setActionError(null);

    try {
      const conversation = await openConversation({
        match_id: matchId,
      });

      setMatchCelebration(null);
      navigate(`/messages/${conversation.id}`);
    } catch (error: unknown) {
      setActionError(normalizeApiError(error).message);
      setIsOpeningConversation(false);
    }
  }

  if (status === "loading") {
    return (
      <main className="discovery-page">
        <section className="discovery-page__heading">
          <div>
            <p className="section-heading__eyebrow">
              Sélection personnalisée
            </p>

            <h1>Nous préparons tes profils.</h1>

            <p>
              Mbolo applique tes préférences et les règles de
              sécurité avant d’afficher les résultats.
            </p>
          </div>
        </section>

        <section
          className="discovery-state-card"
          role="status"
          aria-live="polite"
        >
          <div
            className="auth-loading-card__spinner"
            aria-hidden="true"
          />

          <h2>Recherche en cours</h2>

          <p>
            Quelques secondes suffisent généralement.
          </p>
        </section>
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="discovery-page">
        <section className="discovery-page__heading">
          <div>
            <p className="section-heading__eyebrow">
              Découverte sécurisée
            </p>

            <h1>Impossible de charger les profils.</h1>

            <p>
              La session reste protégée. Tu peux relancer la
              recherche sans actualiser toute l’application.
            </p>
          </div>
        </section>

        <section
          className="discovery-state-card discovery-state-card--error"
          role="alert"
        >
          <div
            className="discovery-state-card__symbol"
            aria-hidden="true"
          >
            !
          </div>

          <h2>Une erreur est survenue</h2>

          <p>
            {errorMessage ||
              "Le service de découverte est temporairement indisponible."}
          </p>

          <button
            type="button"
            onClick={() => {
              void loadDiscoveryPage(currentPage);
            }}
          >
            Réessayer
          </button>
        </section>
      </main>
    );
  }

  if (status === "empty" || !currentProfile) {
    return (
      <main className="discovery-page discovery-page--empty">
        <section className="discovery-empty-hero">
          <div className="discovery-empty-hero__copy">
            <p className="section-heading__eyebrow">Sélection à jour</p>

            <h1>Tu as vu tous les profils disponibles pour le moment.</h1>

            <p>
              Ta sélection est calculée selon tes préférences et les règles
              de compatibilité de Mbolo. Dès qu’un nouveau profil correspond,
              il apparaîtra ici automatiquement.
            </p>

            <div className="discovery-empty-hero__facts" aria-label="Informations de confidentialité">
              <span>✓ Critères privés</span>
              <span>✓ Profils déjà vus exclus</span>
              <span>✓ Calcul effectué côté serveur</span>
            </div>
          </div>

          <aside className="discovery-empty-panel" aria-label="Actions de découverte">
            <div className="discovery-empty-panel__icon" aria-hidden="true">
              <span>◇</span>
            </div>

            <p className="discovery-empty-panel__eyebrow">Aucun profil en attente</p>
            <h2>Ta sélection est complète.</h2>
            <p>
              Actualise maintenant ou ajuste tes préférences pour élargir
              les profils compatibles proposés.
            </p>

            {actionError ? (
              <p className="discovery-rewind-error" role="alert">
                {actionError}
              </p>
            ) : null}

            <div className="discovery-empty-panel__actions">
              <button
                type="button"
                className="discovery-empty-panel__primary"
                onClick={() => {
                  void loadDiscoveryPage(1);
                }}
              >
                Actualiser la sélection
                <span aria-hidden="true">↗</span>
              </button>

              <button
                type="button"
                className="discovery-rewind-button"
                disabled={
                  rewindState.entitled &&
                  (!rewindState.available || isRewindPending)
                }
                onClick={() => {
                  void handleRewind();
                }}
              >
                {rewindState.entitled
                  ? isRewindPending
                    ? "Restauration…"
                    : "↶ Revenir au dernier profil"
                  : "↶ Rewind avec Mbolo Plus"}
              </button>
            </div>
          </aside>
        </section>
      </main>
    );
  }

  return (
    <main className="discovery-page">
      <section className="discovery-page__heading">
        <div>
          <p className="section-heading__eyebrow">
            Découverte personnalisée
          </p>

          <h1>Des profils choisis avec attention.</h1>

          <p>
            Un profil à la fois, dans un espace conçu pour
            réduire la surcharge et préserver la confidentialité.
          </p>
        </div>

        <div className="discovery-page__heading-actions">
          <div className="discovery-page__summary">
            <span>{discoveryData?.count ?? 0}</span>

            <p>
              profils compatibles dans la sélection actuelle
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              navigate("/discovery-preferences");
            }}
          >
            Modifier mes préférences
          </button>
        </div>
      </section>

      {actionError ? (
        <div
          className="discovery-action-alert"
          role="alert"
        >
          <span aria-hidden="true">!</span>

          <p>{actionError}</p>

          <button
            type="button"
            aria-label="Fermer le message"
            onClick={() => {
              setActionError(null);
            }}
          >
            ×
          </button>
        </div>
      ) : null}

      <section className="discovery-page__workspace">
        <aside className="discovery-information-card">
          <p className="section-heading__eyebrow">
            Sécurité intégrée
          </p>

          <h2>La confiance avant la quantité.</h2>

          <ul>
            <li>
              Les adresses e-mail ne sont jamais affichées.
            </li>

            <li>
              Les interactions sont enregistrées côté serveur.
            </li>

            <li>
              Les comptes bloqués sont exclus automatiquement.
            </li>

            <li>
              Un match apparaît uniquement après deux likes.
            </li>
          </ul>

          {user ? (
            <div className="discovery-information-card__session">
              <span aria-hidden="true">✓</span>

              <p>
                Session sécurisée active
                <small>{user.email}</small>
              </p>
            </div>
          ) : null}
        </aside>

        <ProfileCard
          profile={currentProfile}
          currentPosition={currentProfileIndex + 1}
          totalInCurrentPage={profiles.length}
          isActionPending={isActionPending}
          onPass={handlePass}
          onLike={handleLike}
          onSuperLike={handleSuperLike}
          superLikeLabel={
            superLikeState.entitled
              ? `Super Like · ${superLikeState.remaining_today}`
              : "Super Like · Premium"
          }
          isSuperLikeDisabled={
            superLikeState.entitled &&
            superLikeState.remaining_today <= 0
          }
        />

        <button
          type="button"
          className="profile-detail-link-button"
          onClick={() => {
            navigate(`/profiles/${currentProfile.id}`);
          }}
        >
          Voir le profil complet
        </button>

        <button
          type="button"
          className="discovery-rewind-button"
          disabled={
            rewindState.entitled &&
            (!rewindState.available || isRewindPending)
          }
          onClick={() => {
            void handleRewind();
          }}
        >
          {rewindState.entitled
            ? isRewindPending
              ? "Restauration…"
              : "↶ Revenir au dernier profil ignoré"
            : "↶ Rewind · Mbolo Plus"}
        </button>
      </section>

      {matchCelebration ? (
        <MatchModal
          match={matchCelebration}
          onClose={handleMatchModalClose}
          onOpenConversation={() => {
            void handleMatchConversation();
          }}
          isOpeningConversation={isOpeningConversation}
        />
      ) : null}
    </main>
  );
}
