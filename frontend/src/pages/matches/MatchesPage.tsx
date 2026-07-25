/**
 * Page « Mes matchs ».
 *
 * Cette page protégée affiche uniquement les matchs actifs du membre
 * authentifié. Les données restent fournies par Django : le frontend ne
 * décide jamais seul qu'un match existe et ne reçoit que le profil public
 * de l'autre participant.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import { deactivateMatch } from "../../api/interactionService";
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

import "./MatchesPage.css";


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
    useState<MatchesPaginatedResponse | null>(null);

  const [currentPage, setCurrentPage] =
    useState(1);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [matchToRemove, setMatchToRemove] =
    useState<MatchItem | null>(null);

  const [isRemovingMatch, setIsRemovingMatch] =
    useState(false);


  /**
   * Charge une page de matchs depuis l'API Django.
   *
   * Le backend reste l'autorité : le client affiche uniquement ce que
   * l'endpoint /v1/matches/ autorise pour l'utilisateur connecté.
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


  /**
   * Une notification de nouveau match déclenche un rechargement depuis le
   * serveur. Le websocket sert de signal ; les données finales viennent
   * toujours de l'API HTTP authentifiée.
   */
  useEffect(() => {
    if (lastEvent?.event === "match.notification") {
      void loadMatches(1);
    }
  }, [lastEvent, loadMatches, revision]);


  const matches: MatchItem[] =
    matchesData?.results ?? [];

  const verifiedMatchesCount = useMemo(
    () =>
      matches.filter(
        (match) => match.other_profile.is_verified,
      ).length,
    [matches],
  );


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
      <section className="matches-hero">
        <div className="matches-hero__copy">
          <p className="matches-eyebrow">
            Connexions réciproques
          </p>

          <h1>Mes matchs</h1>

          <p className="matches-hero__description">
            Retrouve les personnes avec lesquelles l'intérêt est mutuel,
            consulte leur profil public et commence une conversation dans
            un espace privé.
          </p>

          <div className="matches-hero__trust-list">
            <span>✓ Messagerie après réciprocité</span>
            <span>✓ Données privées protégées</span>
            <span>✓ Contrôle côté serveur</span>
          </div>
        </div>

        <aside
          className="matches-hero__summary"
          aria-label="Résumé de mes matchs"
        >
          <div className="matches-hero__summary-icon" aria-hidden="true">
            ♡
          </div>

          <strong>{count}</strong>

          <span>
            {count > 1
              ? "matchs actifs"
              : "match actif"}
          </span>

          {count > 0 ? (
            <small>
              {verifiedMatchesCount} profil
              {verifiedMatchesCount > 1 ? "s" : ""} vérifié
              {verifiedMatchesCount > 1 ? "s" : ""}
            </small>
          ) : null}
        </aside>
      </section>
    );
  }


  if (status === "loading") {
    return (
      <main className="matches-page matches-page--state">
        {renderHeading(matchesData?.count ?? 0)}

        <section
          className="matches-state matches-state--loading"
          role="status"
          aria-live="polite"
        >
          <div className="matches-spinner" aria-hidden="true" />
          <p className="matches-eyebrow">Connexion sécurisée</p>
          <h2>Chargement de tes matchs</h2>
          <p>
            Mbolo récupère uniquement tes connexions actives depuis le
            serveur authentifié.
          </p>
        </section>
      </main>
    );
  }


  if (status === "error") {
    return (
      <main className="matches-page matches-page--state">
        {renderHeading(0)}

        <section
          className="matches-state matches-state--error"
          role="alert"
        >
          <div className="matches-state__icon" aria-hidden="true">!</div>
          <p className="matches-eyebrow">Service indisponible</p>
          <h2>Impossible de charger tes matchs</h2>
          <p>
            {errorMessage ||
              "Le service est temporairement indisponible."}
          </p>

          <button
            type="button"
            className="matches-button matches-button--primary"
            onClick={() => {
              void loadMatches(currentPage);
            }}
          >
            Réessayer
            <span aria-hidden="true">↗</span>
          </button>
        </section>
      </main>
    );
  }


  if (status === "empty") {
    return (
      <main className="matches-page matches-page--state">
        {renderHeading(0)}

        <section className="matches-empty">
          <div className="matches-empty__visual" aria-hidden="true">
            <div className="matches-empty__avatar matches-empty__avatar--first">
              M
            </div>
            <div className="matches-empty__heart">♡</div>
            <div className="matches-empty__avatar matches-empty__avatar--second">
              B
            </div>
          </div>

          <div className="matches-empty__content">
            <p className="matches-eyebrow">Prochaine connexion</p>
            <h2>Ton prochain match commence dans Découvrir.</h2>
            <p>
              Un profil apparaîtra ici dès qu'une personne que tu as aimée
              manifestera le même intérêt. La messagerie restera fermée tant
              que la réciprocité n'est pas confirmée par le serveur.
            </p>

            <div className="matches-empty__actions">
              <button
                type="button"
                className="matches-button matches-button--primary"
                onClick={() => {
                  navigate("/discovery");
                }}
              >
                Continuer à découvrir
                <span aria-hidden="true">→</span>
              </button>

              <button
                type="button"
                className="matches-button matches-button--secondary"
                onClick={() => {
                  navigate("/settings/discovery");
                }}
              >
                Ajuster mes préférences
              </button>
            </div>
          </div>
        </section>
      </main>
    );
  }


  return (
    <main className="matches-page">
      {renderHeading(matchesData?.count ?? 0)}

      {errorMessage ? (
        <div className="matches-inline-alert" role="alert">
          <span aria-hidden="true">!</span>
          <p>{errorMessage}</p>
        </div>
      ) : null}

      <section className="matches-section-heading">
        <div>
          <p className="matches-eyebrow">Tes connexions</p>
          <h2>Des rencontres qui ont choisi de continuer.</h2>
        </div>

        <button
          type="button"
          onClick={() => {
            navigate("/discovery");
          }}
        >
          Découvrir d'autres profils
          <span aria-hidden="true">→</span>
        </button>
      </section>

      <section
        className="matches-grid"
        aria-label="Liste de mes matchs"
      >
        {matches.map((match) => (
          <MatchCard
            key={match.id}
            match={match}
            onOpenConversation={() => {
              navigate("/messages");
            }}
            onOpenProfile={() => {
              navigate(`/profiles/${match.other_profile.id}`);
            }}
            onRequestUnmatch={() => {
              setMatchToRemove(match);
            }}
          />
        ))}
      </section>

      {matchesData?.previous || matchesData?.next ? (
        <nav
          className="matches-pagination"
          aria-label="Pagination des matchs"
        >
          <button
            type="button"
            disabled={!matchesData.previous}
            onClick={() => {
              void loadMatches(Math.max(1, currentPage - 1));
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
            <div className="unmatch-dialog__icon" aria-hidden="true">!</div>
            <p className="matches-eyebrow">Action sensible</p>

            <h2 id="unmatch-title">
              Supprimer le match avec {matchToRemove.other_profile.display_name} ?
            </h2>

            <p>
              La conversation sera fermée. Cette action ne doit être utilisée
              que lorsque tu souhaites réellement mettre fin à cette connexion.
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
