/**
 * Page principale du moteur de découverte Mbolo.
 *
 * Cette page :
 *
 * - appelle l'API Django sécurisée ;
 * - affiche les profils compatibles ;
 * - gère le chargement ;
 * - gère les erreurs ;
 * - gère l'absence de profil ;
 * - gère la pagination ;
 * - conserve un profil actif à la fois.
 *
 * La route est déjà protégée par ProtectedRoute.
 *
 * Le backend continue néanmoins à imposer IsAuthenticated,
 * car une protection React ne remplace jamais une permission
 * serveur.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import { normalizeApiError } from "../../api/apiError";
import {
  DEFAULT_DISCOVERY_PAGE_SIZE,
  getDiscoveryProfiles,
} from "../../api/discoveryService";
import { ProfileCard } from "../../components/discovery/ProfileCard";
import { useAuth } from "../../hooks/useAuth";

import type {
  DiscoveryPaginatedResponse,
  DiscoveryProfile,
} from "../../types/discovery";

/**
 * Structure locale de l'état de chargement.
 */
type DiscoveryStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";

export function DiscoveryPage() {
  /**
   * Utilisateur actuellement connecté.
   *
   * Nous n'affichons que l'e-mail dans l'en-tête global.
   * La page de découverte n'a pas besoin d'autres données privées.
   */
  const { user } = useAuth();

  /**
   * État visuel de la page.
   */
  const [status, setStatus] =
    useState<DiscoveryStatus>("loading");

  /**
   * Réponse paginée actuellement chargée.
   */
  const [discoveryData, setDiscoveryData] =
    useState<DiscoveryPaginatedResponse | null>(null);

  /**
   * Numéro de la page backend courante.
   */
  const [currentPage, setCurrentPage] = useState(1);

  /**
   * Index du profil actif dans results.
   */
  const [currentProfileIndex, setCurrentProfileIndex] =
    useState(0);

  /**
   * Message d'erreur lisible.
   */
  const [errorMessage, setErrorMessage] = useState("");

  /**
   * Évite plusieurs actions rapides sur la même carte.
   */
  const [isActionPending, setIsActionPending] =
    useState(false);

  /**
   * Profils de la page courante.
   */
  const profiles = useMemo<DiscoveryProfile[]>(
    () => discoveryData?.results ?? [],
    [discoveryData],
  );

  /**
   * Profil actuellement affiché.
   */
  const currentProfile =
    profiles[currentProfileIndex] ?? null;

  /**
   * Charge une page depuis Django.
   */
  const loadDiscoveryPage = useCallback(
    async (page: number): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");
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

  /**
   * Premier chargement de la page.
   */
  useEffect(() => {
    void loadDiscoveryPage(1);
  }, [loadDiscoveryPage]);

  /**
   * Passe au profil suivant.
   *
   * Si la page courante est terminée :
   *
   * - charge la page suivante si elle existe ;
   * - sinon affiche l'état vide/final.
   */
  async function moveToNextProfile(): Promise<void> {
    if (isActionPending) {
      return;
    }

    setIsActionPending(true);

    try {
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
    } finally {
      setIsActionPending(false);
    }
  }

  /**
   * Première version du passage.
   *
   * Aucun appel backend n'est encore effectué.
   * Nous connecterons ensuite l'API d'interactions.
   */
  function handlePass(): void {
    void moveToNextProfile();
  }

  /**
   * Première version du like.
   *
   * Pour éviter de simuler une interaction enregistrée,
   * nous avançons uniquement vers la carte suivante.
   *
   * L'enregistrement réel sera ajouté lorsque le contrat
   * de l'API interactions aura été vérifié.
   */
  function handleLike(): void {
    void moveToNextProfile();
  }

  /**
   * Affichage pendant le chargement.
   */
  if (status === "loading") {
    return (
      <main className="discovery-page">
        <section className="discovery-page__heading">
          <p className="section-heading__eyebrow">
            Sélection personnalisée
          </p>

          <h1>Nous préparons tes profils.</h1>

          <p>
            Mbolo applique tes préférences et les règles de
            sécurité avant d’afficher les résultats.
          </p>
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

  /**
   * Affichage lorsqu'une erreur survient.
   */
  if (status === "error") {
    return (
      <main className="discovery-page">
        <section className="discovery-page__heading">
          <p className="section-heading__eyebrow">
            Découverte sécurisée
          </p>

          <h1>Impossible de charger les profils.</h1>

          <p>
            La session reste protégée. Tu peux relancer la
            recherche sans actualiser toute l’application.
          </p>
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

  /**
   * Affichage lorsqu'aucun profil n'est disponible.
   */
  if (status === "empty" || !currentProfile) {
    return (
      <main className="discovery-page">
        <section className="discovery-page__heading">
          <p className="section-heading__eyebrow">
            Sélection terminée
          </p>

          <h1>Tu as exploré les profils disponibles.</h1>

          <p>
            De nouveaux profils compatibles pourront apparaître
            lorsque la communauté évoluera ou lorsque tes
            préférences seront ajustées.
          </p>
        </section>

        <section className="discovery-state-card">
          <div
            className="discovery-state-card__symbol"
            aria-hidden="true"
          >
            ◇
          </div>

          <h2>Aucun nouveau profil</h2>

          <p>
            Tes critères de recherche restent privés et peuvent
            être modifiés depuis ton espace personnel.
          </p>

          <button
            type="button"
            onClick={() => {
              void loadDiscoveryPage(1);
            }}
          >
            Actualiser la sélection
          </button>
        </section>
      </main>
    );
  }

  /**
   * Affichage normal de la découverte.
   */
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

        <div className="discovery-page__summary">
          <span>{discoveryData?.count ?? 0}</span>

          <p>
            profils compatibles dans la sélection actuelle
          </p>
        </div>
      </section>

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
              La date de naissance exacte reste privée.
            </li>

            <li>
              Les comptes bloqués sont exclus côté serveur.
            </li>

            <li>
              Chaque consultation est journalisée sans
              enregistrer la liste des profils consultés.
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
        />
      </section>
    </main>
  );
}
