
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useNavigate,
  useParams,
} from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  blockProfile,
  reportProfile,
} from "../../api/safetyService";
import {
  createInteraction,
} from "../../api/interactionService";
import {
  getPublicProfileDetail,
} from "../../api/profileDetailService";

import type {
  InteractionDecision,
} from "../../types/interactions";
import type {
  PublicProfileDetail,
} from "../../types/profileDetail";
import type {
  ReportReason,
} from "../../types/safety";


type DetailStatus =
  | "loading"
  | "success"
  | "error";


export function ProfileDetailPage() {
  const navigate = useNavigate();
  const { profileId = "" } = useParams();

  const [status, setStatus] =
    useState<DetailStatus>("loading");

  const [profile, setProfile] =
    useState<PublicProfileDetail | null>(null);

  const [errorMessage, setErrorMessage] =
    useState("");

  const [actionMessage, setActionMessage] =
    useState("");

  const [pendingDecision, setPendingDecision] =
    useState<InteractionDecision | null>(null);

  const [isSafetyMenuOpen, setIsSafetyMenuOpen] =
    useState(false);

  const [isBlockDialogOpen, setIsBlockDialogOpen] =
    useState(false);

  const [isReportDialogOpen, setIsReportDialogOpen] =
    useState(false);

  const [reportReason, setReportReason] =
    useState<ReportReason>("harassment");

  const [reportDescription, setReportDescription] =
    useState("");

  const [isSafetyActionPending, setIsSafetyActionPending] =
    useState(false);

  useEffect(() => {
    let isActive = true;

    async function loadProfile(): Promise<void> {
      setStatus("loading");
      setErrorMessage("");

      try {
        const result =
          await getPublicProfileDetail(profileId);

        if (!isActive) {
          return;
        }

        setProfile(result);
        setStatus("success");
      } catch (error: unknown) {
        if (!isActive) {
          return;
        }

        const normalized =
          normalizeApiError(error);

        setErrorMessage(normalized.message);
        setStatus("error");
      }
    }

    void loadProfile();

    return () => {
      isActive = false;
    };
  }, [profileId]);

  const orderedPhotos = useMemo(
    () =>
      [...(profile?.photos ?? [])].sort(
        (first, second) =>
          Number(second.is_primary) -
            Number(first.is_primary) ||
          first.position - second.position,
      ),
    [profile],
  );

  async function handleDecision(
    decision: InteractionDecision,
  ): Promise<void> {
    if (
      profile === null ||
      pendingDecision !== null ||
      profile.relationship === "match"
    ) {
      return;
    }

    setPendingDecision(decision);
    setErrorMessage("");
    setActionMessage("");

    try {
      const result = await createInteraction({
        target_profile_id: profile.id,
        decision,
      });

      setProfile((currentProfile) =>
        currentProfile === null
          ? currentProfile
          : {
              ...currentProfile,
              current_decision: decision,
              relationship:
                result.matched
                  ? "match"
                  : currentProfile.relationship,
            },
      );

      if (result.matched) {
        setActionMessage(
          `Nouveau match avec ${profile.display_name}.`,
        );

        window.setTimeout(() => {
          navigate("/matches");
        }, 900);

        return;
      }

      setActionMessage(
        decision === "like"
          ? "Ton intérêt a bien été enregistré."
          : "Ce profil a été passé.",
      );
    } catch (error: unknown) {
      const normalized =
        normalizeApiError(error);

      setErrorMessage(normalized.message);
    } finally {
      setPendingDecision(null);
    }
  }


  async function handleBlockProfile(): Promise<void> {
    if (
      profile === null ||
      isSafetyActionPending
    ) {
      return;
    }

    setIsSafetyActionPending(true);
    setErrorMessage("");

    try {
      await blockProfile(profile.id);

      setIsBlockDialogOpen(false);
      setIsSafetyMenuOpen(false);

      navigate(
        "/discovery",
        {
          replace: true,
          state: {
            message: "Le profil a été bloqué.",
          },
        },
      );
    } catch (error: unknown) {
      const normalized = normalizeApiError(error);
      setErrorMessage(normalized.message);
    } finally {
      setIsSafetyActionPending(false);
    }
  }


  async function handleReportProfile(): Promise<void> {
    if (
      profile === null ||
      isSafetyActionPending
    ) {
      return;
    }

    setIsSafetyActionPending(true);
    setErrorMessage("");

    try {
      const result = await reportProfile(
        profile.id,
        {
          reason: reportReason,
          description: reportDescription.trim(),
        },
      );

      setActionMessage(result.message);
      setIsReportDialogOpen(false);
      setIsSafetyMenuOpen(false);
      setReportDescription("");
    } catch (error: unknown) {
      const normalized = normalizeApiError(error);
      setErrorMessage(normalized.message);
    } finally {
      setIsSafetyActionPending(false);
    }
  }


  if (status === "loading") {
    return (
      <main className="profile-detail-page">
        <section className="profile-detail-state">
          Chargement sécurisé du profil…
        </section>
      </main>
    );
  }

  if (status === "error" || profile === null) {
    return (
      <main className="profile-detail-page">
        <section className="profile-detail-state">
          <h1>Profil indisponible</h1>

          <p>
            {errorMessage ||
              "Ce profil n’est pas accessible."}
          </p>

          <button
            type="button"
            onClick={() => navigate(-1)}
          >
            Revenir
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="profile-detail-page">
      <section className="profile-detail-page__topbar">
        <button
          type="button"
          onClick={() => navigate(-1)}
        >
          ← Retour
        </button>

        <div className="profile-detail-safety-menu">
          <span>
            {profile.relationship === "match"
              ? "Profil d’un match"
              : "Profil public"}
          </span>

          <button
            type="button"
            className="profile-detail-safety-menu__trigger"
            aria-label="Actions de sécurité"
            aria-expanded={isSafetyMenuOpen}
            onClick={() => {
              setIsSafetyMenuOpen(
                (currentValue) => !currentValue,
              );
            }}
          >
            ⋯
          </button>

          {isSafetyMenuOpen ? (
            <div className="profile-detail-safety-menu__panel">
              <button
                type="button"
                onClick={() => {
                  setIsReportDialogOpen(true);
                  setIsSafetyMenuOpen(false);
                }}
              >
                Signaler ce profil
              </button>

              <button
                type="button"
                className="profile-detail-safety-menu__danger"
                onClick={() => {
                  setIsBlockDialogOpen(true);
                  setIsSafetyMenuOpen(false);
                }}
              >
                Bloquer ce profil
              </button>
            </div>
          ) : null}
        </div>
      </section>

      <section className="profile-detail-layout">
        <div className="profile-detail-gallery">
          {orderedPhotos.length > 0 ? (
            orderedPhotos.map((photo) => (
              photo.image_url ? (
                <img
                  key={photo.id}
                  src={photo.image_url}
                  alt={`Photo de ${profile.display_name}`}
                  loading="lazy"
                />
              ) : null
            ))
          ) : (
            <div className="profile-detail-gallery__placeholder">
              {profile.display_name
                .charAt(0)
                .toUpperCase()}
            </div>
          )}
        </div>

        <article className="profile-detail-card">
          <p className="section-heading__eyebrow">
            Rencontre Mbolo
          </p>

          <div className="profile-detail-card__title">
            <h1>{profile.display_name}</h1>

            {profile.is_verified ? (
              <span aria-label="Compte vérifié">
                ✓
              </span>
            ) : null}
          </div>

          <p className="profile-detail-card__summary">
            {profile.age !== null
              ? `${profile.age} ans`
              : "Âge non précisé"}
            {" · "}
            {profile.city_label}
          </p>

          <dl className="profile-detail-card__facts">
            <div>
              <dt>Recherche</dt>
              <dd>
                {profile.dating_intent_label}
              </dd>
            </div>

            <div>
              <dt>Genre</dt>
              <dd>{profile.gender_label}</dd>
            </div>
          </dl>

          <section className="profile-detail-card__bio">
            <h2>À propos</h2>

            <p>
              {profile.biography ||
                "Cette personne n’a pas encore ajouté de biographie."}
            </p>
          </section>

          {errorMessage ? (
            <p
              className="profile-detail-card__feedback profile-detail-card__feedback--error"
              role="alert"
            >
              {errorMessage}
            </p>
          ) : null}

          {actionMessage ? (
            <p
              className="profile-detail-card__feedback"
              role="status"
            >
              {actionMessage}
            </p>
          ) : null}

          <div className="profile-detail-card__actions">
            {profile.relationship === "match" ? (
              <button
                type="button"
                onClick={() => navigate("/matches")}
              >
                Voir dans Mes matchs
              </button>
            ) : (
              <>
                <button
                  type="button"
                  className="profile-detail-card__pass"
                  disabled={pendingDecision !== null}
                  onClick={() => {
                    void handleDecision("pass");
                  }}
                >
                  {pendingDecision === "pass"
                    ? "Traitement…"
                    : profile.current_decision === "pass"
                      ? "Déjà passé"
                      : "Passer"}
                </button>

                <button
                  type="button"
                  className="profile-detail-card__like"
                  disabled={pendingDecision !== null}
                  onClick={() => {
                    void handleDecision("like");
                  }}
                >
                  {pendingDecision === "like"
                    ? "Traitement…"
                    : profile.current_decision === "like"
                      ? "Déjà aimé"
                      : "J’aime"}
                </button>
              </>
            )}
          </div>
        </article>
      </section>


      {isBlockDialogOpen ? (
        <div
          className="profile-safety-dialog-backdrop"
          role="presentation"
        >
          <section
            className="profile-safety-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="block-profile-title"
          >
            <p className="section-heading__eyebrow">
              Action de sécurité
            </p>

            <h2 id="block-profile-title">
              Bloquer {profile.display_name} ?
            </h2>

            <p>
              Vous ne pourrez plus vous voir, vous liker ni
              continuer une conversation. Un match actif sera
              désactivé.
            </p>

            <div className="profile-safety-dialog__actions">
              <button
                type="button"
                disabled={isSafetyActionPending}
                onClick={() => {
                  setIsBlockDialogOpen(false);
                }}
              >
                Annuler
              </button>

              <button
                type="button"
                className="profile-safety-dialog__danger"
                disabled={isSafetyActionPending}
                onClick={() => {
                  void handleBlockProfile();
                }}
              >
                {isSafetyActionPending
                  ? "Blocage…"
                  : "Confirmer le blocage"}
              </button>
            </div>
          </section>
        </div>
      ) : null}

      {isReportDialogOpen ? (
        <div
          className="profile-safety-dialog-backdrop"
          role="presentation"
        >
          <section
            className="profile-safety-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-profile-title"
          >
            <p className="section-heading__eyebrow">
              Signalement confidentiel
            </p>

            <h2 id="report-profile-title">
              Signaler ce profil
            </h2>

            <label>
              Motif
              <select
                value={reportReason}
                onChange={(event) => {
                  setReportReason(
                    event.target.value as ReportReason,
                  );
                }}
              >
                <option value="harassment">
                  Harcèlement
                </option>
                <option value="fake_profile">
                  Faux profil ou usurpation
                </option>
                <option value="scam">
                  Arnaque ou demande d’argent
                </option>
                <option value="inappropriate_content">
                  Contenu inapproprié
                </option>
                <option value="threat">
                  Menace ou violence
                </option>
                <option value="spam">
                  Spam ou sollicitation abusive
                </option>
                <option value="underage_suspicion">
                  Suspicion de personne mineure
                </option>
                <option value="other">
                  Autre motif
                </option>
              </select>
            </label>

            <label>
              Informations complémentaires
              <textarea
                maxLength={2000}
                value={reportDescription}
                placeholder="Décris les faits observés sans partager de données sensibles."
                onChange={(event) => {
                  setReportDescription(
                    event.target.value,
                  );
                }}
              />
            </label>

            <small>
              {reportDescription.length}/2000
            </small>

            <div className="profile-safety-dialog__actions">
              <button
                type="button"
                disabled={isSafetyActionPending}
                onClick={() => {
                  setIsReportDialogOpen(false);
                }}
              >
                Annuler
              </button>

              <button
                type="button"
                disabled={isSafetyActionPending}
                onClick={() => {
                  void handleReportProfile();
                }}
              >
                {isSafetyActionPending
                  ? "Envoi…"
                  : "Envoyer le signalement"}
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </main>
  );
}
