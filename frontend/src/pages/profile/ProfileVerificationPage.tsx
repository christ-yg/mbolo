/**
 * Page premium de vérification du profil Mbolo.
 *
 * Cette page conserve toute la logique métier existante :
 * - récupération sécurisée du statut de vérification ;
 * - validation locale du fichier choisi ;
 * - aperçu local du selfie sans envoi automatique ;
 * - soumission uniquement lorsque l'API l'autorise ;
 * - gestion des états non envoyé, en attente, approuvé et refusé.
 *
 * La refonte améliore la hiérarchie visuelle, la confidentialité,
 * l'accessibilité et le responsive mobile.
 */

import {
  type ChangeEvent,
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import { normalizeApiError } from "../../api/apiError";
import {
  getProfileVerification,
  submitProfileVerification,
} from "../../api/profileVerificationService";
import type {
  ProfileVerificationState,
} from "../../types/profileVerification";

import "./ProfileVerificationPage.css";


const MAX_FILE_BYTES = 8 * 1024 * 1024;

type VerificationStatus =
  | "not_submitted"
  | "pending"
  | "approved"
  | "rejected";


const STATUS_CONTENT: Record<
  VerificationStatus,
  {
    eyebrow: string;
    title: string;
    description: string;
    icon: string;
  }
> = {
  not_submitted: {
    eyebrow: "Vérification disponible",
    title: "Profil non vérifié",
    description:
      "Envoie un selfie récent pour demander le badge Profil vérifié.",
    icon: "◇",
  },
  pending: {
    eyebrow: "Examen en cours",
    title: "Demande reçue",
    description:
      "L’équipe Mbolo compare ton selfie privé avec ta photo principale.",
    icon: "⌛",
  },
  approved: {
    eyebrow: "Identité confirmée",
    title: "Profil vérifié",
    description:
      "Ton badge Profil vérifié est maintenant visible sur Mbolo.",
    icon: "✓",
  },
  rejected: {
    eyebrow: "Nouvel envoi possible",
    title: "Selfie à reprendre",
    description:
      "Corrige le point indiqué puis envoie une nouvelle photo.",
    icon: "!",
  },
};


function formatDate(value: string | null): string {
  if (!value) {
    return "Non disponible";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date indisponible";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      dateStyle: "long",
      timeStyle: "short",
    },
  ).format(date);
}


function formatFileSize(bytes: number): string {
  const megabytes = bytes / (1024 * 1024);
  return `${megabytes.toFixed(megabytes >= 1 ? 1 : 2)} Mio`;
}


export function ProfileVerificationPage() {
  const [state, setState] =
    useState<ProfileVerificationState | null>(null);
  const [selfie, setSelfie] =
    useState<File | null>(null);
  const [previewUrl, setPreviewUrl] =
    useState("");
  const [isLoading, setIsLoading] =
    useState(true);
  const [isSubmitting, setIsSubmitting] =
    useState(false);
  const [message, setMessage] =
    useState("");
  const [error, setError] =
    useState("");


  useEffect(() => {
    let active = true;

    void getProfileVerification()
      .then((result) => {
        if (active) {
          setState(result);
        }
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(normalizeApiError(caught).message);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);


  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);


  const status = (
    state?.status ?? "not_submitted"
  ) as VerificationStatus;

  const statusContent = STATUS_CONTENT[status];

  const statusClass = useMemo(
    () =>
      `profile-verification-status `
      + `profile-verification-status--${status}`,
    [status],
  );


  function clearSelectedSelfie(): void {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelfie(null);
    setPreviewUrl("");
  }


  function selectSelfie(
    event: ChangeEvent<HTMLInputElement>,
  ): void {
    const selected = event.target.files?.[0] ?? null;

    setError("");
    setMessage("");

    if (!selected) {
      clearSelectedSelfie();
      return;
    }

    if (
      ![
        "image/jpeg",
        "image/png",
        "image/webp",
      ].includes(selected.type)
    ) {
      setError(
        "Choisis une image au format JPEG, PNG ou WebP.",
      );
      event.target.value = "";
      return;
    }

    if (selected.size > MAX_FILE_BYTES) {
      setError("Le selfie ne peut pas dépasser 8 Mio.");
      event.target.value = "";
      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setSelfie(selected);
    setPreviewUrl(URL.createObjectURL(selected));
  }


  async function submit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();

    if (
      !selfie
      || isSubmitting
      || !state?.can_submit
    ) {
      return;
    }

    setIsSubmitting(true);
    setError("");
    setMessage("");

    try {
      const result =
        await submitProfileVerification(selfie);

      setState(result);
      clearSelectedSelfie();
      setMessage(
        "Ta demande a été transmise de manière sécurisée.",
      );
    } catch (caught: unknown) {
      setError(normalizeApiError(caught).message);
    } finally {
      setIsSubmitting(false);
    }
  }


  return (
    <main className="profile-verification-page">
      <section
        className="profile-verification-hero"
        aria-labelledby="verification-page-title"
      >
        <div className="profile-verification-hero__content">
          <p className="profile-verification-eyebrow">
            Confiance sur Mbolo
          </p>

          <h1 id="verification-page-title">
            Vérifier mon profil
          </h1>

          <p className="profile-verification-hero__description">
            Le badge est accordé après comparaison humaine entre
            un selfie récent et ta photo principale. La validation
            de l’adresse e-mail ne suffit pas à obtenir ce badge.
          </p>

          <div className="profile-verification-hero__links">
            <Link to="/profile/edit">
              <span aria-hidden="true">←</span>
              Retour à mon profil
            </Link>

            <Link to="/profile/photos">
              Gérer ma photo principale
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>

        <aside className="profile-verification-trust-card">
          <span
            className="profile-verification-trust-card__icon"
            aria-hidden="true"
          >
            ◇
          </span>

          <div>
            <p>Justificatif privé</p>
            <strong>Jamais visible sur ton profil</strong>
            <span>
              Le selfie sert uniquement à la vérification.
            </span>
          </div>
        </aside>
      </section>

      {error ? (
        <div
          className="profile-verification-alert profile-verification-alert--error"
          role="alert"
        >
          <span aria-hidden="true">!</span>
          <p>{error}</p>
        </div>
      ) : null}

      {message ? (
        <div
          className="profile-verification-alert profile-verification-alert--success"
          role="status"
        >
          <span aria-hidden="true">✓</span>
          <p>{message}</p>
        </div>
      ) : null}

      {isLoading ? (
        <section
          className="profile-verification-loading"
          aria-busy="true"
        >
          <span
            className="profile-verification-loader"
            aria-hidden="true"
          />
          <p className="profile-verification-eyebrow">
            Vérification en cours
          </p>
          <h2>Chargement de ton statut</h2>
          <p>
            Mbolo récupère les informations de vérification
            associées à ton compte.
          </p>
        </section>
      ) : state ? (
        <div className="profile-verification-grid">
          <section className="profile-verification-card">
            <div className="profile-verification-card__heading">
              <div>
                <p className="profile-verification-eyebrow">
                  Statut actuel
                </p>
                <h2>Suivi de ma vérification</h2>
              </div>

              <span className="profile-verification-card__privacy">
                Données protégées
              </span>
            </div>

            <div className={statusClass}>
              <span
                className="profile-verification-status__icon"
                aria-hidden="true"
              >
                {statusContent.icon}
              </span>

              <div>
                <p>{statusContent.eyebrow}</p>
                <h3>{statusContent.title}</h3>
                <span>{statusContent.description}</span>
              </div>
            </div>

            {state.rejection_reason ? (
              <div className="profile-verification-rejection">
                <span aria-hidden="true">!</span>
                <div>
                  <strong>Pourquoi recommencer ?</strong>
                  <p>{state.rejection_reason}</p>
                </div>
              </div>
            ) : null}

            <div className="profile-verification-timeline">
              <div
                className={
                  state.submitted_at
                    ? "profile-verification-timeline__item profile-verification-timeline__item--complete"
                    : "profile-verification-timeline__item"
                }
              >
                <span aria-hidden="true">
                  {state.submitted_at ? "✓" : "1"}
                </span>

                <div>
                  <strong>Demande envoyée</strong>
                  <p>{formatDate(state.submitted_at)}</p>
                </div>
              </div>

              <div
                className={
                  state.reviewed_at
                    ? "profile-verification-timeline__item profile-verification-timeline__item--complete"
                    : "profile-verification-timeline__item"
                }
              >
                <span aria-hidden="true">
                  {state.reviewed_at ? "✓" : "2"}
                </span>

                <div>
                  <strong>Examen terminé</strong>
                  <p>{formatDate(state.reviewed_at)}</p>
                </div>
              </div>
            </div>
          </section>

          <form
            className="profile-verification-card"
            onSubmit={submit}
          >
            <div className="profile-verification-card__heading">
              <div>
                <p className="profile-verification-eyebrow">
                  Justificatif privé
                </p>
                <h2>Prends un selfie récent</h2>
              </div>
            </div>

            <div className="profile-verification-guidelines">
              <div>
                <span aria-hidden="true">1</span>
                <p>
                  Visage entièrement visible et correctement
                  éclairé.
                </p>
              </div>

              <div>
                <span aria-hidden="true">2</span>
                <p>
                  Une seule personne, sans lunettes sombres
                  ni filtre.
                </p>
              </div>

              <div>
                <span aria-hidden="true">3</span>
                <p>
                  Le visage doit correspondre à ta photo
                  principale.
                </p>
              </div>

              <div>
                <span aria-hidden="true">4</span>
                <p>
                  N’envoie pas de passeport ni de carte
                  d’identité à cette étape.
                </p>
              </div>
            </div>

            <div className="profile-verification-private-note">
              <span aria-hidden="true">◇</span>
              <p>
                Le selfie n’est jamais publié ni montré aux
                autres membres. Il est utilisé uniquement pour
                la procédure de vérification.
              </p>
            </div>

            {state.can_submit ? (
              <div className="profile-verification-upload-zone">
                <label className="profile-verification-upload">
                  <span className="profile-verification-upload__icon">
                    +
                  </span>
                  <strong>Sélectionner mon selfie</strong>
                  <small>
                    JPEG, PNG ou WebP · 8 Mio maximum
                  </small>

                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={selectSelfie}
                  />
                </label>

                {previewUrl && selfie ? (
                  <div className="profile-verification-preview">
                    <img
                      src={previewUrl}
                      alt="Aperçu local du selfie sélectionné"
                    />

                    <div>
                      <strong>{selfie.name}</strong>
                      <span>{formatFileSize(selfie.size)}</span>
                    </div>

                    <button
                      type="button"
                      onClick={clearSelectedSelfie}
                    >
                      Retirer
                    </button>
                  </div>
                ) : null}

                <button
                  type="submit"
                  className="profile-verification-submit"
                  disabled={!selfie || isSubmitting}
                >
                  {isSubmitting
                    ? "Envoi sécurisé…"
                    : "Envoyer ma demande"}
                  <span aria-hidden="true">→</span>
                </button>
              </div>
            ) : (
              <div
                className={
                  state.is_verified
                    ? "profile-verification-locked profile-verification-locked--approved"
                    : "profile-verification-locked"
                }
              >
                <span aria-hidden="true">
                  {state.is_verified ? "✓" : "⌛"}
                </span>

                <div>
                  <strong>
                    {state.is_verified
                      ? "Aucun nouvel envoi nécessaire"
                      : "Envoi temporairement indisponible"}
                  </strong>

                  <p>
                    {state.is_verified
                      ? "Ton profil est déjà vérifié. Le badge reste visible tant que ton compte respecte les règles de Mbolo."
                      : "Tu pourras envoyer un nouveau selfie après la décision de l’équipe Mbolo."}
                  </p>
                </div>
              </div>
            )}
          </form>
        </div>
      ) : (
        <section className="profile-verification-loading">
          <span
            className="profile-verification-status__icon"
            aria-hidden="true"
          >
            !
          </span>
          <h2>Statut indisponible</h2>
          <p>
            Recharge la page pour récupérer les informations.
          </p>
        </section>
      )}
    </main>
  );
}
