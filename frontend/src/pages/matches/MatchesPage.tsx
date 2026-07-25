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

        setStatus(
          result.results.length === 0
            ? "empty"
            : "success",
        );
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
      setErrorMessage(
        normalizeApiError(error).message,
      );
    } finally {
      setIsRemovingMatch(false);
    }
  }


  function renderHeading(count: number) {
    return (
      <section className="matches-page__heading">
        <div>
          <p className="section-heading__eyebrow">
            Connexions réciproques
          </p>

          <h1>Mes matchs</h1>

          <p>
            Retrouve les personnes avec lesquelles l’intérêt
            est mutuel et commence une conversation en toute
            confiance.
          </p>
        </div>

        <div className="matches-page__summary">
          <span>{count}</span>

          <p>
            {count > 1
              ? "matchs actifs"
              : "match actif"}
          </p>
        </div>
      </section>
    );
  }


  if (status === "loading") {
    return (
      <main className="matches-page">
        {renderHeading(matchesData?.count ?? 0)}

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
            Tes connexions actives sont récupérées de manière sécurisée.
          </p>
        </section>
      </main>
    );
  }


  if (status === "error") {
    return (
      <main className="matches-page">
        {renderHeading(0)}

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

          <h2>Impossible de charger tes matchs</h2>

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
        {renderHeading(0)}

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

          <button
            type="button"
            onClick={() => {
              navigate("/discovery");
            }}
          >
            Continuer la découverte
            <span aria-hidden="true">→</span>
          </button>
        </section>
      </main>
    );
  }


  return (
    <main className="matches-page">
      {renderHeading(matchesData?.count ?? 0)}

      {errorMessage ? (
        <div
          className="matches-inline-alert"
          role="alert"
        >
          <span aria-hidden="true">!</span>
          <p>{errorMessage}</p>
        </div>
      ) : null}

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
                className="match-card-with-detail__message"
                onClick={() => {
                  navigate("/messages");
                }}
              >
                <span aria-hidden="true">✦</span>
                Envoyer un message
              </button>

              <button
                type="button"
                className="profile-detail-link-button"
                onClick={() => {
                  navigate(
                    `/profiles/${match.other_profile.id}`,
                  );
                }}
              >
                Voir le profil
              </button>

              <button
                type="button"
                className="match-card-with-detail__unmatch"
                onClick={() => {
                  setMatchToRemove(match);
                }}
                aria-label={`Supprimer le match avec ${match.other_profile.display_name}`}
                title="Supprimer ce match"
              >
                ⋯
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
        <div
          className="unmatch-dialog-backdrop"
          onMouseDown={(event) => {
            if (
              event.target === event.currentTarget &&
              !isRemovingMatch
            ) {
              setMatchToRemove(null);
            }
          }}
        >
          <section
            className="unmatch-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="unmatch-title"
          >
            <p className="section-heading__eyebrow">
              Action sensible
            </p>

            <h2 id="unmatch-title">
              Supprimer le match avec{" "}
              {matchToRemove.other_profile.display_name} ?
            </h2>

            <p>
              La conversation sera fermée. Les messages resteront
              protégés mais ne seront plus accessibles depuis
              l’application.
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
