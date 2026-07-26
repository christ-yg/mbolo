/**
 * Page premium de suivi des signalements envoyés.
 *
 * Cette page affiche uniquement les informations publiques d'un dossier :
 * - le profil signalé ;
 * - le motif choisi par l'utilisateur ;
 * - la date d'envoi ;
 * - le statut public de traitement.
 *
 * Les notes internes, l'identité du modérateur et les éléments confidentiels
 * ne sont jamais exposés dans l'interface.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate } from "react-router-dom";

import { getMyReports } from "../../api/safetyService";
import type {
  ReportReason,
  ReportStatus,
  UserReportItem,
} from "../../types/safety";

import "./ReportsPage.css";


type PageStatus =
  | "loading"
  | "success"
  | "empty"
  | "error";


const REASON_LABELS: Record<ReportReason, string> = {
  harassment: "Harcèlement",
  fake_profile: "Faux profil",
  scam: "Arnaque",
  inappropriate_content: "Contenu inapproprié",
  threat: "Menace",
  spam: "Spam",
  underage_suspicion: "Suspicion de minorité",
  other: "Autre motif",
};


const STATUS_CONTENT: Record<
  ReportStatus,
  {
    label: string;
    explanation: string;
  }
> = {
  pending: {
    label: "Reçu",
    explanation:
      "Le signalement attend son examen par l’équipe de modération.",
  },
  under_review: {
    label: "En cours d’examen",
    explanation:
      "Un modérateur analyse actuellement les éléments transmis.",
  },
  resolved: {
    label: "Traité",
    explanation:
      "L’examen est terminé et les mesures nécessaires ont été prises.",
  },
  rejected: {
    label: "Classé sans suite",
    explanation:
      "L’examen n’a pas permis de confirmer une violation.",
  },
};


function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date indisponible";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


function getProfilePhoto(item: UserReportItem): string | null {
  const photos = [...(item.reported_profile?.photos ?? [])];

  photos.sort(
    (first, second) =>
      Number(second.is_primary) - Number(first.is_primary)
      || first.position - second.position,
  );

  return photos[0]?.image_url ?? null;
}


function getInitial(item: UserReportItem): string {
  return (
    item.reported_profile?.display_name
      ?.trim()
      .charAt(0)
      .toUpperCase()
    || "?"
  );
}


export function ReportsPage() {
  const navigate = useNavigate();

  const [status, setStatus] =
    useState<PageStatus>("loading");
  const [items, setItems] =
    useState<UserReportItem[]>([]);
  const [totalCount, setTotalCount] =
    useState(0);
  const [currentPage, setCurrentPage] =
    useState(1);
  const [hasNextPage, setHasNextPage] =
    useState(false);
  const [isLoadingMore, setIsLoadingMore] =
    useState(false);
  const [errorMessage, setErrorMessage] =
    useState("");


  const counterLabel = useMemo(
    () => (
      totalCount === 1
        ? "signalement"
        : "signalements"
    ),
    [totalCount],
  );


  const loadFirstPage =
    useCallback(async (): Promise<void> => {
      setStatus("loading");
      setErrorMessage("");

      try {
        const response = await getMyReports(1, 20);

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
            : "Impossible de charger tes signalements.",
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
    setErrorMessage("");

    try {
      const nextPage = currentPage + 1;
      const response = await getMyReports(nextPage, 20);

      setItems((currentItems) => [
        ...currentItems,
        ...response.results.filter(
          (item) =>
            !currentItems.some(
              (currentItem) => currentItem.id === item.id,
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


  return (
    <main className="reports-premium-page">
      <section
        className="reports-premium-hero reports-premium-hero--panel"
        aria-labelledby="reports-title"
      >
        <div className="reports-premium-hero__content">
          <p className="reports-premium-eyebrow">
            Sécurité communautaire
          </p>

          <h1 id="reports-title">
            Mes signalements
          </h1>

          <p className="reports-premium-hero__description">
            Suis les dossiers que tu as transmis à Mbolo. Les décisions,
            preuves et notes internes restent protégées pendant toute la
            procédure.
          </p>

          <div className="reports-premium-hero__actions">
            <button
              type="button"
              className="reports-premium-link-button"
              onClick={() => navigate("/account/security")}
            >
              <span aria-hidden="true">←</span>
              Retour à la sécurité du compte
            </button>

            <button
              type="button"
              className="reports-premium-link-button reports-premium-link-button--secondary"
              onClick={() => navigate("/safety")}
            >
              Consulter les règles de sécurité
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>

        <aside className="reports-premium-counter">
          <span className="reports-premium-counter__icon" aria-hidden="true">
            ◉
          </span>

          <strong>{totalCount > 99 ? "99+" : totalCount}</strong>
          <span>{counterLabel}</span>
        </aside>
      </section>

      <aside className="reports-premium-privacy-note" role="note">
        <span className="reports-premium-privacy-note__icon" aria-hidden="true">
          ◇
        </span>

        <div>
          <strong>Confidentialité de la procédure</strong>
          <p>
            Mbolo affiche uniquement l’état public du dossier.
            L’identité du modérateur, ses notes internes et les mesures
            confidentielles ne sont jamais communiquées ici.
          </p>
        </div>

        <span className="reports-premium-privacy-note__label">
          Procédure protégée
        </span>
      </aside>


      <section className="reports-premium-overview" aria-label="Résumé du suivi">
        <div>
          <span className="reports-premium-overview__index">01</span>
          <div>
            <strong>Tu gardes la visibilité</strong>
            <p>Chaque dossier affiche son motif, son statut public et sa dernière mise à jour.</p>
          </div>
        </div>

        <div>
          <span className="reports-premium-overview__index">02</span>
          <div>
            <strong>La modération reste indépendante</strong>
            <p>Les décisions et preuves internes ne sont ni modifiables ni exposées depuis ton compte.</p>
          </div>
        </div>

        <div>
          <span className="reports-premium-overview__index">03</span>
          <div>
            <strong>La procédure reste confidentielle</strong>
            <p>Seules les informations nécessaires au suivi sont affichées dans cet espace privé.</p>
          </div>
        </div>
      </section>

      {errorMessage ? (
        <div
          className="reports-premium-alert"
          role="alert"
        >
          <span aria-hidden="true">!</span>
          <p>{errorMessage}</p>
        </div>
      ) : null}

      {status === "loading" ? (
        <section
          className="reports-premium-state"
          aria-busy="true"
        >
          <span className="reports-premium-loader" aria-hidden="true" />
          <p className="reports-premium-eyebrow">
            Vérification en cours
          </p>
          <h2>Chargement de tes signalements</h2>
          <p>
            Mbolo récupère uniquement les informations publiques liées à
            tes dossiers.
          </p>
        </section>
      ) : status === "error" ? (
        <section className="reports-premium-state">
          <span className="reports-premium-state__icon reports-premium-state__icon--error">
            !
          </span>
          <p className="reports-premium-eyebrow">
            Chargement interrompu
          </p>
          <h2>Impossible d’afficher tes dossiers</h2>
          <p>
            Vérifie ta connexion puis réessaie. Aucun signalement n’a été
            supprimé ou modifié.
          </p>
          <button
            type="button"
            className="reports-premium-button reports-premium-button--primary"
            onClick={() => void loadFirstPage()}
          >
            Réessayer
            <span aria-hidden="true">→</span>
          </button>
        </section>
      ) : status === "empty" ? (
        <section className="reports-premium-state reports-premium-state--empty">
          <span className="reports-premium-state__icon" aria-hidden="true">
            ✓
          </span>
          <p className="reports-premium-eyebrow">
            Aucun dossier actif
          </p>
          <h2>Aucun signalement envoyé</h2>
          <p>
            Les dossiers que tu transmettras apparaîtront ici avec leur
            statut public et leur date de mise à jour.
          </p>

          <div className="reports-premium-state__actions">
            <button
              type="button"
              className="reports-premium-button reports-premium-button--primary"
              onClick={() => navigate("/safety")}
            >
              Voir les règles de sécurité
              <span aria-hidden="true">→</span>
            </button>

            <button
              type="button"
              className="reports-premium-button reports-premium-button--secondary"
              onClick={() => navigate("/account/security")}
            >
              Retour à Sécurité
            </button>
          </div>

          <div className="reports-premium-state__note">
            <span aria-hidden="true">◇</span>
            <p>
              Tu peux signaler un comportement depuis le profil ou la
              conversation concernée.
            </p>
          </div>
        </section>
      ) : (
        <>
          <header className="reports-premium-section-heading">
            <div>
              <p className="reports-premium-eyebrow">Suivi de tes dossiers</p>
              <h2>Une lecture simple de chaque signalement.</h2>
            </div>
            <p>Les dossiers les plus récents apparaissent en premier. Le statut est mis à jour côté serveur.</p>
          </header>

          <section
            className="reports-premium-list"
            aria-label="Liste de mes signalements"
          >
            {items.map((item) => {
              const profile = item.reported_profile;
              const photo = getProfilePhoto(item);
              const statusContent = STATUS_CONTENT[item.status];

              return (
                <article
                  key={item.id}
                  className="reports-premium-card"
                >
                  <div className="reports-premium-card__profile">
                    <div className="reports-premium-card__avatar">
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
                    </div>

                    <div className="reports-premium-card__identity">
                      <p>Profil signalé</p>
                      <h2>
                        {profile?.display_name ?? "Profil indisponible"}
                      </h2>
                      <span>
                        Envoyé le {formatDate(item.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="reports-premium-card__reason">
                    <span>Motif déclaré</span>
                    <strong>{REASON_LABELS[item.reason]}</strong>

                    {item.description ? (
                      <p>{item.description}</p>
                    ) : (
                      <p className="reports-premium-card__muted">
                        Aucun détail complémentaire affiché.
                      </p>
                    )}
                  </div>

                  <div
                    className={
                      `reports-premium-card__status `
                      + `reports-premium-card__status--${item.status}`
                    }
                  >
                    <div className="reports-premium-card__status-header">
                      <span aria-hidden="true">●</span>
                      <strong>{statusContent.label}</strong>
                    </div>

                    <p>{statusContent.explanation}</p>

                    <small>
                      Mis à jour le {formatDate(item.updated_at)}
                    </small>
                  </div>
                </article>
              );
            })}
          </section>

          {hasNextPage ? (
            <div className="reports-premium-pagination">
              <button
                type="button"
                className="reports-premium-button reports-premium-button--secondary"
                disabled={isLoadingMore}
                onClick={() => void loadMore()}
              >
                {isLoadingMore
                  ? "Chargement…"
                  : "Charger plus de dossiers"}
              </button>
            </div>
          ) : null}
        </>
      )}
    </main>
  );
}
