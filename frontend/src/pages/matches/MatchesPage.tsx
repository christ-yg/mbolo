/**
 * Page Mes matchs.
 *
 * Cette page protégée affiche uniquement les matchs actifs
 * de l'utilisateur connecté.
 */

import {
  useCallback,
  useEffect,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  deactivateMatch,
} from "../../api/interactionService";
import {
  DEFAULT_MATCHES_PAGE_SIZE,
  getMatches,
} from "../../api/matchService";
import { MatchCard } from "../../components/matches/MatchCard";
import { useAccountRealtime } from "../../hooks/useAccountRealtime";

import type {
  MatchItem,
  MatchesPaginatedResponse,
} from "../../types/matches";

type MatchesStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";

export function MatchesPage() {
  const navigate = useNavigate();
  const {
    lastEvent,
    revision,
  } = useAccountRealtime();

  const [status, setStatus] =
    useState<MatchesStatus>("loading");

  const [matchesData, setMatchesData] =
    useState<MatchesPaginatedResponse | null>(
      null,
    );

  const [currentPage, setCurrentPage] =
    useState(1);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [matchToRemove, setMatchToRemove] =
    useState<MatchItem | null>(null);

  const [isRemovingMatch, setIsRemovingMatch] =
    useState(false);

  /**
   * Charge une page de matchs depuis Django.
   */
  const loadMatches = useCallback(
    async (page: number): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");

      try {
        const result = await getMatches({
          page,
          pageSize: DEFAULT_MATCHES_PAGE_SIZE,
        });

        setMatchesData(result);
        setCurrentPage(page);

        if (result.results.length === 0) {
          setStatus("empty");
          return;
        }

        setStatus("success");
      } catch (error: unknown) {
        const normalizedError =
          normalizeApiError(error);

        setMatchesData(null);
        setErrorMessage(normalizedError.message);
        setStatus("error");
      }
    },
    [],
  );

  useEffect(() => {
    void loadMatches(1);
  }, [loadMatches]);

  /**
   * Recharge la première page lorsqu'un nouveau match
   * arrive par le canal WebSocket global.
   */
  useEffect(() => {
    if (lastEvent?.event === "match.notification") {
      void loadMatches(1);
    }
  }, [
    lastEvent,
    loadMatches,
    revision,
  ]);

  const matches: MatchItem[] =
    matchesData?.results ?? [];

  async function handleUnmatch(): Promise<void> {
    if (
      matchToRemove === null ||
      isRemovingMatch
    ) {
      return;
    }

    setIsRemovingMatch(true);
    setErrorMessage("");

    try {
      await deactivateMatch(matchToRemove.id);

      setMatchToRemove(null);

      await loadMatches(1);
    } catch (error: unknown) {
      const normalizedError =
        normalizeApiError(error);

      setErrorMessage(normalizedError.message);
    } finally {
      setIsRemovingMatch(false);
    }
  }

  if (status === "loading") {
    return (
      <main className="matches-page">
        <section className="matches-page__heading">
          <div>
            <p className="section-heading__eyebrow">
              Connexions réciproques
            </p>

            <h1>Nous chargeons tes matchs.</h1>

            <p>
              Seules les connexions actives associées
              à ton profil sont récupérées.
            </p>
          </div>
        </section>

        <section
          className="matches-state-card"
          role="status"
          aria-live="polite"
        >
          <div
            className="auth-loading-card__spinner"
            aria-hidden="true"
          />

          <h2>Chargement en cours</h2>

          <p>
            Tes informations privées restent protégées.
          </p>
        </section>
      </main>
    );
  }

  if (status === "error") {
    return (
      <main className="matches-page">
        <section className="matches-page__heading">
          <div>
            <p className="section-heading__eyebrow">
              Mes matchs
            </p>

            <h1>Impossible de charger tes matchs.</h1>

            <p>
              Ta session reste sécurisée. Tu peux
              relancer la requête.
            </p>
          </div>
        </section>

        <section
          className="matches-state-card matches-state-card--error"
          role="alert"
        >
          <div
            className="matches-state-card__symbol"
            aria-hidden="true"
          >
            !
          </div>

          <h2>Une erreur est survenue</h2>

          <p>
            {errorMessage ||
              "Le service est temporairement indisponible."}
          </p>

          <button
            type="button"
            onClick={() => {
              void loadMatches(currentPage);
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
      <main className="matches-page">
        <section className="matches-page__heading">
          <div>
            <p className="section-heading__eyebrow">
              Connexions réciproques
            </p>

            <h1>Mes matchs</h1>

            <p>
              Les personnes qui t’apprécient également
              apparaîtront ici.
            </p>
          </div>

          <div className="matches-page__summary">
            <span>0</span>
            <p>match actif</p>
          </div>
        </section>

        <section className="matches-state-card">
          <div
            className="matches-state-card__symbol"
            aria-hidden="true"
          >
            ♡
          </div>

          <h2>Aucun match pour le moment</h2>

          <p>
            Une connexion apparaîtra ici lorsqu’un like
            deviendra réciproque.
          </p>

          <a href="/discovery">
            Continuer la découverte
            <span aria-hidden="true">→</span>
          </a>
        </section>
      </main>
    );
  }

  return (
    <main className="matches-page">
      <section className="matches-page__heading">
        <div>
          <p className="section-heading__eyebrow">
            Connexions réciproques
          </p>

          <h1>Mes matchs</h1>

          <p>
            Chaque connexion affichée repose sur deux
            likes mutuels et reste limitée aux informations
            publiques.
          </p>
        </div>

        <div className="matches-page__summary">
          <span>{matchesData?.count ?? 0}</span>

          <p>
            {(matchesData?.count ?? 0) > 1
              ? "matchs actifs"
              : "match actif"}
          </p>
        </div>
      </section>

      <section
        className="matches-grid"
        aria-label="Liste de mes matchs"
      >
        {matches.map((match) => (
          <div
            key={match.id}
            className="match-card-with-detail"
          >
            <MatchCard match={match} />

            <div className="match-card-with-detail__actions">
              <button
                type="button"
                className="profile-detail-link-button"
                onClick={() => {
                  navigate(
                    `/profiles/${match.other_profile.id}`,
                  );
                }}
              >
                Voir le profil complet
              </button>

              <button
                type="button"
                className="match-card-with-detail__unmatch"
                onClick={() => {
                  setMatchToRemove(match);
                }}
              >
                Supprimer le match
              </button>
            </div>
          </div>
        ))}
      </section>

      {matchesData?.previous ||
      matchesData?.next ? (
        <nav
          className="matches-pagination"
          aria-label="Pagination des matchs"
        >
          <button
            type="button"
            disabled={!matchesData.previous}
            onClick={() => {
              void loadMatches(
                Math.max(1, currentPage - 1),
              );
            }}
          >
            ← Page précédente
          </button>

          <span>Page {currentPage}</span>

          <button
            type="button"
            disabled={!matchesData.next}
            onClick={() => {
              void loadMatches(currentPage + 1);
            }}
          >
            Page suivante →
          </button>
        </nav>
      ) : null}
      {matchToRemove ? (
        <div className="unmatch-dialog-backdrop">
          <section
            className="unmatch-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="unmatch-title"
          >
            <p className="section-heading__eyebrow">
              Confirmation
            </p>

            <h2 id="unmatch-title">
              Supprimer le match avec{" "}
              {matchToRemove.other_profile.display_name} ?
            </h2>

            <p>
              La conversation sera fermée. Les messages seront
              conservés de manière sécurisée mais ne seront plus
              accessibles depuis l’application.
            </p>

            <div className="unmatch-dialog__actions">
              <button
                type="button"
                disabled={isRemovingMatch}
                onClick={() => {
                  setMatchToRemove(null);
                }}
              >
                Annuler
              </button>

              <button
                type="button"
                disabled={isRemovingMatch}
                onClick={() => {
                  void handleUnmatch();
                }}
              >
                {isRemovingMatch
                  ? "Suppression…"
                  : "Supprimer le match"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
