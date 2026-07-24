import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { getMyReports } from "../../api/safetyService";
import type {
  ReportReason,
  ReportStatus,
  UserReportItem,
} from "../../types/safety";

type PageStatus = "loading" | "success" | "empty" | "error";

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
  {label: string; explanation: string}
> = {
  pending: {
    label: "Reçu",
    explanation: "Le signalement attend son examen par la modération.",
  },
  under_review: {
    label: "En cours d’examen",
    explanation: "Un modérateur analyse actuellement les éléments transmis.",
  },
  resolved: {
    label: "Traité",
    explanation: "L’examen est terminé et les mesures nécessaires ont été prises.",
  },
  rejected: {
    label: "Classé sans suite",
    explanation: "L’examen n’a pas permis de confirmer une violation.",
  },
};

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function getProfilePhoto(item: UserReportItem): string | null {
  const photos = [...(item.reported_profile?.photos ?? [])];
  photos.sort(
    (first, second) =>
      Number(second.is_primary) - Number(first.is_primary) ||
      first.position - second.position,
  );
  return photos[0]?.image_url ?? null;
}

export function ReportsPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<PageStatus>("loading");
  const [items, setItems] = useState<UserReportItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasNextPage, setHasNextPage] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const loadFirstPage = useCallback(async (): Promise<void> => {
    setStatus("loading");
    setErrorMessage("");

    try {
      const response = await getMyReports(1, 20);
      setItems(response.results);
      setTotalCount(response.count);
      setCurrentPage(1);
      setHasNextPage(response.next !== null);
      setStatus(response.results.length > 0 ? "success" : "empty");
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
    if (isLoadingMore || !hasNextPage) return;

    setIsLoadingMore(true);
    setErrorMessage("");

    try {
      const nextPage = currentPage + 1;
      const response = await getMyReports(nextPage, 20);
      setItems((currentItems) => [
        ...currentItems,
        ...response.results.filter(
          (item) =>
            !currentItems.some((currentItem) => currentItem.id === item.id),
        ),
      ]);
      setCurrentPage(nextPage);
      setTotalCount(response.count);
      setHasNextPage(response.next !== null);
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error ? error.message : "Impossible de charger la suite.",
      );
    } finally {
      setIsLoadingMore(false);
    }
  }

  return (
    <main className="reports-page">
      <section className="reports-page__hero">
        <div>
          <p className="section-heading__eyebrow">Sécurité communautaire</p>
          <h1>Mes signalements</h1>
          <p>
            Suis les dossiers que tu as transmis. Les décisions, preuves
            et notes internes restent protégées.
          </p>
        </div>
        <div className="reports-page__counter">
          <strong>{totalCount > 99 ? "99+" : totalCount}</strong>
          <span>signalement(s)</span>
        </div>
      </section>

      <aside className="reports-page__privacy-note" role="note">
        <span aria-hidden="true">⌾</span>
        <p>
          <strong>Confidentialité de la procédure</strong>
          Mbolo affiche seulement l’état public du dossier. L’identité
          du modérateur et ses notes ne sont jamais communiquées ici.
        </p>
      </aside>

      {errorMessage ? (
        <div className="reports-page__error" role="alert">{errorMessage}</div>
      ) : null}

      {status === "loading" ? (
        <section className="reports-page__state" role="status">
          Chargement de tes signalements…
        </section>
      ) : status === "error" ? (
        <section className="reports-page__state">
          <h2>Chargement impossible</h2>
          <button type="button" onClick={() => void loadFirstPage()}>
            Réessayer
          </button>
        </section>
      ) : status === "empty" ? (
        <section className="reports-page__state">
          <span aria-hidden="true">✓</span>
          <h2>Aucun signalement envoyé</h2>
          <p>Les dossiers que tu transmettras apparaîtront ici.</p>
          <button type="button" onClick={() => navigate("/safety")}>
            Retour à Sécurité
          </button>
        </section>
      ) : (
        <>
          <section className="reports-list">
            {items.map((item) => {
              const profile = item.reported_profile;
              const photo = getProfilePhoto(item);
              const statusContent = STATUS_CONTENT[item.status];

              return (
                <article key={item.id} className="report-card">
                  <div className="report-card__profile">
                    <div className="report-card__avatar">
                      {photo ? (
                        <img src={photo} alt="" loading="lazy" />
                      ) : (
                        <span aria-hidden="true">
                          {profile?.display_name?.charAt(0).toUpperCase() ?? "?"}
                        </span>
                      )}
                    </div>
                    <div>
                      <p>Profil signalé</p>
                      <h2>{profile?.display_name ?? "Profil indisponible"}</h2>
                      <span>Envoyé le {formatDate(item.created_at)}</span>
                    </div>
                  </div>

                  <div className="report-card__reason">
                    <span>Motif</span>
                    <strong>{REASON_LABELS[item.reason]}</strong>
                    {item.description ? <p>{item.description}</p> : null}
                  </div>

                  <div className={`report-card__status report-card__status--${item.status}`}>
                    <span>{statusContent.label}</span>
                    <p>{statusContent.explanation}</p>
                    <small>Mis à jour le {formatDate(item.updated_at)}</small>
                  </div>
                </article>
              );
            })}
          </section>

          {hasNextPage ? (
            <div className="reports-page__pagination">
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
    </main>
  );
}
